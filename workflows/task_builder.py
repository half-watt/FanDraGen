"""Shared helpers for concise workflow task construction."""

from __future__ import annotations

from typing import Any

from schemas.models import AgentTask


def single_task(
    *,
    task_type: str,
    description: str,
    assigned_agent: str,
    requires_tools: list[str] | None = None,
    input_payload: dict[str, Any] | None = None,
) -> list[AgentTask]:
    """Return a one-item task list used by most workflows."""

    return [
        AgentTask(
            task_type=task_type,
            description=description,
            assigned_agent=assigned_agent,
            requires_tools=requires_tools or [],
            input_payload=input_payload or {},
        )
    ]