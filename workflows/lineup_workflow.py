"""Workflow builder for lineup optimization requests."""

from __future__ import annotations

from schemas.models import AgentTask, WorkflowState
from workflows.task_builder import single_task


def build_tasks(state: WorkflowState) -> list[AgentTask]:
    return single_task(
        task_type="lineup optimization",
        description="Build the best lineup from the current roster.",
        assigned_agent="ManagingAgent",
        requires_tools=["LeagueDataTool", "RecommendationTool", "PlayerStatsTool"],
    )
