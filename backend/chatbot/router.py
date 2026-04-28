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
    """Check if Gemini API key is configured."""
    import os
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return {"status": "ok", "gemini": "configured"}
    return {"status": "error", "gemini": "not_configured", "error": "GEMINI_API_KEY not set"}
