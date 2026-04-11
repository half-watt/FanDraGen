"""Boss-agent tests."""

from __future__ import annotations

from workflows.orchestrator import WorkflowOrchestrator


def test_boss_agent_decomposes_trade_workflow() -> None:
    state = WorkflowOrchestrator().run("Should I trade Player A for Player B?")
    decomposition_events = [entry for entry in state.logs if entry["event"] == "boss_decomposition"]

    assert decomposition_events
    tasks = decomposition_events[0]["details"]["tasks"]
    assert tasks[0]["assigned_agent"] == "TradeEvaluationAgent"
    assert state.approval_status.approval_required is True
