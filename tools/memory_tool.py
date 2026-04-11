"""Lightweight local memory tool for demo preferences and artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from schemas.models import ToolResult, WorkflowState
from tools.base import BaseTool
from utils.file_utils import demo_path, read_json, write_json


class MemoryTool(BaseTool):
    """Stores user preferences and session artifacts in a local JSON file."""

    tool_name = "MemoryTool"

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or demo_path()
        self.memory_path = self.data_dir / "user_memory.json"

    def _load(self) -> dict[str, Any]:
        return read_json(self.memory_path)

    def store_user_preferences(self, state: WorkflowState, preferences: dict[str, Any]) -> ToolResult:
        payload = self._load()
        payload.setdefault("preferences", {}).update(preferences)
        write_json(self.memory_path, payload)
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="store_user_preferences",
            data=payload,
            supporting_points=["Stored demo preferences locally."],
            summary="Stored user preferences.",
        )
        return self._record(state, "store_user_preferences", {"preferences": preferences}, result)

    def load_user_preferences(self, state: WorkflowState) -> ToolResult:
        payload = self._load().get("preferences", {})
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="load_user_preferences",
            data=payload,
            supporting_points=["Loaded demo preferences from local memory."],
            summary="Loaded user preferences.",
        )
        return self._record(state, "load_user_preferences", {}, result)

    def store_session_artifacts(self, state: WorkflowState, artifact_name: str, artifact: dict[str, Any]) -> ToolResult:
        payload = self._load()
        payload.setdefault("session_artifacts", {})[artifact_name] = artifact
        write_json(self.memory_path, payload)
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="store_session_artifacts",
            data={artifact_name: artifact},
            supporting_points=[f"Stored session artifact '{artifact_name}'."],
            summary=f"Stored session artifact {artifact_name}.",
        )
        return self._record(state, "store_session_artifacts", {"artifact_name": artifact_name}, result)