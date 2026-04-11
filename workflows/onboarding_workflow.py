"""Workflow builder for onboarding/help requests."""

from __future__ import annotations

from schemas.models import AgentTask, WorkflowState


def build_tasks(state: WorkflowState) -> list[AgentTask]:
    return [
        AgentTask(
            task_type="onboarding/help",
            description="Explain the mocked NBA league rules and how the system works.",
            assigned_agent="OnboardingAgent",
            requires_tools=["RulesTool", "LeagueDataTool"],
        )
    ]
