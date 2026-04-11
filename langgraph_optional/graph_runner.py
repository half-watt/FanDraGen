"""Optional LangGraph runner that mirrors the plain Python workflow."""

from __future__ import annotations

from langgraph_optional.graph_builder import build_graph
from workflows.orchestrator import WorkflowOrchestrator


def run_graph(query_text: str) -> dict[str, object]:
    """Run the optional graph mirror if LangGraph is available."""

    graph = build_graph()
    state = WorkflowOrchestrator().run(query_text)
    return {
        "graph": graph,
        "final_response": state.final_delivery_payload.json_payload if state.final_delivery_payload else {},
    }
