"""Intent registry maps routed intents to worker tasks."""

from __future__ import annotations

from schemas.models import RouteDecision, UserQuery, WorkflowState
from workflows.intent_registry import build_tasks_for_route


def _state(intent: str) -> WorkflowState:
    st = WorkflowState(original_user_query=UserQuery(text="x"))
    st.route_decision = RouteDecision(
        intent=intent,
        domain="nba",
        route_target="NBABossAgent",
        confidence=0.9,
        reasoning="test",
    )
    return st


def test_registry_maps_trade_intent() -> None:
    tasks = build_tasks_for_route(_state("trade evaluation"))
    assert tasks[0].assigned_agent == "TradeEvaluationAgent"


def test_registry_maps_lineup_intent() -> None:
    tasks = build_tasks_for_route(_state("lineup optimization"))
    assert tasks[0].assigned_agent == "ManagingAgent"


def test_registry_fallback_missing_intent_goes_to_managing_agent() -> None:
    tasks = build_tasks_for_route(_state("unknown-intent-xyz"))
    assert tasks[0].task_type == "missing data / fallback explanation"
