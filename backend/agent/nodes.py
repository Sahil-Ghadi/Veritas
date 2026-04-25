import asyncio
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Any, List
from ..core.firebase import db_async
from ..schema.state import (
    GraphState,
    EssenceOutput,
    ClaimSplitOutput,
    QueryBuilderOutput,
    AlignmentOutput,
    JudgeOutput,
    ExplanationOutput,
)
from ..core.prompts import (
    ESSENCE_PROMPT,
    CLAIM_SPLIT_PROMPT,
    QUERY_BUILDER_PROMPT,
    ALIGNMENT_PROMPT,
    JUDGE_PROMPT,
    AGGREGATOR_PROMPT,
)
from ..core.llm_client import model
from ..services.input_parser import parse_input
from ..services.web_search import adversarial_search
from ..services.essence_guard import check_essence_drift

_CACHE_COLLECTION = "analysis_cache"
_CACHE_TTL_DAYS = 7

# Node 1 — Cache Check
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

# Node 2 — Input Parser
async def input_parser_node(state: GraphState) -> dict:
    """
    Fetch/parse the article text.
    content_hash is intentionally NOT returned here — cache_check_node is the
    authoritative owner of that field (keyed by sha256(raw_input)).
    """
    result = await parse_input(state["raw_input"], state["input_type"])
    return {"parsed_text": result["parsed_text"]}

# Node 3 — Essence Extractor
async def essence_extractor_node(state: GraphState) -> dict:
    prompt = ESSENCE_PROMPT.format(article_text=state["parsed_text"][:6000])
    structured_llm = model.with_structured_output(EssenceOutput)
    result = await structured_llm.ainvoke(prompt)
    return {
        "essence": result.essence,
        "framing_tone": result.framing_tone,
        "primary_actor": result.primary_actor,
        "implied_consequence": result.implied_consequence,
    }

# Node 4 — Claim Splitter
async def claim_splitter_node(state: GraphState) -> dict:
    prompt = CLAIM_SPLIT_PROMPT.format(
        essence=state["essence"],
        article_text=state["parsed_text"][:6000],
    )
    structured_llm = model.with_structured_output(ClaimSplitOutput)
    result = await structured_llm.ainvoke(prompt)
    
    # Convert Claim models to dicts for GraphState compatibility
    claims_dict = [c.model_dump() for c in result.claims]
    
    drift_result = check_essence_drift(state["essence"], claims_dict)
    return {
        "claims": claims_dict,
        "drift_score": drift_result["drift_score"],
    }

# Node 5 — Claim Router
from langgraph.types import Send
def claim_router_node(state: GraphState) -> List[Send]:
    return [
        Send("query_builder", {**state, "current_claim": claim})
        for claim in state["claims"]
    ]

# Node 6 — Query Builder
async def query_builder_node(state: GraphState) -> dict:
    claim = state["current_claim"]
    prompt = QUERY_BUILDER_PROMPT.format(
        claim=claim["text"],
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

# Node 7 — Adversarial Searcher
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
            "diversity_score": search_result["diversity_score"],
            "echo_chamber_detected": search_result["echo_chamber_detected"],
            "no_contradiction_found": search_result["no_contradiction_found"],
        }
    }

# Sub-nodes for the LLM Judge Subgraph
async def alignment_node(state: GraphState) -> dict:
    claim = state["current_claim"]
    results = state["current_search_results"]
    evidence_text = "\n\n".join(
        f"URL: {r.get('url', '')}\n{r.get('content', r.get('raw_content', ''))[:400]}"
        for r in results
    )
    prompt = ALIGNMENT_PROMPT.format(claim=claim["text"], evidence=evidence_text)
    structured_llm = model.with_structured_output(AlignmentOutput)
    result = await structured_llm.ainvoke(prompt)

    enriched = []
    url_to_alignment = {a.url: a.model_dump() for a in result.evidence_alignment}
    for r in results:
        meta = url_to_alignment.get(r.get("url", ""), {})
        enriched.append({**r, **meta})

    return {
        "current_search_results": enriched,
        "current_claim": {**claim, "has_direct_evidence": result.has_direct_evidence},
    }

async def judge_node(state: GraphState) -> dict:
    claim = state["current_claim"]
    results = state["current_search_results"]
    essence = state["essence"]

    supporting = [r for r in results if r.get("stance") == "supports"
                  and r.get("relevance") in ("direct", "partial")]
    contradicting = [r for r in results if r.get("stance") == "contradicts"
                     and r.get("relevance") in ("direct", "partial")]

    def fmt_evidence(items):
        if not items: return "None found."
        return "\n\n".join(
            f"[{r.get('source_type','secondary').upper()}] {r.get('url','')}\n"
            f"{r.get('content', r.get('raw_content',''))[:350]}"
            for r in items
        )

    if not claim.get("has_direct_evidence", True):
        return {
            "current_claim": {
                **claim,
                "verdict": "unverifiable",
                "confidence": 0.1,
                "reasoning": "No search results directly addressed this claim.",
            }
        }

    prompt = JUDGE_PROMPT.format(
        claim=claim["text"],
        essence=essence,
        supporting_evidence=fmt_evidence(supporting),
        contradicting_evidence=fmt_evidence(contradicting),
        diversity_note="WARNING: Echo chamber detected." if claim.get("echo_chamber_detected") else "Sources appear independent.",
        contradiction_note="NOTE: No contradiction found." if claim.get("no_contradiction_found") else "Contradicting evidence was searched.",
    )
    structured_llm = model.with_structured_output(JudgeOutput)
    result = await structured_llm.ainvoke(prompt)
    return {
        "current_claim": {
            **claim,
            "verdict": result.verdict,
            "confidence": result.confidence,
            "false_detail": result.false_detail,
            "reasoning": result.reasoning,
            "uncertainty_reason": result.uncertainty_reason,
        }
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
        "supporting_sources": [r.get("url") for r in results if r.get("stance") == "supports"],
        "contradicting_sources": [r.get("url") for r in results if r.get("stance") == "contradicts"],
    }
    return {"claim_results": [claim_result]}

# Node 8 — Score Aggregator
VERDICT_WEIGHT = {"supported": 1.0, "uncertain": 0.5, "unverifiable": 0.4, "contradicted": 0.0}

async def score_aggregator_node(state: GraphState) -> dict:
    results = state["claim_results"]
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