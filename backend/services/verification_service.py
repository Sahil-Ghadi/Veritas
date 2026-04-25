"""
Dispute verification service.

Real implementation:
  1. Domain credibility scoring — scores the counter_source_url domain against
     a tiered trust list (high/low/neutral).
  2. Tavily evidence search — retrieves external articles that support or refute
     the counter-argument.
  3. Gemini LLM adjudication — structured-output call that weighs the claim,
     current verdict, counter-argument, source credibility, and evidence to
     produce a final dispute_valid / confidence / reason / new_verdict.
"""

from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from core.llm_client import model
from services.input_parser import fetch_url_text

logger = logging.getLogger(__name__)


# ── Structured output schema ──────────────────────────────────────────────────

class VerificationOutput(BaseModel):
    dispute_valid: bool = Field(
        description=(
            "True if the counter-argument substantively challenges the original "
            "verdict with credible evidence. False if it is vague, unsupported, "
            "or from a low-credibility source."
        )
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Adjudicator confidence in this decision (0 = none, 1 = certain).",
    )
    reason: str = Field(
        description=(
            "Plain-English explanation (2–4 sentences) of why the dispute was "
            "accepted or rejected, citing specific evidence or its absence."
        )
    )
    new_verdict: str = Field(
        description=(
            "Suggested updated verdict. Use one of: "
            "SUPPORTED, CONTESTED, CONTRADICTED, UNVERIFIABLE."
        )
    )


# ── Domain credibility scorer ─────────────────────────────────────────────────

_HIGH_CREDIBILITY = {
    "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk",
    "nytimes.com", "washingtonpost.com", "theguardian.com",
    "nature.com", "science.org", "who.int", "cdc.gov",
    "nih.gov", "gov.uk", "europa.eu", "snopes.com",
    "factcheck.org", "politifact.com", "fullfact.org",
}

_LOW_CREDIBILITY = {
    "infowars.com", "naturalnews.com", "beforeitsnews.com",
    "worldnewsdailyreport.com", "empirenews.net", "yournewswire.com",
}


def _score_domain(url: Optional[str]) -> float:
    """Return a credibility score in [0, 1] for the domain of the given URL."""
    if not url:
        return 0.5  # no source — neutral penalty

    domain = urlparse(url).netloc.replace("www.", "").lower()

    if domain in _HIGH_CREDIBILITY:
        return 0.9
    if domain in _LOW_CREDIBILITY:
        return 0.1

    # TLD-based heuristics
    if domain.endswith((".gov", ".edu")):
        return 0.8
    if domain.endswith(".org"):
        return 0.6

    return 0.5  # unknown domain — neutral


# ── Prompt builder ────────────────────────────────────────────────────────────

def _build_adjudication_prompt(
    claim_text: str,
    current_verdict: str,
    counter_argument: str,
    counter_source_url: Optional[str],
    source_credibility: float,
    source_content: Optional[str],
) -> str:
    credibility_label = (
        "HIGH" if source_credibility >= 0.75
        else "LOW" if source_credibility <= 0.25
        else "MODERATE"
    )
    
    source_section = ""
    if source_content:
        source_section = f"\n\n─── COUNTER-SOURCE CONTENT ───\n{source_content[:2000]}"
        
    return f"""\
You are an impartial fact-check adjudicator reviewing a dispute against an \
AI-generated claim verdict.

─── ORIGINAL CLAIM ───
{claim_text}

─── CURRENT VERDICT ───
{current_verdict}

─── DISPUTER'S COUNTER-ARGUMENT ───
{counter_argument}

─── COUNTER-SOURCE ───
URL: {counter_source_url or "None provided"}
Domain credibility: {credibility_label} ({source_credibility:.2f}/1.0){source_section}

─── ADJUDICATION RULES ───
Accept the dispute (dispute_valid=true) ONLY if ALL of the following hold:
  1. The counter-argument presents a specific, falsifiable challenge — not
     just a general disagreement or emotional reaction.
  2. The counter-argument points out a logical flaw in the original verdict OR
     the counter-source domain is HIGH/MODERATE credibility OR the counter-source 
     content provides strong evidence.
  3. The source credibility is not LOW (≤ 0.25) unless the provided content
     overwhelmingly supports the counter-argument.

Reject the dispute (dispute_valid=false) if:
  • The counter-argument is vague, purely opinion-based, or lacks specifics.
  • The source credibility is LOW and no strong evidence is found in the content.

Set confidence proportionally to how clear-cut the decision is.
Suggest new_verdict from: SUPPORTED, CONTESTED, CONTRADICTED, UNVERIFIABLE.
"""


# ── Main verification function ────────────────────────────────────────────────

async def verify_dispute(
    claim_text: str,
    current_verdict: str,
    counter_argument: str,
    counter_source_url: Optional[str] = None,
) -> dict:
    """
    Verify a dispute against the original claim.

    Args:
        claim_text:         Full text of the claim being disputed.
        current_verdict:    The current verdict label (e.g. "supported").
        counter_argument:   The disputer's counter-argument text.
        counter_source_url: Optional URL the disputer provided as evidence.

    Returns:
        {
            dispute_valid       (bool)   – whether the dispute holds up
            confidence          (float)  – adjudicator confidence in [0, 1]
            reason              (str)    – human-readable explanation
            new_verdict         (str)    – suggested new verdict label
            source_credibility  (float)  – domain credibility score used
        }
    """
    # ── Step 1: Domain credibility + Content fetching ──────────────────────
    source_credibility = _score_domain(counter_source_url)
    logger.info(
        "verify_dispute | source_credibility=%.2f url=%s",
        source_credibility,
        counter_source_url,
    )

    source_content = None
    if counter_source_url:
        try:
            source_content = await fetch_url_text(counter_source_url)
        except Exception as exc:
            logger.warning("Failed to fetch counter_source_url %s: %s", counter_source_url, exc)

    # ── Step 2: LLM adjudication ───────────────────────────────────────────
    prompt = _build_adjudication_prompt(
        claim_text=claim_text,
        current_verdict=current_verdict,
        counter_argument=counter_argument,
        counter_source_url=counter_source_url,
        source_credibility=source_credibility,
        source_content=source_content,
    )

    structured_llm = model.with_structured_output(VerificationOutput)
    try:
        result: VerificationOutput = await structured_llm.ainvoke(prompt)
    except Exception as exc:
        logger.error("LLM adjudication failed: %s", exc, exc_info=True)
        raise RuntimeError(f"Adjudication failed: {exc}") from exc

    logger.info(
        "verify_dispute | valid=%s confidence=%.2f verdict=%s",
        result.dispute_valid,
        result.confidence,
        result.new_verdict,
    )

    return {
        "dispute_valid": result.dispute_valid,
        "confidence": round(result.confidence, 4),
        "reason": result.reason,
        "new_verdict": result.new_verdict,
        "source_credibility": source_credibility,
    }
