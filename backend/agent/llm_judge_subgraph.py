from langgraph.graph import StateGraph, END
from .nodes import query_builder_node, adversarial_searcher_node, alignment_node, judge_node, penalty_node
from schema.state import GraphState

def build_claim_processing_subgraph():
    """
    Compile and return the claim processing subgraph.
    Input state: GraphState with current_claim populated.
    Output state: claim_results list appended with one ClaimResult.
    """
    sg = StateGraph(GraphState)

    sg.add_node("query_builder", query_builder_node)
    sg.add_node("adversarial_searcher", adversarial_searcher_node)
    sg.add_node("alignment", alignment_node)
    sg.add_node("judge", judge_node)
    sg.add_node("penalty", penalty_node)

    sg.set_entry_point("query_builder")
    sg.add_edge("query_builder", "adversarial_searcher")
    sg.add_edge("adversarial_searcher", "alignment")
    sg.add_edge("alignment", "judge")
    sg.add_edge("judge", "penalty")
    sg.add_edge("penalty", END)

    return sg.compile()

# Singleton — compile once, reuse
claim_processing_subgraph = build_claim_processing_subgraph()