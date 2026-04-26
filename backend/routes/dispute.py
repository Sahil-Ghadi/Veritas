"""
Dispute router — POST /disputes

Resolves the current user from the existing verify_token dependency, delegates
all business logic to dispute_service.create_dispute, and maps service-layer
exceptions to appropriate HTTP responses.

HTTP contract:
  201  { status, score_impact, new_score }        — dispute validated
  200  { status, reason }                          — dispute rejected (not an error)
  404  { error, code }                             — post not found
  403  { error, code }                             — guard-rail failure
  422                                              — Pydantic validation error (automatic)
  500  { detail: "Internal server error" }         — unexpected failure (logged server-side)
"""

from __future__ import annotations

import logging

from core.firebase import verify_token, db_async
from fastapi import APIRouter, Depends, HTTPException, Request, status
from models.dispute import DisputeErrorCode
from schema.dispute import DisputeRequest
from google.cloud import firestore
from services.dispute_service import DisputeError, create_dispute

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Disputes"])


@router.post(
    "/disputes",
    summary="Submit a dispute against a post claim",
    status_code=status.HTTP_200_OK,
)
async def submit_dispute(
    body: DisputeRequest,
    req: Request,
    current_user: dict = Depends(verify_token),
) -> dict:
    """
    Submit a new dispute for a specific claim on a post.

    Guard-rail failures return HTTP 403 with an error code in the body so the
    client can display a user-friendly message without string-matching.
    POST_NOT_FOUND returns HTTP 404 instead.
    """
    try:
        result = await create_dispute(current_user=current_user, request=body)
        return result

    except DisputeError as exc:
        error_body = {"error": exc.message, "code": exc.code.value}

        if exc.code == DisputeErrorCode.POST_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_body,
            )

        # All other guard-rail failures are 403 Forbidden.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_body,
        )

    except Exception as exc:
        # Log the full traceback server-side; never leak internals to the client.
        logger.error(
            "Unexpected error in submit_dispute (post_id=%s, user=%s): %s",
            body.post_id,
            current_user.get("uid", "unknown"),
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

@router.get(
    "/posts/{post_id}/disputes",
    summary="Get all disputes for a post",
    status_code=status.HTTP_200_OK,
)
async def get_post_disputes(post_id: str):
    """
    Fetches all disputes for a post. 
    Note: We fetch without order_by to avoid requiring a composite index 
    on (post_id, created_at), sorting in Python instead.
    """
    try:
        snaps = (
            await db_async.collection("disputes")
            .where("post_id", "==", post_id)
            .get()
        )
        disputes = []
        for snap in snaps:
            d = snap.to_dict()
            if d:
                # Convert datetime to string
                if d.get("created_at"):
                    if not isinstance(d["created_at"], str):
                        try:
                            d["created_at"] = d["created_at"].isoformat()
                        except Exception:
                            d["created_at"] = str(d["created_at"])
                disputes.append(d)
        
        # Sort by created_at descending in memory
        disputes.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return disputes
    except Exception as exc:
        logger.error(f"Error fetching disputes for post {post_id}: {exc}", exc_info=True)
        raise HTTPException(500, f"Error fetching disputes: {exc}")


@router.get(
    "/posts/{post_id}/score-history",
    summary="Get the credibility score history for a post",
    status_code=status.HTTP_200_OK,
)
async def get_score_history(post_id: str):
    """
    Returns the score_history array from the post document.
    Each entry is: { date: str, score: float, reason: str }
    The initial AI score is prepended as the baseline entry.
    """
    try:
        snap = await db_async.collection("posts").document(post_id).get()
        if not snap.exists:
            raise HTTPException(status_code=404, detail="Post not found")

        post = snap.to_dict() or {}
        history = post.get("score_history", [])

        # Normalise any datetime objects to ISO strings
        normalised = []
        for entry in history:
            e = dict(entry)
            if e.get("date") and not isinstance(e["date"], str):
                try:
                    e["date"] = e["date"].isoformat()
                except Exception:
                    e["date"] = str(e["date"])
            normalised.append(e)

        # Prepend the baseline AI score as the first data point
        ai_score = post.get("ai_score")
        created_at = post.get("created_at")
        if created_at and not isinstance(created_at, str):
            try:
                created_at = created_at.isoformat()
            except Exception:
                created_at = str(created_at)

        if ai_score is not None:
            baseline_score = round(
                (ai_score if ai_score > 1 else ai_score * 100), 2
            )
            baseline = {
                "date": created_at or "",
                "score": baseline_score,
                "reason": "Initial AI analysis",
            }
            # Only prepend if history doesn't already have this entry
            if not normalised or normalised[0].get("reason") != "Initial AI analysis":
                normalised = [baseline] + normalised

        return normalised

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error fetching score history for post {post_id}: {exc}", exc_info=True)
        raise HTTPException(500, f"Error fetching score history: {exc}")
