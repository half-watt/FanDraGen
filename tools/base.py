"""Base classes for FanDraGen tools."""

from __future__ import annotations

from abc import ABC
from typing import Any

from schemas.models import ToolCallRecord, ToolResult, WorkflowState
from utils.logging_utils import log_event


class BaseTool(ABC):
    """Base class that standardizes tool-call logging."""

    tool_name = "BaseTool"

    def _record(
        self,
        state: WorkflowState,
        method_name: str,
        arguments: dict[str, Any],
        result: ToolResult,
        status: str = "success",
    ) -> ToolResult:
        state.tool_call_history.append(
            ToolCallRecord(
                tool_name=self.tool_name,
                method_name=method_name,
                arguments=arguments,
                status=status,
                summary=result.summary,
                fallback_used=result.fallback_used,
            )
        )
        log_event(
            state,
            "tool_call",
            tool=self.tool_name,
            method=method_name,
            fallback=result.fallback_used,
            summary=result.summary,
        )
        return result
