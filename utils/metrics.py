"""Traditional metrics helpers for demo evaluation.

The goal here is not to create a benchmark suite. Instead, these helpers expose
simple counters and ratios that make the system behavior inspectable during a
classroom demo.
"""

from __future__ import annotations

from schemas.models import WorkflowState


def update_metrics(state: WorkflowState) -> None:
    """Populate lightweight metrics based on workflow artifacts."""

    tool_calls = len(state.tool_call_history)
    fallback_calls = sum(1 for call in state.tool_call_history if call.fallback_used)
    rejections = sum(1 for result in state.evaluator_results if not result.passed)
    approvals = 1 if state.approval_status.approval_required else 0
    grounded = 1 if any(call.status == "success" for call in state.tool_call_history) else 0

    state.metrics = {
        "task_completion_rate": 1.0 if state.final_delivery_payload else 0.0,
        "routing_accuracy": 1.0 if state.route_decision and state.route_decision.route_target == "NBABossAgent" else 0.0,
        "tool_invocation_correctness": 1.0 if tool_calls > 0 else 0.0,
        "evaluator_rejection_rate": rejections / max(len(state.evaluator_results), 1),
        "revision_success_rate": 1.0 if state.revision_count <= 1 else 0.0,
        "response_grounding_coverage": float(grounded),
        "deterministic_consistency": 1.0,
        "fallback_event_count": fallback_calls,
        "approval_checkpoint_count": approvals,
    }
