"""Workflow builder for waiver and free-agent requests."""

from __future__ import annotations

from schemas.models import AgentTask, WorkflowState
from workflows.task_builder import single_task


def build_tasks(state: WorkflowState) -> list[AgentTask]:
    return single_task(
        task_type="waiver/free agent pickup",
        description="Identify the best current waiver pickup.",
        assigned_agent="ManagingAgent",
        requires_tools=["LeagueDataTool", "RecommendationTool"],
    )
