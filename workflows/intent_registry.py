"""
Intent Registry: Central mapping from routed intent to workflow builder.

To add a new intent:
1. Add the intent and its keywords to INTENT_KEYWORDS.
2. Add the intent to INTENT_PRIORITY in the desired order.
3. Add the intent and its workflow builder to INTENT_TO_WORKFLOW.
4. Add tests and update docs as needed.

This registry enforces that all supported intents are mapped in all relevant places, and that unknown or unmapped intents trigger explicit fallback and logging.
"""

from __future__ import annotations

from schemas.models import AgentTask, WorkflowState
from typing import Literal
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


IntentKey = Literal[
    "onboarding/help",
    "draft advice",
    "lineup optimization",
    "trade evaluation",
    "waiver/free agent pickup",
    "roster news summary",
    "explanation / why reasoning",
    "missing data / fallback explanation",
]

INTENT_KEYWORDS: dict[IntentKey, list[str]] = {
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
INTENT_PRIORITY: tuple[IntentKey, ...] = (
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


INTENT_TO_WORKFLOW: dict[IntentKey, callable] = {
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

def intent_workflow_mapping() -> dict[str, str]:
    """Return a mapping of intent keys to workflow builder function names (for docs, tests, UI)."""
    return {k: v.__name__ if hasattr(v, '__name__') else str(v) for k, v in INTENT_TO_WORKFLOW.items()}

#
# To add a new intent:
# 1. Add the intent and its keywords to INTENT_KEYWORDS.
# 2. Add the intent to INTENT_PRIORITY in the desired order.
# 3. Add the intent and its workflow builder to INTENT_TO_WORKFLOW.
# 4. Add tests and update docs as needed.
#


def build_tasks_for_route(state: WorkflowState) -> list[AgentTask]:
    """Return worker tasks for the current `state.route_decision.intent`."""

    intent = state.route_decision.intent if state.route_decision else DEFAULT_INTENT
    builder = INTENT_TO_WORKFLOW.get(intent)
    if builder is None:
        state.add_fallback(f"unknown_intent:{intent}")
        log_event(
            state,
            event_type="intent_registry_fallback",
            agent="IntentRegistry",
            tool="N/A",
            status="warning",
            message=f"Unknown intent: {intent}",
            details={"unknown_intent": intent},
        )
        return _fallback_task()
    return builder(state)
