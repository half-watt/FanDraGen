"""Workflow builder for lineup optimization requests."""

from __future__ import annotations

from schemas.models import AgentTask, WorkflowState


def build_tasks(state: WorkflowState) -> list[AgentTask]:
    return [
        AgentTask(
            task_type="lineup optimization",
            description="Build the best lineup from the current roster.",
            assigned_agent="ManagingAgent",
            requires_tools=["LeagueDataTool", "RecommendationTool", "PlayerStatsTool"],
        )
    ]
