"""Single mapping from routed intent to worker tasks (replaces scattered imports in the boss)."""

from __future__ import annotations

from schemas.models import AgentTask, WorkflowState

from workflows import (
    draft_workflow,
    lineup_workflow,
    news_workflow,
    onboarding_workflow,
    trade_workflow,
    waiver_workflow,
)


def build_tasks_for_route(state: WorkflowState) -> list[AgentTask]:
    """Return worker tasks for the current `state.route_decision.intent`."""

    intent = state.route_decision.intent if state.route_decision else "onboarding/help"
    if intent == "onboarding/help":
        return onboarding_workflow.build_tasks(state)
    if intent in {"draft advice", "explanation / why reasoning"}:
        return draft_workflow.build_tasks(state)
    if intent == "lineup optimization":
        return lineup_workflow.build_tasks(state)
    if intent == "trade evaluation":
        return trade_workflow.build_tasks(state)
    if intent == "waiver/free agent pickup":
        return waiver_workflow.build_tasks(state)
    if intent == "roster news summary":
        return news_workflow.build_tasks(state)
    return [
        AgentTask(
            task_type="missing data / fallback explanation",
            description="Explain fallback and missing-data behavior.",
            assigned_agent="ManagingAgent",
        )
    ]
