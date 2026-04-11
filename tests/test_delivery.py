"""Delivery formatting tests."""

from __future__ import annotations

from agents.delivery.delivery_agent import DeliveryAgent
from schemas.models import AgentResult, Recommendation, RouteDecision, UserQuery, WorkflowState


def test_delivery_returns_json_and_markdown() -> None:
    state = WorkflowState(original_user_query=UserQuery(text="Who should I draft first from the available player pool?"))
    state.route_decision = RouteDecision(
        intent="draft advice",
        domain="nba",
        route_target="NBABossAgent",
        confidence=0.9,
        reasoning="test",
    )
    result = AgentResult(
        agent_name="DraftingAgent",
        summary="Draft Zion Mercer first.",
        confidence=0.8,
        rationale=["Top score in the mock pool."],
        recommendations=[
            Recommendation(
                item_id="p013",
                title="Draft Zion Mercer first",
                details="Highest heuristic score.",
                confidence=0.8,
                score=27.5,
                action_type="draft advice",
                approval_required=True,
                proposed_action="Draft Zion Mercer.",
                supporting_evidence=["heuristic score"],
            )
        ],
    )
    final = DeliveryAgent().deliver(state, result)

    assert "recommendations" in final.json_payload
    assert "# FanDraGen Result" in final.markdown_summary
    assert state.approval_status.approval_required is True
