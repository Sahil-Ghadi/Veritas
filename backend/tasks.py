"""
Background task executed by the ARQ worker.
Runs the full Veritas LangGraph pipeline, then sends the verdict
back to the user via Twilio WhatsApp.
"""
from agent.pipeline import pipeline
from services.twilio_service import twilio_service


async def analyze_whatsapp_task(
    ctx,  # ARQ context (contains redis connection etc.)
    user_phone: str,
    text: str,
    media_url: str = None,
):
    input_type = "image" if media_url else "text"
    raw_input = media_url if media_url else text

    try:
        # ── Run the pipeline ──────────────────────────────────────────────────
        result = await pipeline.ainvoke({
            "raw_input": raw_input,
            "input_type": input_type,
        })

        score: float = result.get("ai_score", 0.5)
        explanation: str = result.get("article_level_explanation", "")
        content_hash: str = result.get("content_hash", "")

        # ── Pick an icon / label ──────────────────────────────────────────────
        if score >= 0.8:
            label = "✅ *TRUE*"
        elif score >= 0.55:
            label = "⚠️ *MISLEADING*"
        elif score >= 0.35:
            label = "🔍 *UNVERIFIED*"
        else:
            label = "❌ *FALSE*"

        # Shorten explanation to WhatsApp-safe length
        short_explanation = (
            explanation[:350] + "…" if len(explanation) > 350 else explanation
        )

        report_url = (
            f"https://veritas.app/analyze/{content_hash}"
            if content_hash
            else "https://veritas.app"
        )

        body = "\n".join([
            f"{label} — {int(score * 100)}% credibility",
            "",
            short_explanation,
            "",
            f"📊 Full breakdown: {report_url}",
        ])

    except Exception as exc:
        print(f"[analyze_whatsapp_task] Pipeline error: {exc}")
        body = (
            "❌ Analysis failed. Please try again or visit https://veritas.app"
        )

    twilio_service.send_whatsapp(to=user_phone, body=body)
