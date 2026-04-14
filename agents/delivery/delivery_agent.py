"""Delivery agent that formats the final response."""

from __future__ import annotations

from schemas.models import AgentResult, ApprovalStatus, FinalResponse, WorkflowState
from utils.logging_utils import log_event
from utils.nba_data_source import nba_stats_csv_display_path
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
            log_event(
                state,
                event_type="approval_checkpoint",
                agent="DeliveryAgent",
                tool="N/A",
                status="info",
                message="Approval checkpoint reached.",
                details={"proposed_action": proposed_action},
            )

        json_payload = {
            "query": state.original_user_query.model_dump(mode="json"),
            "route": state.route_decision.model_dump() if state.route_decision else None,
            "recommendations": [item.model_dump() for item in result.recommendations],
            "summary": result.summary,
            "rationale": result.rationale,
            "assumptions": result.assumptions,
            "supporting_evidence": getattr(result, "supporting_evidence", []),
            "confidence": result.confidence,
            "data_source": {
                "nba_stats_csv": nba_stats_csv_display_path(),
                "league_config_dir": "data/nba",
                "using_synthetic_players": False,
                "fallback_flags": state.fallback_flags,
                "live_espn_enrichment_enabled": bool(state.trace_metadata.get("live_espn_enrichment_enabled")),
                "nba_api_enrichment_enabled": bool(state.trace_metadata.get("nba_api_enrichment_enabled")),
                "gemini_configured": bool(state.trace_metadata.get("gemini_configured")),
                "gemini_enrichment_applied": bool(state.trace_metadata.get("gemini_enrichment_applied")),
            },
            "approval_status": state.approval_status.model_dump(),
            "trace": build_trace_snapshot(state),
        }
        md_lines = [
            "# FanDraGen Result",
            "",
            "---",
        ]
        if state.trace_metadata.get("gemini_enrichment_applied"):
            md_lines.append(
                "**Gemini polish:** The summary and rationale below were rewritten for readability only. "
                "The pick, scores, and figures still come entirely from tools—not from separate LLM “decisions.”"
            )
        md_lines.extend([
            f"**Recommendation:** {result.recommendations[0].title if result.recommendations else result.summary}",
            f"**Rationale:** {'; '.join(result.rationale) if result.rationale else 'No rationale available.'}",
            f"**Assumptions:** {'; '.join(result.assumptions) if result.assumptions else 'No special assumptions.'}",
            f"**Supporting evidence:** {'; '.join(getattr(result, 'supporting_evidence', [])) if getattr(result, 'supporting_evidence', []) else 'No supporting evidence.'}",
            f"**Confidence:** {result.confidence:.2f}",
            f"**Data source:** NBA stats CSV + league templates under data/nba; flags={state.fallback_flags or ['none']}",
            f"**Approval required:** {state.approval_status.approval_required}",
            f"**Proposed action:** {state.approval_status.proposed_action or 'None'}",
            "**Action execution:** No real account action is performed in this prototype.",
        ])
        # Surface unresolved evaluator issues if present
        unresolved = [a for a in result.assumptions if a.startswith("Unresolved evaluator issues")] if hasattr(result, "assumptions") else []
        if unresolved:
            md_lines.append("")
            md_lines.append("**:warning: Unresolved evaluator issues after all allowed revisions:**")
            md_lines.extend([f"- {issue}" for issue in unresolved])
        markdown_summary = "\n".join(md_lines)
        final = FinalResponse(json_payload=json_payload, markdown_summary=markdown_summary)
        state.final_delivery_payload = final
        log_event(
            state,
            event_type="delivery_complete",
            agent="DeliveryAgent",
            tool="N/A",
            status="success",
            message="Delivery complete.",
            details={"approval_required": approval_required},
        )
        return final
