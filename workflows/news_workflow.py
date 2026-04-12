"""Workflow builder for roster news requests."""

from __future__ import annotations

from schemas.models import AgentTask, WorkflowState
from workflows.task_builder import single_task


def build_tasks(state: WorkflowState) -> list[AgentTask]:
    return single_task(
        task_type="roster news summary",
        description="Summarize the most relevant roster news.",
        assigned_agent="NewsSummarizationAgent",
        requires_tools=["LeagueDataTool", "NewsTool"],
    )
