import re
import os
import httpx
import base64
from agent.pipeline import pipeline
from services.twilio_service import twilio_service


async def analyze_whatsapp_task(
    ctx,  # ARQ context (contains redis connection etc.)
    user_phone: str,
    text: str,
    media_url: str = None,
):
    input_type = "text"
    raw_input = text

    if media_url:
        try:
            auth = (os.getenv("TWILIO_ACCOUNT_SID", ""), os.getenv("TWILIO_AUTH_TOKEN", ""))
            async with httpx.AsyncClient() as client:
                resp = await client.get(media_url, follow_redirects=True, auth=auth)
                resp.raise_for_status()
                raw_input = base64.b64encode(resp.content).decode("utf-8")
                input_type = "image"
        except Exception as exc:
            print(f"[analyze_whatsapp_task] Failed to download media: {exc}")
            twilio_service.send_whatsapp(
                to=user_phone,
                body="❌ Could not download the image. Please try again or send a text/link."
            )
            return
    elif text:
        # Look for the first URL in the text
        url_match = re.search(r'(https?://\S+)', text, re.IGNORECASE)
        if url_match:
            raw_input = url_match.group(1)
            input_type = "url"

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

        body_parts = [
            f"{label} — {int(score * 100)}% credibility",
            "",
            explanation,
        ]

        claims = result.get("claim_results", [])
        supporting = set()
        contradictory = set()
        for claim in claims:
            for s in claim.get("supporting_sources", []):
                supporting.add(s)
            for s in claim.get("contradicting_sources", []):
                contradictory.add(s)

        if supporting:
            body_parts.append("\n✅ *Supporting Sources:*")
            for url in list(supporting)[:5]:
                body_parts.append(f"• {url}")
                
        if contradictory:
            body_parts.append("\n❌ *Contradictory Sources:*")
            for url in list(contradictory)[:5]:
                body_parts.append(f"• {url}")

        body = "\n".join(body_parts)

    except Exception as exc:
        print(f"[analyze_whatsapp_task] Pipeline error: {exc}")
        body = (
            "❌ Analysis failed. Please try again or visit https://veritas.app"
        )

    twilio_service.send_whatsapp(to=user_phone, body=body)
