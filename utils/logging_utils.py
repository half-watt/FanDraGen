"""Structured logging helpers for workflow tracing."""

from __future__ import annotations

from typing import Any

from schemas.models import WorkflowState


def log_event(state: WorkflowState, event: str, **details: Any) -> None:
    """Append a normalized log event to workflow state."""

    state.log(event, details)


def summarize_logs(state: WorkflowState) -> str:
    """Create a concise, human-readable trace summary."""

    lines = ["Trace Summary"]
    for entry in state.logs:
        lines.append(f"- {entry['event']}: {entry['details']}")
    return "\n".join(lines)
