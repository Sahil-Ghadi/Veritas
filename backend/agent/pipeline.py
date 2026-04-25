from langgraph.graph import StateGraph, END
from .nodes import (
    cache_check_node,
    input_parser_node,
    essence_extractor_node,
    claim_splitter_node,
    claim_router_node,
    query_builder_node,
    adversarial_searcher_node,
    score_aggregator_node,
    explanation_generator_node,
    cache_writer_node,
)
from .llm_judge_subgraph import judge_subgraph
from schema.state import GraphState

def build_pipeline():
    # 1. Main Graph
    workflow = StateGraph(GraphState)

    # Add primary nodes
    workflow.add_node("cache_check", cache_check_node)
    workflow.add_node("input_parser", input_parser_node)
    workflow.add_node("essence_extractor", essence_extractor_node)
    workflow.add_node("claim_splitter", claim_splitter_node)
    workflow.add_node("score_aggregator", score_aggregator_node)
    workflow.add_node("explanation_generator", explanation_generator_node)
    workflow.add_node("cache_writer", cache_writer_node)

    # 2. Claim Pipeline (Branch)
    # This part handles individual claims in parallel
    workflow.add_node("query_builder", query_builder_node)
    workflow.add_node("adversarial_searcher", adversarial_searcher_node)
    workflow.add_node("llm_judge", judge_subgraph)

    # Set up edges
    workflow.set_entry_point("cache_check")

    # Cache hit  → skip straight to score_aggregator (claim_results already loaded)
    # Cache miss → full pipeline from input_parser
    workflow.add_conditional_edges(
        "cache_check",
        lambda state: "score_aggregator" if state.get("cached") else "input_parser",
        {"score_aggregator": "score_aggregator", "input_parser": "input_parser"},
    )
    workflow.add_edge("input_parser", "essence_extractor")
    workflow.add_edge("essence_extractor", "claim_splitter")
    
    # Fan-out from claim_splitter via claim_router
    workflow.add_conditional_edges(
        "claim_splitter",
        claim_router_node,
        ["query_builder"]
    )

    # Claim processing pipeline
    workflow.add_edge("query_builder", "adversarial_searcher")
    workflow.add_edge("adversarial_searcher", "llm_judge")
    
    # Fan-in: llm_judge results go to score_aggregator
    # Note: penalty_node in the subgraph appends to claim_results
    workflow.add_edge("llm_judge", "score_aggregator")

    workflow.add_edge("score_aggregator", "explanation_generator")
    workflow.add_edge("explanation_generator", "cache_writer")
    workflow.add_edge("cache_writer", END)

    return workflow.compile()

pipeline = build_pipeline()
