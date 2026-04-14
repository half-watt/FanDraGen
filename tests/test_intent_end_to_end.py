"""Test that all major user intents have an end-to-end workflow path."""

from workflows.intent_registry import supported_intents, build_tasks_for_route
from schemas.models import WorkflowState, UserQuery, RouteDecision
import pytest

def make_state_for_intent(intent):
    query = UserQuery(text=f"test for {intent}")
    state = WorkflowState(original_user_query=query)
    state.route_decision = RouteDecision(
        intent=intent,
        domain="nba",
        route_target="NBABossAgent",
        confidence=1.0,
        reasoning="test"
    )
    return state

@pytest.mark.parametrize("intent", list(supported_intents()))
def test_intent_has_workflow_path(intent):
    state = make_state_for_intent(intent)
    tasks = build_tasks_for_route(state)
    assert isinstance(tasks, list)
    assert tasks, f"No tasks returned for intent: {intent}"
    # Optionally: check that at least one task has the correct agent or type
    assert hasattr(tasks[0], "assigned_agent")
