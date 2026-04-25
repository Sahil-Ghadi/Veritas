from langgraph.graph import StateGraph, END
from .nodes import alignment_node, judge_node, penalty_node
from ..schema.state import GraphState

def build_judge_subgraph():
    """
    Compile and return the LLM judge subgraph.
    Input state: GraphState with current_claim + current_search_results populated.
    Output state: claim_results list appended with one ClaimResult.
    """
    sg = StateGraph(GraphState)

    sg.add_node("alignment", alignment_node)
    sg.add_node("judge", judge_node)
    sg.add_node("penalty", penalty_node)

    sg.set_entry_point("alignment")
    sg.add_edge("alignment", "judge")
    sg.add_edge("judge", "penalty")
    sg.add_edge("penalty", END)

    return sg.compile()

# Singleton — compile once, reuse
judge_subgraph = build_judge_subgraph()