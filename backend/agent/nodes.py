import asyncio
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Any, List
from core.firebase import db_async
from schema.state import (
    GraphState,
    EssenceOutput,
    ClaimSplitOutput,
    QueryBuilderOutput,
    EvidenceJudgeOutput,
    ExplanationOutput,
)
from core.prompts import (
    ESSENCE_PROMPT,
    CLAIM_SPLIT_PROMPT,
    QUERY_BUILDER_PROMPT,
    EVIDENCE_JUDGE_PROMPT,
    AGGREGATOR_PROMPT,
)
from core.llm_client import model
from services.input_parser import parse_input
from services.web_search import adversarial_search
from services.essence_guard import check_essence_drift

_CACHE_COLLECTION = "analysis_cache"
_CACHE_TTL_DAYS = 7
_MAX_CLAIMS = 4

# Node 1: Cache Check
async def cache_check_node(state: GraphState) -> dict:
    """
    Hash raw_input → query Firestore analysis_cache.
    On a hit within TTL: restore all result fields so the pipeline can skip
    straight to score_aggregator.
    On a miss: just set content_hash so cache_writer can key correctly.
    """
    raw_hash = hashlib.sha256(state["raw_input"].strip().encode()).hexdigest()
    try:
        doc_snap = await db_async.collection(_CACHE_COLLECTION).document(raw_hash).get()
        if doc_snap.exists:
            data: dict = doc_snap.to_dict() or {}
            cached_at = data.get("cached_at")
            if cached_at is not None:
                # Firestore returns timezone-aware DatetimeWithNanoseconds
                if hasattr(cached_at, "tzinfo") and cached_at.tzinfo is None:
                    cached_at = cached_at.replace(tzinfo=timezone.utc)
                age = datetime.now(timezone.utc) - cached_at
                if age < timedelta(days=_CACHE_TTL_DAYS):
                    return {
                        "cached": True,
                        "content_hash": raw_hash,
                        "parsed_text": data.get("parsed_text", ""),
                        "essence": data.get("essence", ""),
                        "framing_tone": data.get("framing_tone", "neutral"),
                        "primary_actor": data.get("primary_actor", ""),
                        "implied_consequence": data.get("implied_consequence", ""),
                        "claims": data.get("claims", []),
                        "claim_results": data.get("claim_results", []),
                        "ai_score": data.get("ai_score", 0.5),
                        "score_breakdown": data.get("score_breakdown", {}),
                        "article_level_explanation": data.get("article_level_explanation", ""),
                        "drift_score": data.get("drift_score", 0.0),
                        "cached_result": data,
                    }
    except Exception as exc:
        # Cache failure is non-fatal — proceed with fresh analysis
        print(f"[cache_check] Firestore error: {exc}")

    return {"cached": False, "cached_result": None, "content_hash": raw_hash}

# Node 2: Input Parser
async def input_parser_node(state: GraphState) -> dict:
    """
    Fetch/parse the article text.
    content_hash is intentionally NOT returned here — cache_check_node is the
    authoritative owner of that field (keyed by sha256(raw_input)).
    """
    result = await parse_input(state["raw_input"], state["input_type"])
    return {"parsed_text": result["parsed_text"]}

# Node 3: Essence Extractor
async def essence_extractor_node(state: GraphState) -> dict:
    prompt = ESSENCE_PROMPT.format(article_text=state["parsed_text"][:6000])
    structured_llm = model.with_structured_output(EssenceOutput)
    result = await structured_llm.ainvoke(prompt)
    out = {
        "is_verifiable": result.is_verifiable,
        "essence": result.essence,
        "framing_tone": result.framing_tone,
        "primary_actor": result.primary_actor,
        "implied_consequence": result.implied_consequence,
    }
    if not result.is_verifiable and state.get("input_type") == "text":
        out["claim_results"] = [{
            "claim": "The provided text is a personal, anonymous, or non-news statement.",
            "claim_type": "fact",
            "verdict": "unverifiable",
            "confidence": 1.0,
            "reasoning": "This text does not contain public, verifiable claims or news. It appears to be a personal statement or conversational text.",
            "echo_chamber_detected": False,
            "supporting_sources": [],
            "contradicting_sources": []
        }]
        out["ai_score"] = 0.5
        out["score_breakdown"] = {"total_claims": 0, "fact_score": 0.5, "framing_score": 0.5}
        out["article_level_explanation"] = (
            "The provided text does not contain any checkable public claims or news events. "
            "Our system is designed to fact-check news, public allegations, and objective claims—not "
            "personal statements, opinions, or everyday conversational text. Please provide an article, "
            "news excerpt, or a verifiable public claim."
        )
        
    return out

# Node 4: Claim Splitter
async def claim_splitter_node(state: GraphState) -> dict:
    prompt = CLAIM_SPLIT_PROMPT.format(
        essence=state["essence"],
        article_text=state["parsed_text"][:6000],
    )
    structured_llm = model.with_structured_output(ClaimSplitOutput)
    result = await structured_llm.ainvoke(prompt)
    
    # Convert Claim models to dicts for GraphState compatibility
    claims_dict = [c.model_dump() for c in result.claims][:_MAX_CLAIMS]
    
    drift_result = check_essence_drift(state["essence"], claims_dict)
    return {
        "claims": claims_dict,
        "drift_score": drift_result["drift_score"],
    }

# Node 5: Claim Router
from langgraph.types import Send
def claim_router_node(state: GraphState) -> List[Send]:
    """
    Fan-out: Create a separate execution branch for each claim found.
    We remove claim-specific state (like current_claim and results) from the base
    state so each branch starts fresh, but inherits the context (essence, etc.).
    """
    base_state = dict(state)
    for key in ("current_claim", "current_search_results", "claim_results"):
        base_state.pop(key, None)
    
    claims = state.get("claims") or []
    return [
        Send("claim_processing", {**base_state, "current_claim": dict(claim)})
        for claim in state["claims"]
    ]

# Node 6: Query Builder
async def query_builder_node(state: GraphState) -> dict:
    claim = state["current_claim"]
    prompt = QUERY_BUILDER_PROMPT.format(
        claim=claim["text"],
        claim_type=claim.get("type", "fact"),
        essence=state["essence"],
    )
    structured_llm = model.with_structured_output(QueryBuilderOutput)
    result = await structured_llm.ainvoke(prompt)
    return {
        "current_claim": {
            **claim,
            "confirming_query": result.confirming_query,
            "contradicting_query": result.contradicting_query,
        }
    }

# Node 7: Adversarial Searcher
async def adversarial_searcher_node(state: GraphState) -> dict:
    claim = state["current_claim"]
    search_result = await adversarial_search(
        confirming_query=claim["confirming_query"],
        contradicting_query=claim["contradicting_query"],
        max_results_each=3,
    )
    return {
        "current_search_results": search_result["tagged_results"],
        "current_claim": {
            **claim,
            "echo_chamber_detected": search_result["echo_chamber_detected"],
            "no_contradiction_found": search_result["no_contradiction_found"],
        }
    }

# Sub-node for LLM Judge Subgraph - one LLM call per claim
async def evidence_judge_node(state: GraphState) -> dict:
    claim = state["current_claim"]
    results = state["current_search_results"]
    essence = state["essence"]

    # Fast-path: no search results — skip LLM entirely
    if not results:
        return {
            "current_search_results": [],
            "current_claim": {
                **claim,
                "has_direct_evidence": False,
                "verdict": "unverifiable",
                "confidence": 0.1,
                "reasoning": "No search results addressed this claim.",
                "false_detail": None,
                "uncertainty_reason": None,
            },
        }

    def extract_text(r: dict) -> str:
        body = (r.get("content") or "").strip()
        if body:
            return body[:500]
        title = (r.get("title") or "").strip()
        snippet = (r.get("snippet") or "").strip()
        return f"{title}\n{snippet}".strip()[:500]

    # Build a flat evidence block with pre-tagged stances from adversarial_search
    evidence_text = "\n\n".join(
        f"[Stance: {r.get('stance', 'unknown')}] URL: {r.get('url', '')}\n{extract_text(r)}"
        for r in results
    )

    prompt = EVIDENCE_JUDGE_PROMPT.format(
        claim=claim["text"],
        claim_type=claim.get("type", "fact"),
        essence=essence,
        evidence=evidence_text,
        diversity_note="WARNING: Echo chamber detected." if claim.get("echo_chamber_detected") else "Sources appear independent.",
        contradiction_note="NOTE: No contradiction found." if claim.get("no_contradiction_found") else "Contradicting evidence was searched.",
    )
    structured_llm = model.with_structured_output(EvidenceJudgeOutput)
    result = await structured_llm.ainvoke(prompt)

    # Enrich raw results with the LLM's per-URL classification
    url_to_alignment = {a.url: a.model_dump() for a in result.evidence_alignment}
    enriched = [{**r, **url_to_alignment.get(r.get("url", ""), {})} for r in results]

    return {
        "current_search_results": enriched,
        "current_claim": {
            **claim,
            "has_direct_evidence": result.has_direct_evidence,
            "verdict": result.verdict,
            "confidence": result.confidence,
            "false_detail": result.false_detail,
            "reasoning": result.reasoning,
            "uncertainty_reason": result.uncertainty_reason,
        },
    }

async def penalty_node(state: GraphState) -> dict:
    claim = state["current_claim"]
    results = state["current_search_results"]
    raw_conf = claim.get("confidence", 0.3)
    echo = claim.get("echo_chamber_detected", False)
    final_conf = round(raw_conf * (0.75 if echo else 1.0), 4)

    claim_result = {
        "claim": claim["text"],
        "claim_type": claim.get("type", "fact"),
        "verdict": claim.get("verdict", "uncertain"),
        "confidence": final_conf,
        "false_detail": claim.get("false_detail"),
        "reasoning": claim.get("reasoning", ""),
        "uncertainty_reason": claim.get("uncertainty_reason"),
        "echo_chamber_detected": echo,
        "supporting_sources": [r.get("url") for r in results if r.get("stance") == "supports"],
        "contradicting_sources": [r.get("url") for r in results if r.get("stance") == "contradicts"],
    }
    return {"claim_results": [claim_result]}

# Node 8 — Score Aggregator
VERDICT_WEIGHT = {"supported": 1.0, "uncertain": 0.5, "unverifiable": 0.4, "contradicted": 0.0}

async def score_aggregator_node(state: GraphState) -> dict:
    results = state.get("claim_results") or []
    print(f"[aggregator] Received {len(results)} claim results for final scoring.")
    
    if not results:
        return {"ai_score": 0.5, "score_breakdown": {}}

    def weighted_score(claims):
        if not claims: return None
        total_conf = sum(c["confidence"] for c in claims)
        if total_conf == 0: return 0.5
        return sum(VERDICT_WEIGHT.get(c["verdict"], 0.4) * c["confidence"] for c in claims) / total_conf

    fact_score = weighted_score([r for r in results if r.get("claim_type") == "fact"])
    framing_score = weighted_score([r for r in results if r.get("claim_type") == "framing"])

    if fact_score is not None and framing_score is not None:
        ai_score = round(0.7 * fact_score + 0.3 * framing_score, 4)
    else:
        ai_score = round(fact_score or framing_score or 0.5, 4)

    return {
        "ai_score": ai_score,
        "score_breakdown": {
            "total_claims": len(results),
            "fact_score": fact_score,
            "framing_score": framing_score,
        }
    }

# Node 9 — Explanation Generator
async def explanation_generator_node(state: GraphState) -> dict:
    claim_summaries = "\n".join([f"- {r['claim']} ({r['verdict']})" for r in state["claim_results"]])
    prompt = AGGREGATOR_PROMPT.format(
        essence=state.get("essence", ""),
        framing_tone=state.get("framing_tone", "neutral"),
        claim_summaries=claim_summaries,
        ai_score=round(state.get("ai_score", 0.5), 2),
    )
    structured_llm = model.with_structured_output(ExplanationOutput)
    result = await structured_llm.ainvoke(prompt)
    return {"article_level_explanation": result.explanation}

# Node 10 — Cache Writer
async def cache_writer_node(state: GraphState) -> dict:
    """
    Persist the full analysis result to Firestore analysis_cache.
    Uses the same sha256(raw_input) key as cache_check_node.
    Errors here are non-fatal — the caller already has the result.
    """
    content_hash = state.get("content_hash")
    if not content_hash:
        return {"content_hash_written": False}

    try:
        cache_doc = {
            "content_hash": content_hash,
            "cached_at": datetime.now(timezone.utc),
            "parsed_text": state.get("parsed_text", ""),
            "essence": state.get("essence", ""),
            "framing_tone": state.get("framing_tone", ""),
            "primary_actor": state.get("primary_actor", ""),
            "implied_consequence": state.get("implied_consequence", ""),
            "claims": state.get("claims", []),
            "claim_results": state.get("claim_results", []),
            "ai_score": state.get("ai_score", 0.5),
            "score_breakdown": state.get("score_breakdown", {}),
            "article_level_explanation": state.get("article_level_explanation", ""),
            "drift_score": state.get("drift_score", 0.0),
        }
        await db_async.collection(_CACHE_COLLECTION).document(content_hash).set(cache_doc)
        return {"content_hash_written": True}
    except Exception as exc:
        print(f"[cache_writer] Firestore error: {exc}")
        return {"content_hash_written": False}