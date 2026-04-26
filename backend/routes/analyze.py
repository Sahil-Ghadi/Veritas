import traceback
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from core.firebase import db_async
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from firebase_admin import auth as firebase_auth
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["analyze"])

# Job store (In-memory for now, consider Firestore for persistence)
_job_store: Dict[str, dict] = {}


class AnalyzeRequest(BaseModel):
    input_type: str = Field(..., description="'url' | 'text' | 'image'")
    raw_input: str = Field(
        ..., description="URL string, plain text, or base64 image data"
    )


class AnalyzeResponse(BaseModel):
    job_id: str
    status: str = "queued"


class ResultResponse(BaseModel):
    job_id: str
    status: str
    step: Optional[str] = None
    post_id: Optional[str] = None
    content_hash: Optional[str] = None
    cached: bool = False
    submitted_by: Optional[str] = None
    my_vote: Optional[str] = None
    upvotes: int = 0
    downvotes: int = 0
    disputes: int = 0
    result: Optional[dict] = None
    error: Optional[str] = None


class AnalysisListItem(BaseModel):
    job_id: str
    status: str
    step: Optional[str] = None
    input_type: Optional[str] = None
    raw_input: Optional[str] = None
    created_at: Optional[str] = None
    result: Optional[dict] = None
    content_hash: Optional[str] = None
    cached: bool = False
    post_id: Optional[str] = None
    submitted_by: Optional[str] = None
    my_vote: Optional[str] = None
    upvotes: int = 0
    downvotes: int = 0
    disputes: int = 0


async def _get_user_from_request(req: Request) -> dict:
    """Best-effort auth parsing. Returns decoded token if bearer token is valid."""
    auth_header = req.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return {}
    token = auth_header.replace("Bearer ", "").strip()
    if not token:
        return {}
    try:
        decoded = firebase_auth.verify_id_token(token)
        return decoded
    except Exception:
        return {}


async def _upsert_post_from_job(job_id: str, job: dict) -> None:
    """Ensure a Firestore post doc exists for dispute/vote features."""
    if job.get("status") != "done":
        return
    if bool(job.get("cached", False)):
        return
    result = job.get("result") or {}
    post_id = job.get("post_id") or job_id
    claims = result.get("claims") or []
    post_claims = [
        {
            "text": c.get("claim", ""),
            "verdict": c.get("verdict", "uncertain"),
            "confidence": c.get("confidence", 0.0),
        }
        for c in claims
    ]
    post_doc = {
        "id": post_id,
        "job_id": job_id,            # stored so we can query by job_id later
        "poster_id": job.get("submitted_by_uid", "system"),
        "submitted_by": job.get("submitted_by", "community"),
        "source": "analysis_pipeline",
        "input_type": job.get("input_type", "text"),
        "raw_input": job.get("raw_input", ""),
        "content_hash": job.get("content_hash"),
        "summary": result.get("explanation", ""),
        "essence": result.get("essence", ""),
        "ai_score": result.get("ai_score", 0.5),
        "claims": claims,            # store full claim objects (with sources, reasoning)
        "upvotes": int(job.get("upvotes", 0) or 0),
        "downvotes": int(job.get("downvotes", 0) or 0),
        "disputes": int(job.get("disputes", 0) or 0),
        "created_at": job.get("created_at"),
        "updated_at": datetime.now(timezone.utc),
    }
    await db_async.collection("posts").document(post_id).set(post_doc, merge=True)


async def _sync_job_counts_from_post(job_id: str) -> None:
    """Reflect persisted post vote/dispute counters back into job store."""
    job = _job_store.get(job_id)
    if not job:
        return
    # Avoid blocking result polling for queued/processing/error jobs.
    # Counters are only persisted once a completed analysis is upserted as a post.
    if job.get("status") != "done":
        return
    post_snap = await db_async.collection("posts").document(job_id).get()
    if not post_snap.exists:
        return
    post = post_snap.to_dict() or {}
    job["upvotes"] = int(post.get("upvotes", 0) or 0)
    job["downvotes"] = int(post.get("downvotes", 0) or 0)
    job["disputes"] = int(post.get("disputes", 0) or 0)
    job["submitted_by"] = post.get("submitted_by", job.get("submitted_by", "community"))


async def _sync_user_vote(job_id: str, uid: Optional[str]) -> None:
    if not uid:
        return
    job = _job_store.get(job_id)
    if not job:
        return
    post_id = job.get("post_id") or job_id
    vote_doc = (
        await db_async.collection("post_votes").document(f"{post_id}:{uid}").get()
    )
    if vote_doc.exists:
        vote_data = vote_doc.to_dict() or {}
        job["my_vote"] = vote_data.get("vote", "none")
    else:
        job["my_vote"] = "none"


async def _run_pipeline(job_id: str, raw_input: str, input_type: str):
    from agent.pipeline import pipeline

    node_to_step = {
        "cache_check": "Extracting essence",
        "input_parser": "Extracting essence",
        "essence_extractor": "Identifying claims",
        "claim_splitter": "Evaluating evidence",
        "claim_processing": "Scoring credibility",
        "score_aggregator": "Generating verdict",
        "explanation_generator": "Completed",
        "cache_writer": "Completed",
    }

    _job_store[job_id]["status"] = "processing"
    _job_store[job_id]["step"] = "Initializing pipeline"
    print(f"[analyze] Starting pipeline for job {job_id}...")

    try:
        initial_state = {
            "raw_input": raw_input,
            "input_type": input_type,
            "cached": False,
            "claim_results": [],
        }

        # Stream with both "updates" (for progress labels) and "values" (for the
        # fully-merged state).  Using only "updates" was lossy: when N parallel
        # `penalty` branches all complete in the same LangGraph superstep they
        # share the key "penalty" in the update dict, so Python's dict semantics
        # kept only the LAST branch's claim_result.  "values" gives us the state
        # AFTER LangGraph has applied every reducer (including the list-concat
        # reducer on claim_results), so all N results are always present.
        final_state: dict = dict(initial_state)
        async for chunk in pipeline.astream(
            initial_state,  # type: ignore[arg-type]
            stream_mode=["updates", "values"],
        ):
            # Each chunk is a (mode, data) tuple when multiple stream modes are
            # requested.  The isinstance guards let Pyright narrow data to dict.
            if not isinstance(chunk, tuple) or len(chunk) != 2:
                continue
            mode, data = chunk
            if mode == "updates" and isinstance(data, dict):
                for node_name in data:
                    print(f"[analyze] Node finished: {node_name}")
                    step_label = node_to_step.get(node_name)
                    if step_label:
                        _job_store[job_id]["step"] = step_label
            elif mode == "values" and isinstance(data, dict):
                # Always keep the latest fully-merged state from LangGraph so
                # that claim_results contains every parallel branch's output.
                final_state = data

        print(
            f"[analyze] Pipeline finished. Results found: {len(final_state.get('claim_results', []))}"
        )

        current_job = _job_store.get(job_id, {})
        _job_store[job_id] = {
            "status": "done",
            "step": "Completed",
            "input_type": current_job.get("input_type", input_type),
            "raw_input": current_job.get("raw_input", raw_input),
            "created_at": current_job.get("created_at"),
            "cached": bool(final_state.get("cached", False)),
            "content_hash": final_state.get("content_hash"),
            "post_id": current_job.get(
                "post_id",
                current_job.get("content_hash")
                or final_state.get("content_hash")
                or job_id,
            ),
            "upvotes": current_job.get("upvotes", 0),
            "downvotes": current_job.get("downvotes", 0),
            "disputes": current_job.get("disputes", 0),
            "result": {
                "ai_score": final_state.get("ai_score"),
                "essence": final_state.get("essence"),
                "explanation": final_state.get("article_level_explanation"),
                "claims": final_state.get("claim_results", []),
            },
        }
        await _upsert_post_from_job(job_id, _job_store[job_id])
    except Exception as exc:
        print(f"[analyze] pipeline failed for job {job_id}: {exc}")
        traceback.print_exc()
        current_job = _job_store.get(job_id, {})
        _job_store[job_id] = {
            **current_job,
            "status": "error",
            "step": "Failed",
            "error": f"{type(exc).__name__}: {exc}",
        }


@router.post("/analyze", response_model=AnalyzeResponse, status_code=202)
async def analyze(
    req: AnalyzeRequest, background_tasks: BackgroundTasks, http_req: Request
):
    if req.input_type not in ("url", "text", "image"):
        raise HTTPException(400, "input_type must be 'url', 'text', or 'image'")

    user_info = await _get_user_from_request(http_req)
    uid = user_info.get("uid")
    submitted_by = user_info.get("name") or user_info.get("email") or "community"
    
    if uid and submitted_by == "community":
        try:
            user_snap = await db_async.collection("users").document(uid).get()
            if user_snap.exists:
                user_data = user_snap.to_dict() or {}
                submitted_by = user_data.get("name") or user_data.get("email") or uid
            else:
                submitted_by = uid
        except Exception:
            submitted_by = uid

    job_id = str(uuid.uuid4())
    _job_store[job_id] = {
        "status": "queued",
        "step": "Queued",
        "input_type": req.input_type,
        "raw_input": req.raw_input,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "cached": False,
        "content_hash": None,
        "post_id": None,
        "submitted_by_uid": uid,
        "submitted_by": submitted_by,
        "my_vote": "none",
    }

    background_tasks.add_task(_run_pipeline, job_id, req.raw_input, req.input_type)
    return AnalyzeResponse(job_id=job_id)


@router.get("/results/{job_id}", response_model=ResultResponse)
async def get_results(job_id: str, req: Request):
    """Fetch a single analysis result.

    Checks the in-memory job store first (live jobs).
    Falls back to Firestore `posts` collection for completed analyses
    that survived a server restart.
    """
    user_info = await _get_user_from_request(req)
    uid = user_info.get("uid")
    job = _job_store.get(job_id)

    if job is not None and job.get("status") == "done":
        # Even if in memory, sync from Firestore to get latest disputes/votes
        await _sync_job_counts_from_post(job_id)
        post_snap = await db_async.collection("posts").document(job.get("post_id") or job_id).get()
        if post_snap.exists:
            post = post_snap.to_dict() or {}
            job["result"] = {
                "ai_score": post.get("ai_score"),
                "essence": post.get("essence", ""),
                "explanation": post.get("summary", ""),
                "claims": post.get("claims", []),
            }
            job["upvotes"] = int(post.get("upvotes", 0) or 0)
            job["downvotes"] = int(post.get("downvotes", 0) or 0)
            job["disputes"] = int(post.get("disputes", 0) or 0)

    if job is not None:
        await _sync_user_vote(job_id, uid)
        return ResultResponse(job_id=job_id, **job)

    # ── Firestore fallback ──────────────────────────────────────────────────
    # The ID passed may be either the post_id (Firestore doc) or the original job_id.
    post = None
    post_id = job_id
    try:
        snap = await db_async.collection("posts").document(job_id).get()
        if snap.exists:
            post = snap.to_dict() or {}
            post_id = snap.id
    except Exception:
        pass

    if post is None:
        # Try querying by job_id field (stored inside the post doc)
        try:
            query = db_async.collection("posts").where("job_id", "==", job_id).limit(1)
            snaps = await query.get()
            if snaps:
                post = snaps[0].to_dict() or {}
                post_id = snaps[0].id
        except Exception:
            pass

    if post is None:
        raise HTTPException(404, "Job not found")

    # Normalise created_at
    created_at = post.get("created_at")
    if created_at and not isinstance(created_at, str):
        try:
            created_at = created_at.isoformat()
        except Exception:
            created_at = str(created_at)

    # Fetch per-user vote
    my_vote = "none"
    if uid:
        try:
            vote_doc = await db_async.collection("post_votes").document(f"{post_id}:{uid}").get()
            if vote_doc.exists:
                my_vote = (vote_doc.to_dict() or {}).get("vote", "none")
        except Exception:
            pass

    result_dict = {
        "ai_score": post.get("ai_score"),
        "essence": post.get("essence", ""),
        "explanation": post.get("summary", ""),
        "claims": post.get("claims", []),
    }

    return ResultResponse(
        job_id=job_id,
        status="done",
        step="Completed",
        post_id=post_id,
        content_hash=post.get("content_hash"),
        cached=False,
        submitted_by=post.get("submitted_by", "community"),
        my_vote=my_vote,
        upvotes=int(post.get("upvotes", 0) or 0),
        downvotes=int(post.get("downvotes", 0) or 0),
        disputes=int(post.get("disputes", 0) or 0),
        result=result_dict,
    )


@router.get("/results", response_model=list[AnalysisListItem])
async def list_results(req: Request):
    """Return all completed analyses.

    Strategy:
    1. Read ALL posts from Firestore (persistent across restarts).
    2. Merge any in-memory jobs that completed this session but haven't been
       written to Firestore yet (edge case: race between write and read).
    3. Deduplicate by content_hash so the same article analysed twice shows once.
    4. Attach per-user vote state if the caller is authenticated.
    """
    user_info = await _get_user_from_request(req)
    uid = user_info.get("uid")

    # ── 1. Load from Firestore ──────────────────────────────────────────────
    seen_hashes: set[str] = set()
    # Map post_id -> raw dict so we can merge in-memory data on top
    posts_by_id: dict[str, dict] = {}
    try:
        post_snaps = await db_async.collection("posts").get()
        for snap in post_snaps:
            post = snap.to_dict() or {}
            post_id = snap.id
            content_hash = post.get("content_hash")
            # Deduplicate by content_hash
            if content_hash:
                if content_hash in seen_hashes:
                    continue
                seen_hashes.add(content_hash)
            posts_by_id[post_id] = {**post, "post_id": post_id}
    except Exception as exc:
        print(f"[analyze] failed to load posts from Firestore: {exc}")

    # ── 2. Merge live in-memory jobs (may have fresher counter data) ────────
    for job_id, job in _job_store.items():
        if job.get("status") != "done":
            continue
        if bool(job.get("cached", False)):
            continue
        post_id = job.get("post_id") or job_id
        content_hash = job.get("content_hash")
        # If already covered by Firestore, just refresh counters
        if post_id in posts_by_id:
            posts_by_id[post_id]["upvotes"] = int(job.get("upvotes", 0) or 0)
            posts_by_id[post_id]["downvotes"] = int(job.get("downvotes", 0) or 0)
            posts_by_id[post_id]["disputes"] = int(job.get("disputes", 0) or 0)
            continue
        # Not in Firestore yet – add directly from memory
        if content_hash:
            if content_hash in seen_hashes:
                continue
            seen_hashes.add(content_hash)
        result = job.get("result") or {}
        posts_by_id[post_id] = {
            "post_id": post_id,
            "id": post_id,
            "job_id": job_id,
            "input_type": job.get("input_type"),
            "raw_input": job.get("raw_input"),
            "content_hash": content_hash,
            "summary": result.get("explanation", ""),
            "essence": result.get("essence", ""),
            "ai_score": result.get("ai_score", 0.5),
            "claims": result.get("claims", []),
            "submitted_by": job.get("submitted_by", "community"),
            "created_at": job.get("created_at"),
            "upvotes": int(job.get("upvotes", 0) or 0),
            "downvotes": int(job.get("downvotes", 0) or 0),
            "disputes": int(job.get("disputes", 0) or 0),
        }

    # ── 3. Fetch per-user vote and build response ───────────────────────────
    items: list[AnalysisListItem] = []
    for post_id, post in posts_by_id.items():
        my_vote = "none"
        if uid:
            try:
                vote_doc = await db_async.collection("post_votes").document(f"{post_id}:{uid}").get()
                if vote_doc.exists:
                    my_vote = (vote_doc.to_dict() or {}).get("vote", "none")
            except Exception:
                pass

        # Reconstruct result dict in the shape the frontend expects
        result_dict = {
            "ai_score": post.get("ai_score"),
            "essence": post.get("essence", ""),
            "explanation": post.get("summary", ""),
            "claims": post.get("claims", []),
        }

        # created_at may be a Firestore DatetimeWithNanoseconds; normalise to str
        created_at = post.get("created_at")
        if created_at and not isinstance(created_at, str):
            try:
                created_at = created_at.isoformat()
            except Exception:
                created_at = str(created_at)

        # job_id: prefer in-memory mapping, else use post_id
        job_id = post.get("job_id") or post_id

        items.append(
            AnalysisListItem(
                job_id=job_id,
                status="done",
                step="Completed",
                input_type=post.get("input_type"),
                raw_input=post.get("raw_input", ""),
                created_at=created_at,
                result=result_dict,
                content_hash=post.get("content_hash"),
                cached=False,
                post_id=post_id,
                submitted_by=post.get("submitted_by", "community"),
                my_vote=my_vote,
                upvotes=int(post.get("upvotes", 0) or 0),
                downvotes=int(post.get("downvotes", 0) or 0),
                disputes=int(post.get("disputes", 0) or 0),
            )
        )

    # Sort newest first
    items.sort(key=lambda x: x.created_at or "", reverse=True)
    return items
