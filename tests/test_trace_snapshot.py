"""Test that build_trace_snapshot produces a compact, inspectable state for logs/tests."""

from workflows.orchestrator import WorkflowOrchestrator
from utils.trace_utils import build_trace_snapshot

def test_build_trace_snapshot_for_inspection():
    state = WorkflowOrchestrator().run("Suggest a trade for my team")
    snapshot = build_trace_snapshot(state)
    # The snapshot should include all key fields for inspection
    assert "route" in snapshot
    assert "agents" in snapshot
    assert "tool_calls" in snapshot
    assert "fallback_flags" in snapshot
    assert "revision_count" in snapshot
    assert "approval_status" in snapshot
    assert "metrics" in snapshot
    assert "trace_metadata" in snapshot
    # The snapshot should be compact and serializable
    import json
    json.dumps(snapshot)  # Should not raise
    # At least one workflow step should be present in trace_metadata
    assert "workflow_steps" in snapshot["trace_metadata"]
    assert snapshot["trace_metadata"]["workflow_steps"]
