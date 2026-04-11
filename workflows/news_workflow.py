"""Workflow builder for roster news requests."""

from __future__ import annotations

from schemas.models import AgentTask, WorkflowState


def build_tasks(state: WorkflowState) -> list[AgentTask]:
    return [
        AgentTask(
            task_type="roster news summary",
            description="Summarize the most relevant roster news.",
            assigned_agent="NewsSummarizationAgent",
            requires_tools=["LeagueDataTool", "NewsTool"],
        )
    ]
