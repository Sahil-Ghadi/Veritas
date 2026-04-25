import uvicorn
from core.config import get_settings
import core.firebase  # noqa: F401 — triggers SDK init on import
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, analyze, dispute, vote, whatsapp
from chatbot.router import router as chatbot_router

settings = get_settings()

app = FastAPI()

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings["origins_list"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    pass


# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/auth")
app.include_router(analyze.router)          # prefix already set in router (/api)
app.include_router(dispute.router, prefix="/api")
app.include_router(vote.router, prefix="/api")
app.include_router(whatsapp.router)   # POST /whatsapp/webhook
app.include_router(chatbot_router)   # POST /chatbot/chat


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "env": settings["app_env"]}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
