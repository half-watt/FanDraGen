"""Workflow builder for draft-style requests."""

from __future__ import annotations

from schemas.models import AgentTask, WorkflowState


def build_tasks(state: WorkflowState) -> list[AgentTask]:
    return [
        AgentTask(
            task_type=state.route_decision.intent,
            description="Rank draft options and optionally recommend the top pick.",
            assigned_agent="DraftingAgent",
            requires_tools=["LeagueDataTool", "RecommendationTool", "PlayerStatsTool"],
        )
    ]
