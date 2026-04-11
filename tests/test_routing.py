"""Routing tests for the deterministic router."""

from __future__ import annotations

from agents.routing_agent import RoutingAgent
from schemas.models import UserQuery, WorkflowState


def test_routes_draft_prompt_to_nba_boss() -> None:
    router = RoutingAgent()
    query = UserQuery(text="Who should I draft first from the available player pool?")
    state = WorkflowState(original_user_query=query)
    decision = router.route(query, state)

    assert decision.intent == "draft advice"
    assert decision.route_target == "NBABossAgent"
    assert decision.domain == "nba"


def test_routes_missing_data_prompt() -> None:
    router = RoutingAgent()
    query = UserQuery(text="What assumptions are you making because data is missing?")
    state = WorkflowState(original_user_query=query)
    decision = router.route(query, state)

    assert decision.intent == "missing data / fallback explanation"
