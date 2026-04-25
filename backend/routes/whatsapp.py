"""
WhatsApp webhook — registered at POST /whatsapp/webhook.

Flow:
  1. Twilio POSTs inbound message here
  2. We respond with empty TwiML instantly (<1s)
  3. We send an "Analyzing…" outbound message via Twilio REST API
  4. We enqueue the heavy pipeline job onto Redis (ARQ)
  5. The ARQ worker picks it up, runs the pipeline, sends the verdict
"""
import os
from fastapi import APIRouter, Form, Depends
from fastapi.responses import Response
from arq import create_pool
from arq.connections import RedisSettings
from dotenv import load_dotenv

from services.twilio_service import twilio_service

load_dotenv()

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


# ── Redis pool dependency ─────────────────────────────────────────────────────
async def get_redis():
    settings = RedisSettings.from_dsn(
        os.getenv("REDIS_URL", "redis://localhost:6379")
    )
    redis = await create_pool(settings)
    try:
        yield redis
    finally:
        await redis.aclose()


# ── Webhook ───────────────────────────────────────────────────────────────────
@router.post("/webhook")
async def whatsapp_webhook(
    Body: str = Form(default=""),
    From: str = Form(...),
    MediaUrl0: str = Form(default=None),
    redis=Depends(get_redis),
):
    # 1. Send instant "working" reply via outbound API
    twilio_service.send_whatsapp(
        to=From,
        body=(
            "🔍 *Analyzing your message…*\n"
            "This usually takes around 60 seconds. "
            "I'll send the full verdict here when it's ready!"
        ),
    )

    # 2. Push job to ARQ queue
    await redis.enqueue_job(
        "analyze_whatsapp_task",
        user_phone=From,
        text=Body,
        media_url=MediaUrl0,
    )

    # 3. Return empty TwiML so Twilio knows we received it
    return Response(
        content="<Response></Response>",
        media_type="application/xml",
    )
