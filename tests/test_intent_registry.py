"""Intent registry maps routed intents to worker tasks."""

from __future__ import annotations

from agents.routing_agent import RoutingAgent
from schemas.models import RouteDecision, UserQuery, WorkflowState
from workflows.intent_registry import build_tasks_for_route, supported_intents


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


def test_supported_intents_match_router_keys() -> None:
    assert supported_intents() == set(RoutingAgent.intent_keywords.keys())


def test_registry_unknown_intent_adds_fallback_flag() -> None:
    state = _state("unknown-intent-xyz")
    build_tasks_for_route(state)

    assert "unknown_intent:unknown-intent-xyz" in state.fallback_flags
