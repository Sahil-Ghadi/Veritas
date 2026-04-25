from langgraph.graph import StateGraph, END
from .nodes import (
    cache_check_node,
    input_parser_node,
    essence_extractor_node,
    claim_splitter_node,
    claim_router_node,
    query_builder_node,
    adversarial_searcher_node,
    alignment_node,
    judge_node,
    penalty_node,
    score_aggregator_node,
    explanation_generator_node,
    cache_writer_node,
)
from schema.state import GraphState


def build_pipeline():
    workflow = StateGraph(GraphState)

    # ── Primary nodes ──────────────────────────────────────
    workflow.add_node("cache_check", cache_check_node)
    workflow.add_node("input_parser", input_parser_node)
    workflow.add_node("essence_extractor", essence_extractor_node)
    workflow.add_node("claim_splitter", claim_splitter_node)
    workflow.add_node("score_aggregator", score_aggregator_node)
    workflow.add_node("explanation_generator", explanation_generator_node)
    workflow.add_node("cache_writer", cache_writer_node)

    workflow.add_node("query_builder", query_builder_node)
    workflow.add_node("adversarial_searcher", adversarial_searcher_node)
    workflow.add_node("alignment", alignment_node)
    workflow.add_node("judge", judge_node)
    workflow.add_node("penalty", penalty_node)

    # ── Entry ──────────────────────────────────────────────
    workflow.set_entry_point("cache_check")

    # Cache hit  → score_aggregator (claim_results already in state)
    # Cache miss → full pipeline
    workflow.add_conditional_edges(
        "cache_check",
        lambda state: "score_aggregator" if state.get("cached") else "input_parser",
        {"score_aggregator": "score_aggregator", "input_parser": "input_parser"},
    )

    # ── Linear pre-processing ──────────────────────────────
    workflow.add_edge("input_parser", "essence_extractor")
    workflow.add_edge("essence_extractor", "claim_splitter")

    # ── Fan-out: claim_splitter → N parallel claim branches ─
    # claim_router_node returns List[Send("query_builder", per_claim_state)]
    workflow.add_conditional_edges(
        "claim_splitter",
        claim_router_node,
    )

    # ── Per-claim linear pipeline ──────────────────────────
    workflow.add_edge("query_builder", "adversarial_searcher")
    workflow.add_edge("adversarial_searcher", "alignment")
    workflow.add_edge("alignment", "judge")
    workflow.add_edge("judge", "penalty")

    # ── Fan-in: all penalty branches → score_aggregator ──
    # claim_results uses operator.add reducer so each branch's
    # [ClaimResult] is appended rather than overwritten
    workflow.add_edge("penalty", "score_aggregator")

    # ── Linear post-processing ─────────────────────────────
    workflow.add_edge("score_aggregator", "explanation_generator")
    workflow.add_edge("explanation_generator", "cache_writer")
    workflow.add_edge("cache_writer", END)

    return workflow.compile()


pipeline = build_pipeline()