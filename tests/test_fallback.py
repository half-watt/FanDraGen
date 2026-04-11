"""Fallback and revision-loop tests."""

from __future__ import annotations

from workflows.orchestrator import WorkflowOrchestrator


def test_missing_data_prompt_triggers_fallback_and_single_revision() -> None:
    state = WorkflowOrchestrator().run("What assumptions are you making because data is missing?")
    assert "missing_projection_source_local_mode" in state.fallback_flags
    assert state.revision_count == 1
    assert state.final_delivery_payload is not None
