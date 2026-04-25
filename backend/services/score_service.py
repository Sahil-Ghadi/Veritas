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
) -> float:
    """
    Return the (negative) credibility-score delta for a validated dispute.

    Formula:
        impact = round(-15 × (confidence×0.5 + source_credibility×0.3 + claim_centrality×0.2), 2)

    All three inputs are expected to be floats in [0, 1].

    Examples
    --------
    >>> calculate_score_impact(0.82, 0.5, 0.5)
    -9.9
    >>> calculate_score_impact(1.0, 1.0, 1.0)
    -15.0
    >>> calculate_score_impact(0.0, 0.0, 0.0)
    -0.0
    """
    raw = -15.0 * (confidence * 0.5 + source_credibility * 0.3 + claim_centrality * 0.2)
    return round(raw, 2)


# ── Atomic score + dispute update ──────────────────────────────────────────────


async def apply_score_impact(
    post_ref: Any,
    dispute_ref: Any,
    impact: float,
    reason: str,
    validation_result: dict,
) -> float:
    """
    Atomically:
      • Update the post's ``credibility_score`` and append to ``score_history``.
      • Update the dispute's ``status``, ``score_impact``, and
        ``validation_result``.

    Both writes land in a single Firestore batch so they are always in sync —
    a partial failure cannot leave the post updated but the dispute stale (or
    vice versa).

    Args:
        post_ref:          AsyncDocumentReference for the post being disputed.
        dispute_ref:       AsyncDocumentReference for the dispute document.
        impact:            The signed score delta (typically negative) produced
                           by ``calculate_score_impact``.
        reason:            Human-readable label stored in the score history entry.
        validation_result: The full dict returned by the verification service,
                           stored verbatim on the dispute document.

    Returns:
        The new credibility score after clamping to [0, ∞).
    """
    # ── Read current score from Firestore (fresh read to avoid stale data) ─────
    post_snap = await post_ref.get()
    _post_raw: dict[str, Any] | None = post_snap.to_dict()
    post_data: dict[str, Any] = _post_raw if _post_raw is not None else {}
    current_score: float = float(post_data.get("credibility_score", 50.0))

    # ── Clamp: score can never go below 0 ─────────────────────────────────────
    new_score = round(max(0.0, current_score + impact), 2)

    # ── Build score-history entry ──────────────────────────────────────────────
    history_entry = {
        "date": datetime.now(timezone.utc).isoformat(),
        "score": new_score,
        "reason": reason,
    }

    # ── Batch commit ───────────────────────────────────────────────────────────
    # db_async.batch() returns an AsyncWriteBatch whose .commit() is awaitable.
    batch = db_async.batch()

    batch.update(
        post_ref,
        {
            "credibility_score": new_score,
            # ArrayUnion appends the entry without overwriting the existing array.
            "score_history": gcloud_firestore.ArrayUnion([history_entry]),
        },
    )

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
