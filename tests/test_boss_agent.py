"""Boss-agent tests."""

from __future__ import annotations

from agents.boss.nba_boss import NBABossAgent
from schemas.models import AgentTask, RouteDecision, UserQuery, WorkflowState
from workflows.orchestrator import WorkflowOrchestrator


def test_boss_agent_decomposes_trade_workflow() -> None:
    state = WorkflowOrchestrator().run("Should I trade Player A for Player B?")
    decomposition_events = [entry for entry in state.logs if entry["event"] == "boss_decomposition"]

    assert decomposition_events
    tasks = decomposition_events[0]["details"]["tasks"]
    assert tasks[0]["assigned_agent"] == "TradeEvaluationAgent"
    assert state.approval_status.approval_required is True


def test_boss_falls_back_when_worker_assignment_missing() -> None:
    boss = NBABossAgent()
    state = WorkflowState(original_user_query=UserQuery(text="fallback test"))
    state.route_decision = RouteDecision(
        intent="lineup optimization",
        domain="nba",
        route_target="NBABossAgent",
        confidence=0.9,
        reasoning="test",
    )

    def _bad_build(_state: WorkflowState) -> list[AgentTask]:
        return [
            AgentTask(
                task_type="lineup optimization",
                description="invalid worker task",
                assigned_agent="NotARealAgent",
            )
        ]

    boss._build_tasks = _bad_build
    boss.run(state)

    assert "missing_worker:NotARealAgent" in state.fallback_flags
