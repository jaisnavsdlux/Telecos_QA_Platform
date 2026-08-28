from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from graph.state_schema import GraphState
from graph.nodes.zip_upload_node import zip_upload_node
from graph.nodes.mode_router_node import mode_router_node, route_mode
from graph.nodes.ingest_node import ingest_node
from graph.nodes.match_rules_node import match_rules_node
from graph.nodes.validate_node import validate_node
from graph.nodes.report_node import report_node

# ── Feature Stubs for Complete Architecture ──────────────────────────────

def rule_generator_node(state: GraphState):
    """(Stub) Rule generator: Excel -> rules.json"""
    print(f"[rule_generator] Creating rules for {state.get('job_id')}")
    return state

def fc_selector_node(state: GraphState):
    """(Stub) FC selector: user picks one FC diagram"""
    print(f"[fc_selector] Selecting FC for {state.get('job_id')}")
    return state

def report_validator_node(state: GraphState):
    """(Stub) Report validator: auto quality check"""
    print(f"[report_validator] Auto quality check for {state.get('job_id')}")
    # Default to true for now, meaning it skips human intervention unless flagged
    return {"report_quality_ok": True}

def human_in_loop_node(state: GraphState):
    """(Stub) Human in loop: Teams approval / Intervention"""
    print(f"[human_in_loop] Waiting for manual review on {state.get('job_id')}")
    return state


# ── Graph Compilation ───────────────────────────────────────────────────

def create_compliance_graph():
    workflow = StateGraph(GraphState)

    # 1. Add all nodes from the visual architecture
    workflow.add_node("zip_upload", zip_upload_node)
    workflow.add_node("mode_router", mode_router_node)
    workflow.add_node("rule_generator", rule_generator_node)
    workflow.add_node("fc_selector", fc_selector_node)
    workflow.add_node("ingest", ingest_node)
    
    # Validation nodes (composed of match_rules + validate in our codebase)
    workflow.add_node("match_rules", match_rules_node)
    workflow.add_node("validate", validate_node)
    
    workflow.add_node("report", report_node)
    workflow.add_node("report_validator", report_validator_node)
    workflow.add_node("human_in_loop", human_in_loop_node)

    # 2. Define the exact flow
    workflow.set_entry_point("zip_upload")
    workflow.add_edge("zip_upload", "mode_router")

    # Mode branch (create rules vs validate)
    workflow.add_conditional_edges(
        "mode_router",
        route_mode,
        {
            "create_rules": "rule_generator",
            "validate": "fc_selector"
        }
    )
    
    workflow.add_edge("rule_generator", END)

    # Validation branch
    workflow.add_edge("fc_selector", "ingest")
    workflow.add_edge("ingest", "match_rules")
    workflow.add_edge("match_rules", "validate")
    workflow.add_edge("validate", "report")
    workflow.add_edge("report", "report_validator")

    # Quality check branching
    def route_report_validator(state: GraphState):
        if state.get("report_quality_ok", True):
            # Satisfied -> Push back (Skipping SharePoint upload as requested, ending graph)
            return END
        else:
            # Not Satisfied -> Human in loop
            return "human_in_loop"

    workflow.add_conditional_edges(
        "report_validator",
        route_report_validator,
        {
            END: END,
            "human_in_loop": "human_in_loop"
        }
    )

    # Re-run logic from Human in loop
    def route_human_in_loop(state: GraphState):
        if state.get("approved"):
            return END
        else:
            # Re-run -> Back to validation nodes
            return "validate"

    workflow.add_conditional_edges(
        "human_in_loop",
        route_human_in_loop,
        {
            END: END,
            "validate": "validate"
        }
    )

    return workflow

def compile_graph(workflow, use_memory_saver=True):
    # Interruption targets for HITL
    breaks = ["fc_selector", "human_in_loop"]
    
    if use_memory_saver:
        checkpointer = MemorySaver()
        return workflow.compile(checkpointer=checkpointer, interrupt_before=breaks)
    else:
        return workflow.compile(interrupt_before=breaks)

# Core blueprints
workflow_blueprint = create_compliance_graph()
compliance_app = compile_graph(workflow_blueprint, use_memory_saver=True)
studio_app = compile_graph(workflow_blueprint, use_memory_saver=False)
