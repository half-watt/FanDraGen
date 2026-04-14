"""Test that fallback and unknown intent handling is visible in logs and trace."""

from workflows.intent_registry import build_tasks_for_route
from schemas.models import WorkflowState, UserQuery

def test_unknown_intent_fallback_logged():
    state = WorkflowState(original_user_query=UserQuery(text="foobar"))
    state.route_decision = type("FakeRoute", (), {"intent": "not_a_real_intent"})()
    tasks = build_tasks_for_route(state)
    # Should fallback to the fallback task
    assert tasks[0].task_type == "missing data / fallback explanation"
    # Should log the fallback
    found = any(
        log.event_type == "intent_registry_fallback" and log.details.get("unknown_intent") == "not_a_real_intent"
        for log in state.logs
    )
    assert found, "Fallback for unknown intent was not logged in state.logs"
