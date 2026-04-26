"""
Dispute service — primary orchestrator for the dispute lifecycle.

Flow:
  1. Run all guard-rail checks in order (fail fast).
  2. Write the dispute document with status=PENDING (so rate-limit and
     duplicate checks are immediately accurate for concurrent requests).
  3. Call the verification service.
  4. If rejected → update dispute to REJECTED and return.
  5. If valid    → call score_service.apply_score_impact (batch commit)
                   and return the new score.

Firestore collections used:
  • posts      — keyed by post_id
  • users      — keyed by uid
  • disputes   — keyed by uuid4 string

Composite indexes required in Firestore Console
(queries will fail with an error pointing to the index creation URL):
  • disputes: (disputer_id ASC, created_at ASC)
  • disputes: (post_id ASC, claim_index ASC, disputer_id ASC)
  • disputes: (post_id ASC, created_at ASC)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from core.firebase import db_async
from models.dispute import DisputeErrorCode, DisputeStatus
from schema.dispute import DisputeRequest
from services.score_service import apply_score_impact, calculate_score_impact
from services.verification_service import verify_dispute
from google.cloud import firestore as gcloud_firestore

logger = logging.getLogger(__name__)


# ── Domain exception ───────────────────────────────────────────────────────────


class DisputeError(Exception):
    """Raised for all guard-rail failures. Carries a machine-readable code."""

    def __init__(self, code: DisputeErrorCode, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


# ── Public entry point ─────────────────────────────────────────────────────────


async def create_dispute(current_user: dict, request: DisputeRequest) -> dict:
    """
    Validate, persist, verify, and score a new dispute.

    Args:
        current_user: Decoded Firebase auth token dict (must have 'uid').
        request:      Validated DisputeRequest from the route handler.

    Returns:
        On rejection: {"status": "REJECTED", "reason": str}
        On validation: {"status": "VALIDATED", "score_impact": float, "new_score": float}

    Raises:
        DisputeError: For any guard-rail failure (caught by the route handler).
    """
    user_id: str = current_user["uid"]
    post_id: str = request.post_id
    claim_index: int = request.claim_index

    # ── Guard rail 1 — post existence + self-dispute ───────────────────────────
    post_ref = db_async.collection("posts").document(post_id)
    post_snap = await post_ref.get()

    if not post_snap.exists:
        raise DisputeError(
            DisputeErrorCode.POST_NOT_FOUND,
            f"Post '{post_id}' does not exist.",
        )

    _post_raw: dict[str, Any] | None = post_snap.to_dict()
    post_data: dict[str, Any] = _post_raw if _post_raw is not None else {}

    if post_data.get("poster_id") == user_id:
        raise DisputeError(
            DisputeErrorCode.SELF_DISPUTE,
            "You cannot dispute a claim on your own post.",
        )

    # ── Guard rails 2 + 3 — single query, Python-side filtering ──────────────
    # Firestore requires composite indexes for multi-field queries. To avoid
    # that operational overhead we fetch ALL disputes by this user (single-field
    # query, auto-indexed) and apply the duplicate / rate-limit checks in Python.
    user_dispute_snaps = (
        await db_async.collection("disputes")
        .where("disputer_id", "==", user_id)
        .get()
    )

    today_midnight = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    today_count = 0
    for snap in user_dispute_snaps:
        d = snap.to_dict() or {}
        # Guard rail 2 — exact duplicate on same post + claim
        if d.get("post_id") == post_id and d.get("claim_index") == claim_index:
            raise DisputeError(
                DisputeErrorCode.ALREADY_DISPUTED,
                "You have already submitted a dispute for this claim.",
            )
        # Guard rail 3 — count today's disputes
        created = d.get("created_at")
        if created is not None:
            if hasattr(created, "tzinfo") and created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if created >= today_midnight:
                today_count += 1

    if today_count >= 10:
        raise DisputeError(
            DisputeErrorCode.RATE_LIMIT_REACHED,
            "You have reached the daily limit of 10 disputes. Try again tomorrow.",
        )

    # ── Guard rail 5 — post flood protection (20 disputes/hour cap) ────────────
    # Fetch all disputes for this post and filter by timestamp in Python
    # to avoid needing a composite index on (post_id, created_at).
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    post_dispute_snaps = (
        await db_async.collection("disputes")
        .where("post_id", "==", post_id)
        .get()
    )

    recent_disputes_count = 0
    for snap in post_dispute_snaps:
        d = snap.to_dict() or {}
        created = d.get("created_at")
        if created is not None:
            if hasattr(created, "tzinfo") and created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if created >= one_hour_ago:
                recent_disputes_count += 1

    if recent_disputes_count >= 20:
        # Mark the post as under_review so the frontend can surface a warning.
        await post_ref.update({"under_review": True})
        raise DisputeError(
            DisputeErrorCode.POST_UNDER_REVIEW,
            "This post has received too many disputes recently and is under review.",
        )

    # ── Write PENDING dispute (locks the slot before async verification) ───────
    dispute_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    counter_source_str = (
        str(request.counter_source_url) if request.counter_source_url else None
    )

    dispute_doc: dict = {
        "id": dispute_id,
        "post_id": post_id,
        "disputer_id": user_id,
        "claim_index": claim_index,
        "dispute_type": request.dispute_type.value,
        "counter_argument": request.counter_argument,
        "counter_source_url": counter_source_str,
        "status": DisputeStatus.PENDING.value,
        "validation_result": None,
        "score_impact": None,
        "created_at": now,
    }

    dispute_ref = db_async.collection("disputes").document(dispute_id)
    await dispute_ref.set(dispute_doc)
    await post_ref.set(
        {
            "updated_at": datetime.now(timezone.utc),
        },
        merge=True,
    )
    logger.info("Dispute %s created (PENDING) for post %s", dispute_id, post_id)

    # ── Extract claim text + current verdict ──────────────────────────────────
    claims: list = post_data.get("claims", [])
    claim_text = ""
    current_verdict = ""
    if 0 <= claim_index < len(claims):
        claim = claims[claim_index]
        claim_text = claim.get("text", "")
        current_verdict = claim.get("verdict", "")

    # ── Call verification service ──────────────────────────────────────────────
    try:
        verification_result = await verify_dispute(
            claim_text=claim_text,
            current_verdict=current_verdict,
            counter_argument=request.counter_argument,
            counter_source_url=counter_source_str,
        )
    except Exception as exc:
        # Verification failure: mark dispute as REJECTED with the error reason.
        logger.error(
            "Verification error for dispute %s: %s", dispute_id, exc, exc_info=True
        )
        await dispute_ref.update(
            {
                "status": DisputeStatus.REJECTED.value,
                "validation_result": {"error": str(exc)},
            }
        )
        return {
            "status": DisputeStatus.REJECTED.value,
            "reason": "Verification service error. Please try again later.",
        }

    # ── Process verification result ────────────────────────────────────────────
    if not verification_result.get("dispute_valid", False):
        await dispute_ref.update(
            {
                "status": DisputeStatus.REJECTED.value,
                "validation_result": verification_result,
            }
        )
        logger.info(
            "Dispute %s REJECTED: %s", dispute_id, verification_result.get("reason")
        )
        return {
            "status": DisputeStatus.REJECTED.value,
            "reason": verification_result.get(
                "reason", "Dispute was not substantiated."
            ),
        }

    # ── Calculate score impact ─────────────────────────────────────────────────
    confidence: float = float(verification_result.get("confidence", 0.5))
    
    # User rule: if original is false -> make it true, else -> make it false
    if current_verdict.lower() in ["false", "mostly-false", "contradicted"]:
        new_verdict = "supported"
    else:
        new_verdict = "contradicted"
        
    is_supporting: bool = (new_verdict == "supported")

    impact: float = calculate_score_impact(
        confidence=confidence,
        source_credibility=0.5,
        claim_centrality=0.5,
        is_supporting=is_supporting,
    )

    # ── Atomic batch: update post score + dispute status ──────────────────────
    reason_label = (
        f"Dispute validated (confidence={confidence:.2f}): "
        f"{verification_result.get('reason', '')}"
    )
    new_score = await apply_score_impact(
        post_ref=post_ref,
        dispute_ref=dispute_ref,
        impact=impact,
        reason=reason_label,
        validation_result=verification_result,
        claim_index=claim_index,
        new_verdict=new_verdict,
    )

    logger.info(
        "Dispute %s VALIDATED | impact=%.2f new_score=%.2f",
        dispute_id,
        impact,
        new_score,
    )

    # TODO: dispatch post-resolution notifications to post owner and disputer.

    return {
        "status": DisputeStatus.VALIDATED.value,
        "score_impact": impact,
        "new_score": new_score,
    }
