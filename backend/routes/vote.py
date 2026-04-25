from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from core.firebase import db_async, verify_token
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from google.cloud import firestore as gcloud_firestore

router = APIRouter(tags=["Votes"])


class VoteRequest(BaseModel):
    vote: Literal["up", "down", "none"]


@router.post("/posts/{post_id}/vote")
async def cast_vote(
    post_id: str,
    body: VoteRequest,
    current_user: dict = Depends(verify_token),
) -> dict:
    uid = current_user["uid"]
    post_ref = db_async.collection("posts").document(post_id)
    vote_ref = db_async.collection("post_votes").document(f"{post_id}:{uid}")

    post_snap = await post_ref.get()
    if not post_snap.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Post '{post_id}' does not exist.", "code": "POST_NOT_FOUND"},
        )

    vote_snap = await vote_ref.get()
    old_vote = (vote_snap.to_dict() or {}).get("vote") if vote_snap.exists else "none"
    new_vote = body.vote

    if old_vote == new_vote:
        post_data = post_snap.to_dict() or {}
        return {
            "post_id": post_id,
            "upvotes": int(post_data.get("upvotes", 0) or 0),
            "downvotes": int(post_data.get("downvotes", 0) or 0),
            "my_vote": old_vote,
        }

    delta_up = 0
    delta_down = 0
    if old_vote == "up":
        delta_up -= 1
    elif old_vote == "down":
        delta_down -= 1

    if new_vote == "up":
        delta_up += 1
    elif new_vote == "down":
        delta_down += 1

    update_payload = {"updated_at": datetime.now(timezone.utc)}
    if delta_up != 0:
        update_payload["upvotes"] = gcloud_firestore.Increment(delta_up)
    if delta_down != 0:
        update_payload["downvotes"] = gcloud_firestore.Increment(delta_down)
    await post_ref.set(update_payload, merge=True)

    if new_vote == "none":
        if vote_snap.exists:
            await vote_ref.delete()
    else:
        await vote_ref.set(
            {
                "post_id": post_id,
                "uid": uid,
                "vote": new_vote,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    post_after = (await post_ref.get()).to_dict() or {}
    return {
        "post_id": post_id,
        "upvotes": max(0, int(post_after.get("upvotes", 0) or 0)),
        "downvotes": max(0, int(post_after.get("downvotes", 0) or 0)),
        "my_vote": new_vote,
    }
