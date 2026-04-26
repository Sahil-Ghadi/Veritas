"""
Score service — impact calculation and atomic Firestore score updates.

Responsibilities:
  1. calculate_score_impact  – pure function, no I/O, formula-driven.
  2. apply_score_impact      – async; reads the post's current credibility_score,
                               computes the new score, and commits a Firestore
                               batch that atomically updates both the post
                               (credibility_score + score_history) and the
                               dispute document (status + score_impact +
                               validation_result).

TODO items for future sprints:
  • Real source-credibility scorer:
      Accept a domain extracted from counter_source_url and return a float in
      [0, 1] by querying a trust database (e.g. a Firestore
      'source_trust_scores' collection seeded from NewsGuard / MBFC data).
      Replace the hardcoded 0.5 default in dispute_service.create_dispute.

  • Real claim-centrality scorer:
      Determine how central the disputed claim is to the overall post verdict
      (e.g. via embedding similarity between the claim and the post summary).
      Replace the hardcoded 0.5 default in dispute_service.create_dispute.

  • Notification dispatch (post-commit):
      After apply_score_impact returns, fire async notifications to both the
      post owner (score changed) and the disputer (dispute resolved).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from core.firebase import db_async
from google.cloud import firestore as gcloud_firestore  # for ArrayUnion sentinel
from models.dispute import DisputeStatus

logger = logging.getLogger(__name__)


# ── Impact formula ─────────────────────────────────────────────────────────────


def calculate_score_impact(
    confidence: float,
    source_credibility: float,
    claim_centrality: float,
    is_supporting: bool = False,
) -> float:
    """
    Return the credibility-score delta for a validated dispute.

    Formula:
        impact = round(direction * 15 × (confidence×0.5 + source_credibility×0.3 + claim_centrality×0.2), 2)
        where direction is 1.0 if is_supporting is True, else -1.0.

    All three inputs are expected to be floats in [0, 1].

    Examples
    --------
    >>> calculate_score_impact(0.82, 0.5, 0.5)
    -9.9
    >>> calculate_score_impact(1.0, 1.0, 1.0, is_supporting=True)
    15.0
    >>> calculate_score_impact(0.0, 0.0, 0.0)
    -0.0
    """
    direction = 1.0 if is_supporting else -1.0
    # Reduced impact: 30% of the original 15.0 base is 4.5
    raw = direction * 4.5 * (confidence * 0.5 + source_credibility * 0.3 + claim_centrality * 0.2)
    return round(raw, 2)


# ── Atomic score + dispute update ──────────────────────────────────────────────


async def apply_score_impact(
    post_ref: Any,
    dispute_ref: Any,
    impact: float,
    reason: str,
    validation_result: dict,
    claim_index: int | None = None,
    new_verdict: str | None = None,
) -> float:
    """
    Atomically:
      • Update the post's ``credibility_score`` and append to ``score_history``.
      • Update the specific claim's verdict if provided.
      • Update the dispute's ``status``, ``score_impact``, and
        ``validation_result``.

    Args:
        post_ref:          AsyncDocumentReference for the post being disputed.
        dispute_ref:       AsyncDocumentReference for the dispute document.
        impact:            The signed score deltaProduced by ``calculate_score_impact``.
        reason:            Human-readable label stored in the score history.
        validation_result: The full verification result dict.
        claim_index:       Index of the claim to update in the array.
        new_verdict:       The new verdict string (e.g. 'mostly-true', 'false').
    """
    # ── Read current score and claims from Firestore ───────────────────────────
    post_snap = await post_ref.get()
    _post_raw: dict[str, Any] | None = post_snap.to_dict()
    post_data: dict[str, Any] = _post_raw if _post_raw is not None else {}
    current_score: float = float(post_data.get("credibility_score", 50.0))
    claims = post_data.get("claims", [])

    # ── Update claim verdict if index is valid ────────────────────────────────
    if claim_index is not None and new_verdict and 0 <= claim_index < len(claims):
        # Update the claim in the local copy
        claims[claim_index]["verdict"] = new_verdict.lower()

    # ── Clamp: score must be between 0 and 100 ───────────────────────────────
    new_score = round(min(100.0, max(0.0, current_score + impact)), 2)

    # ── Build score-history entry ──────────────────────────────────────────────
    history_entry = {
        "date": datetime.now(timezone.utc).isoformat(),
        "score": new_score,
        "reason": reason,
    }

    # ── Batch commit ───────────────────────────────────────────────────────────
    batch = db_async.batch()

    update_payload = {
        "credibility_score": new_score,
        "score_history": gcloud_firestore.ArrayUnion([history_entry]),
        "disputes": gcloud_firestore.Increment(1),
    }

    # Only include claims in update if we actually modified it
    if claim_index is not None:
        update_payload["claims"] = claims

    batch.update(post_ref, update_payload)

    batch.update(
        dispute_ref,
        {
            "status": DisputeStatus.VALIDATED.value,
            "score_impact": impact,
            "validation_result": validation_result,
        },
    )

    await batch.commit()

    logger.info(
        "Score updated | post=%s old=%.2f impact=%.2f new=%.2f",
        post_ref.id,
        current_score,
        impact,
        new_score,
    )

    return new_score
