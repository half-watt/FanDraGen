"""Single mapping from routed intent to worker tasks (replaces scattered imports in the boss)."""

from __future__ import annotations

from schemas.models import AgentTask, WorkflowState
from utils.logging_utils import log_event

from workflows import (
    draft_workflow,
    lineup_workflow,
    news_workflow,
    onboarding_workflow,
    trade_workflow,
    waiver_workflow,
)
from workflows.task_builder import single_task


INTENT_KEYWORDS: dict[str, list[str]] = {
    "onboarding/help": ["new", "how does this league work", "help", "league work"],
    "draft advice": ["draft", "draft first"],
    "lineup optimization": ["best lineup", "set my best lineup", "lineup"],
    "trade evaluation": ["trade"],
    "waiver/free agent pickup": ["waiver", "pickup", "free agent"],
    "roster news summary": ["news", "summarize important news"],
    "explanation / why reasoning": ["why", "rank these players", "explain"],
    "missing data / fallback explanation": ["assumptions", "missing data", "fallback"],
}

# More specific intents are matched before generic onboarding/help (which includes "new").
INTENT_PRIORITY: tuple[str, ...] = (
    "missing data / fallback explanation",
    "explanation / why reasoning",
    "roster news summary",
    "waiver/free agent pickup",
    "trade evaluation",
    "lineup optimization",
    "draft advice",
    "onboarding/help",
)

DEFAULT_INTENT = "onboarding/help"


def _fallback_task() -> list[AgentTask]:
    return single_task(
        task_type="missing data / fallback explanation",
        description="Explain fallback and missing-data behavior.",
        assigned_agent="ManagingAgent",
    )


INTENT_TO_WORKFLOW = {
    "onboarding/help": onboarding_workflow.build_tasks,
    "draft advice": draft_workflow.build_tasks,
    "lineup optimization": lineup_workflow.build_tasks,
    "trade evaluation": trade_workflow.build_tasks,
    "waiver/free agent pickup": waiver_workflow.build_tasks,
    "roster news summary": news_workflow.build_tasks,
    "explanation / why reasoning": draft_workflow.build_tasks,
    "missing data / fallback explanation": lambda _state: _fallback_task(),
}


def supported_intents() -> set[str]:
    """Return all canonical intent keys."""

    return set(INTENT_TO_WORKFLOW)


def build_tasks_for_route(state: WorkflowState) -> list[AgentTask]:
    """Return worker tasks for the current `state.route_decision.intent`."""

    intent = state.route_decision.intent if state.route_decision else DEFAULT_INTENT
    builder = INTENT_TO_WORKFLOW.get(intent)
    if builder is None:
        state.add_fallback(f"unknown_intent:{intent}")
        log_event(state, "intent_registry_fallback", unknown_intent=intent)
        return _fallback_task()
    return builder(state)
