from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from .engine import get_chatbot_response

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

class ChatRequest(BaseModel):
    message: str
    article_context: str = ""

@router.post("/chat")
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    reply = await get_chatbot_response(request.message, request.article_context)
    return {"reply": reply}

@router.get("/health")
async def health():
    """Check if Ollama is reachable."""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get("http://127.0.0.1:11434/api/tags")
            if resp.status_code == 200:
                return {"status": "ok", "ollama": "connected"}
            return {"status": "warning", "ollama": "unreachable", "code": resp.status_code}
    except Exception as e:
        return {"status": "error", "ollama": "disconnected", "error": str(e)}
