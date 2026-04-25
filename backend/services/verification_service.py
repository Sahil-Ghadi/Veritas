"""
Dispute verification service.

Current implementation: STUB (always returns dispute_valid=True, confidence=0.82).

TODO — replace with the real verification chain:
  1. Source credibility scoring:
       - Extract domain from counter_source_url.
       - Score the domain against a trust/credibility database
         (e.g. NewsGuard, MBFC, or a custom Firestore trust-scores collection).
       - Return a float in [0, 1] representing source credibility.

  2. Tavily web search cross-reference:
       - Use TavilySearchResults (langchain_community.tools) to search for
         evidence supporting or refuting the counter_argument.
       - Feed the top N results as context to the adjudicator.

  3. Claude adjudication:
       - Send claim_text, current_verdict, counter_argument, source snippets,
         and source credibility score to Claude via LangChain ChatAnthropic.
       - Use a structured output schema (Pydantic model) so Claude returns:
           { dispute_valid, confidence, reason, new_verdict }
       - Parse and return this as the verification result dict.
"""

import asyncio
from typing import Optional


async def verify_dispute(
    claim_text: str,
    current_verdict: str,
    counter_argument: str,
    counter_source_url: Optional[str] = None,
) -> dict:
    """
    Verify a dispute against the original claim.

    Args:
        claim_text: The full text of the claim being disputed.
        current_verdict: The current verdict label on the claim (e.g. "TRUE", "FALSE").
        counter_argument: The disputer's counter-argument text.
        counter_source_url: Optional URL the disputer provided as evidence.

    Returns:
        A dict with keys:
            dispute_valid (bool)   – whether the dispute holds up
            confidence   (float)  – adjudicator confidence in [0, 1]
            reason       (str)    – human-readable explanation
            new_verdict  (str)    – suggested new verdict label
            score_impact (float)  – raw suggested impact (used for reference; final
                                    impact is computed by score_service.calculate_score_impact)
    """
    # Simulate network / LLM latency
    await asyncio.sleep(1.5)

    # ── STUB RESPONSE ──────────────────────────────────────────────────────────
    return {
        "dispute_valid": True,
        "confidence": 0.82,
        "reason": "Stub: not yet implemented",
        "new_verdict": "CONTESTED",
        "score_impact": -8.5,
    }
