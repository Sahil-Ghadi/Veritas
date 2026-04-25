import uuid
import asyncio
import traceback
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime, timezone
from core.firebase import db_async
from firebase_admin import auth as firebase_auth

router = APIRouter(prefix="/api", tags=["analyze"])

# Job store (In-memory for now, consider Firestore for persistence)
_job_store: Dict[str, dict] = {}

class AnalyzeRequest(BaseModel):
    input_type: str = Field(..., description="'url' | 'text' | 'image'")
    raw_input: str = Field(..., description="URL string, plain text, or base64 image data")

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


async def _get_uid_from_request(req: Request) -> Optional[str]:
    """Best-effort auth parsing. Returns uid if bearer token is valid."""
    auth_header = req.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.replace("Bearer ", "").strip()
    if not token:
        return None
    try:
        decoded = firebase_auth.verify_id_token(token)
        return decoded.get("uid")
    except Exception:
        return None


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
        "poster_id": job.get("submitted_by_uid", "system"),
        "submitted_by": job.get("submitted_by", "community"),
        "source": "analysis_pipeline",
        "input_type": job.get("input_type", "text"),
        "raw_input": job.get("raw_input", ""),
        "content_hash": job.get("content_hash"),
        "summary": result.get("explanation", ""),
        "essence": result.get("essence", ""),
        "ai_score": result.get("ai_score", 0.5),
        "claims": post_claims,
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
    post_id = job.get("post_id") or job_id
    post_snap = await db_async.collection("posts").document(post_id).get()
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
    vote_doc = await db_async.collection("post_votes").document(f"{post_id}:{uid}").get()
    if vote_doc.exists:
        vote_data = vote_doc.to_dict() or {}
        job["my_vote"] = vote_data.get("vote", "none")
    else:
        job["my_vote"] = "none"

async def _run_pipeline(job_id: str, raw_input: str, input_type: str):
    from agent.pipeline import pipeline

    node_to_step = {
        "cache_check": "Checking cache",
        "input_parser": "Extracting content",
        "essence_extractor": "Extracting essence",
        "claim_splitter": "Identifying claims",
        "query_builder": "Building search queries",
        "adversarial_searcher": "Cross-referencing sources",
        "alignment": "Aligning evidence",
        "judge": "Evaluating evidence",
        "penalty": "Calculating confidence",
        "score_aggregator": "Scoring credibility",
        "explanation_generator": "Generating verdict",
        "cache_writer": "Finalizing result",
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

        merged_state = dict(initial_state)
        async for update in pipeline.astream(initial_state, stream_mode="updates"):
            for node_name, payload in update.items():
                print(f"[analyze] Node finished: {node_name}")
                step_label = node_to_step.get(node_name)
                if step_label:
                    _job_store[job_id]["step"] = step_label
                
                # Merging logic
                if isinstance(payload, dict):
                    for key, value in payload.items():
                        if key == "claim_results" and isinstance(value, list):
                            merged_state.setdefault("claim_results", [])
                            merged_state["claim_results"].extend(value)
                        else:
                            merged_state[key] = value
        
        final_state = merged_state
        print(f"[analyze] Pipeline finished. Results found: {len(final_state.get('claim_results', []))}")

        current_job = _job_store.get(job_id, {})
        _job_store[job_id] = {
            "status": "done",
            "step": "Completed",
            "input_type": current_job.get("input_type", input_type),
            "raw_input": current_job.get("raw_input", raw_input),
            "created_at": current_job.get("created_at"),
            "cached": bool(final_state.get("cached", False)),
            "content_hash": final_state.get("content_hash"),
            "post_id": current_job.get("post_id", current_job.get("content_hash") or final_state.get("content_hash") or job_id),
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
async def analyze(req: AnalyzeRequest, background_tasks: BackgroundTasks, http_req: Request):
    if req.input_type not in ("url", "text", "image"):
        raise HTTPException(400, "input_type must be 'url', 'text', or 'image'")

    uid = await _get_uid_from_request(http_req)
    submitted_by = "community"
    if uid:
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
    job = _job_store.get(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    await _upsert_post_from_job(job_id, job)
    await _sync_job_counts_from_post(job_id)
    uid = await _get_uid_from_request(req)
    await _sync_user_vote(job_id, uid)
    return ResultResponse(job_id=job_id, **job)


@router.get("/results", response_model=list[AnalysisListItem])
async def list_results(req: Request):
    items: list[AnalysisListItem] = []
    uid = await _get_uid_from_request(req)
    seen_hashes: set[str] = set()
    for job_id, job in _job_store.items():
        if job.get("status") != "done":
            continue
        if bool(job.get("cached", False)):
            continue
        content_hash = job.get("content_hash")
        if content_hash:
            if content_hash in seen_hashes:
                continue
            seen_hashes.add(content_hash)
        await _sync_job_counts_from_post(job_id)
        await _sync_user_vote(job_id, uid)
        items.append(
            AnalysisListItem(
                job_id=job_id,
                status=job.get("status", "queued"),
                step=job.get("step"),
                input_type=job.get("input_type"),
                raw_input=job.get("raw_input"),
                created_at=job.get("created_at"),
                result=job.get("result"),
                content_hash=job.get("content_hash"),
                cached=bool(job.get("cached", False)),
                post_id=job.get("post_id"),
                submitted_by=job.get("submitted_by"),
                my_vote=job.get("my_vote"),
                upvotes=job.get("upvotes", 0),
                downvotes=job.get("downvotes", 0),
                disputes=job.get("disputes", 0),
            )
        )
    return items