"""Structured logging helpers for workflow tracing."""

from __future__ import annotations

from typing import Any

from schemas.models import WorkflowState, LogEvent


def log_event(
    state: WorkflowState,
    event_type: str,
    agent: str,
    tool: str,
    status: str,
    message: str,
    details: dict[str, Any] = None,
) -> None:
    """Append a structured LogEvent to workflow state."""
    log = LogEvent(
        event_type=event_type,
        agent=agent,
        tool=tool,
        status=status,
        message=message,
        details=details or {},
    )
    state.log(log)


def summarize_logs(state: WorkflowState) -> str:
    """Create a concise, human-readable trace summary."""

    lines = ["Trace Summary"]
    for entry in state.logs:
        lines.append(f"- {entry.event_type}: {entry.details}")
    return "\n".join(lines)
