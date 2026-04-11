"""Helpers for producing high-signal trace artifacts for demos."""

from __future__ import annotations

from typing import Any

from schemas.models import WorkflowState


def add_trace_metadata(state: WorkflowState, **metadata: Any) -> None:
    """Merge additional trace metadata into shared state."""

    state.trace_metadata.update(metadata)


def build_trace_snapshot(state: WorkflowState) -> dict[str, Any]:
    """Create a compact trace payload for printing or tests."""

    return {
        "route": state.route_decision.model_dump() if state.route_decision else None,
        "agents": state.invoked_agents,
        "tool_calls": [record.model_dump(mode="json") for record in state.tool_call_history],
        "fallback_flags": state.fallback_flags,
        "revision_count": state.revision_count,
        "approval_status": state.approval_status.model_dump(),
        "metrics": state.metrics,
    }
