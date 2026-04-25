from langgraph.graph import StateGraph, END
from .nodes import query_builder_node, adversarial_searcher_node, evidence_judge_node, penalty_node
from schema.state import GraphState

def build_claim_processing_subgraph():
    """
    Compile and return the claim processing subgraph.
    Input state: GraphState with current_claim populated.
    Output state: claim_results list appended with one ClaimResult.

    Performance: alignment + judge have been merged into evidence_judge_node,
    cutting LLM calls per claim from 2 → 1.
    """
    sg = StateGraph(GraphState)

    sg.add_node("query_builder", query_builder_node)
    sg.add_node("adversarial_searcher", adversarial_searcher_node)
    sg.add_node("evidence_judge", evidence_judge_node)  # replaces alignment + judge
    sg.add_node("penalty", penalty_node)

    sg.set_entry_point("query_builder")
    sg.add_edge("query_builder", "adversarial_searcher")
    sg.add_edge("adversarial_searcher", "evidence_judge")
    sg.add_edge("evidence_judge", "penalty")
    sg.add_edge("penalty", END)

    return sg.compile()

# Singleton — compile once, reuse
claim_processing_subgraph = build_claim_processing_subgraph()