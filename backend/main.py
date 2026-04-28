import uvicorn
from core.config import get_settings
import core.firebase  # noqa: F401 — triggers SDK init on import
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, analyze, dispute, vote, whatsapp
from chatbot.router import router as chatbot_router

settings = get_settings()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings["origins_list"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup
@app.on_event("startup")
async def startup():
    pass


# Routes
app.include_router(auth.router, prefix="/auth")
app.include_router(analyze.router)
app.include_router(dispute.router, prefix="/api")
app.include_router(vote.router, prefix="/api")
app.include_router(whatsapp.router)
app.include_router(chatbot_router)


@app.get("/health", tags=["Health"])
async def health():
    """Check all critical services."""
    import os
    import asyncio
    from core.firebase import db_async
    from services.web_search import _get_tavily

    checks = {
        "env": settings["app_env"],
        "firebase": "ok",
        "gemini": "not_configured",
        "tavily": "not_configured",
        "redis": "not_configured",
    }

    # Check Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        checks["gemini"] = "configured"

    # Check Tavily
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        try:
            _get_tavily()
            checks["tavily"] = "configured"
        except Exception:
            checks["tavily"] = "invalid_key"

    # Check Redis
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        checks["redis"] = "configured"

    # Check Firebase
    try:
        await db_async.collection("health_check").document("ping").get()
    except Exception:
        checks["firebase"] = "error"

    all_ok = all(v in ("ok", "configured") for v in checks.values())
    status = "ok" if all_ok else "degraded"

    return {"status": status, "checks": checks}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
