"""Workflow builder for draft-style requests."""

from __future__ import annotations

from schemas.models import AgentTask, WorkflowState
from workflows.task_builder import single_task


def build_tasks(state: WorkflowState) -> list[AgentTask]:
    return single_task(
        task_type=state.route_decision.intent,
        description="Rank draft options and optionally recommend the top pick.",
        assigned_agent="DraftingAgent",
        requires_tools=["LeagueDataTool", "RecommendationTool", "PlayerStatsTool"],
    )
