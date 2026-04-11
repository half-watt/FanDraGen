"""Delivery agent that formats the final response."""

from __future__ import annotations

from schemas.models import AgentResult, ApprovalStatus, FinalResponse, WorkflowState
from utils.logging_utils import log_event
from utils.trace_utils import build_trace_snapshot


class DeliveryAgent:
    """Produces the final JSON payload and readable markdown summary."""

    def deliver(self, state: WorkflowState, result: AgentResult) -> FinalResponse:
        approval_required = any(item.approval_required for item in result.recommendations)
        proposed_action = result.recommendations[0].proposed_action if result.recommendations else None
        state.approval_status = ApprovalStatus(
            approval_required=approval_required,
            approved=None,
            proposed_action=proposed_action,
            action_not_executed=True,
            checkpoint_reason="Recommendation-style output requires simulated human approval." if approval_required else "No approval required.",
        )
        if approval_required:
            log_event(state, "approval_checkpoint", proposed_action=proposed_action)

        json_payload = {
            "query": state.original_user_query.model_dump(mode="json"),
            "route": state.route_decision.model_dump() if state.route_decision else None,
            "recommendations": [item.model_dump() for item in result.recommendations],
            "summary": result.summary,
            "rationale": result.rationale,
            "assumptions": result.assumptions,
            "confidence": result.confidence,
            "fallback_demo_data_usage": {
                "using_demo_data": True,
                "fallback_flags": state.fallback_flags,
                "live_espn_enrichment_enabled": bool(state.trace_metadata.get("live_espn_enrichment_enabled")),
                "nba_api_enrichment_enabled": bool(state.trace_metadata.get("nba_api_enrichment_enabled")),
                "gemini_configured": bool(state.trace_metadata.get("gemini_configured")),
                "gemini_enrichment_applied": bool(state.trace_metadata.get("gemini_enrichment_applied")),
            },
            "approval_status": state.approval_status.model_dump(),
            "trace": build_trace_snapshot(state),
        }
        markdown_summary = "\n".join(
            [
                "# FanDraGen Result",
                f"**Recommendation:** {result.recommendations[0].title if result.recommendations else result.summary}",
                f"**Rationale:** {'; '.join(result.rationale) if result.rationale else 'No rationale available.'}",
                f"**Assumptions:** {'; '.join(result.assumptions) if result.assumptions else 'No special assumptions.'}",
                f"**Confidence:** {result.confidence:.2f}",
                f"**Fallback/demo-data usage:** Demo mode active; flags={state.fallback_flags or ['none']}",
                f"**Approval required:** {state.approval_status.approval_required}",
                f"**Proposed action:** {state.approval_status.proposed_action or 'None'}",
                "**Action execution:** No real account action is performed in this prototype.",
            ]
        )
        final = FinalResponse(json_payload=json_payload, markdown_summary=markdown_summary)
        state.final_delivery_payload = final
        log_event(state, "delivery_complete", approval_required=approval_required)
        return final
