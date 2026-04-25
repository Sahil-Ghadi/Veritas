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

from core.firebase import verify_token
from fastapi import APIRouter, Depends, HTTPException, Request, status
from models.dispute import DisputeErrorCode
from schema.dispute import DisputeRequest
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
