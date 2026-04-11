"""Workflow builder for trade evaluation requests."""

from __future__ import annotations

from schemas.models import AgentTask, WorkflowState


def build_tasks(state: WorkflowState) -> list[AgentTask]:
    return [
        AgentTask(
            task_type="trade evaluation",
            description="Evaluate the proposed one-for-one trade using NBA stats CSV rows.",
            assigned_agent="TradeEvaluationAgent",
            input_payload={"give_player": "Top Player Omega", "receive_player": "Top Player Bravo"},
            requires_tools=["PlayerStatsTool", "RecommendationTool"],
        )
    ]
