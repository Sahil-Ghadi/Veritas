import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict

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
    result: Optional[dict] = None
    error: Optional[str] = None

async def _run_pipeline(job_id: str, raw_input: str, input_type: str):
    from ..agent.pipeline import pipeline
    
    _job_store[job_id]["status"] = "processing"
    try:
        initial_state = {
            "raw_input": raw_input,
            "input_type": input_type,
            "cached": False,
            "claim_results": [],
        }
        final_state = await pipeline.ainvoke(initial_state)

        _job_store[job_id] = {
            "status": "done",
            "result": {
                "ai_score": final_state.get("ai_score"),
                "essence": final_state.get("essence"),
                "explanation": final_state.get("article_level_explanation"),
                "claims": final_state.get("claim_results", []),
            },
        }
    except Exception as exc:
        _job_store[job_id] = {"status": "error", "error": str(exc)}

@router.post("/analyze", response_model=AnalyzeResponse, status_code=202)
async def analyze(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    if req.input_type not in ("url", "text", "image"):
        raise HTTPException(400, "input_type must be 'url', 'text', or 'image'")

    job_id = str(uuid.uuid4())
    _job_store[job_id] = {"status": "queued"}

    background_tasks.add_task(_run_pipeline, job_id, req.raw_input, req.input_type)
    return AnalyzeResponse(job_id=job_id)

@router.get("/results/{job_id}", response_model=ResultResponse)
async def get_results(job_id: str):
    job = _job_store.get(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    return ResultResponse(job_id=job_id, **job)