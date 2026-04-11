"""Workflow builder for trade evaluation requests."""

from __future__ import annotations

from schemas.models import AgentTask, WorkflowState


def build_tasks(state: WorkflowState) -> list[AgentTask]:
    return [
        AgentTask(
            task_type="trade evaluation",
            description="Evaluate the proposed one-for-one trade in demo mode.",
            assigned_agent="TradeEvaluationAgent",
            input_payload={"give_player": "Luka Vance", "receive_player": "Tariq Cole"},
            requires_tools=["PlayerStatsTool", "RecommendationTool"],
        )
    ]
