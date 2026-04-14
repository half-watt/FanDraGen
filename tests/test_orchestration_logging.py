"""Test that orchestration logging includes all key events."""

from workflows.orchestrator import WorkflowOrchestrator

def test_orchestration_logging_success():
    orchestrator = WorkflowOrchestrator()
    state = orchestrator.run("Suggest a trade for my team")
    event_types = [log.event_type for log in state.logs]
    # Check that success and dispatch logs are present
    assert "route_target_dispatched" in event_types
    assert "workflow_complete" in event_types
    # Check that no error log is present for a normal run
    assert not any(log.status == "error" for log in state.logs)
