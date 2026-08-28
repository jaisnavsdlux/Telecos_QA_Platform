from typing import Dict, Any
from graph.state_schema import GraphState


def mode_router_node(state: GraphState) -> Dict[str, Any]:
    """
    Node: Mode Router
    Decides whether the run should:
      - 'validate'     → proceed to FC selector → ingest → validation nodes
      - 'create_rules' → send Excel checklist to rule generator
    The mode is set by the caller (API, Studio, or Teams bot) when the job is created.
    """
    mode = state.get("mode", "validate")
    print(f"[mode_router] Mode selected: {mode}")
    return {"mode": mode, "status": f"routed:{mode}"}


def route_mode(state: GraphState) -> str:
    """
    Conditional edge function called by LangGraph after mode_router_node.
    Returns the name of the next node.
    """
    return state.get("mode", "validate")
