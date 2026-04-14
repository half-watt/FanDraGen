"""Test that workflow steps are recorded in trace metadata."""

from workflows.orchestrator import WorkflowOrchestrator

def test_workflow_trace_metadata_steps():
    orchestrator = WorkflowOrchestrator()
    state = orchestrator.run("Suggest a trade for my team")
    steps = state.trace_metadata.get("workflow_steps", [])
    step_names = [step["step"] for step in steps]
    # Check that key workflow steps are present
    assert "route_decision" in step_names
    assert "trace_metadata_injected" in step_names
    assert "boss_agent_dispatched" in step_names
    assert "metrics_updated" in step_names
    # Steps should be in order
    assert step_names.index("route_decision") < step_names.index("boss_agent_dispatched")
    assert step_names[-1] == "metrics_updated"
