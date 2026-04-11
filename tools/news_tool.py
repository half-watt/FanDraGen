"""Mocked player and team news tool."""

from __future__ import annotations

from pathlib import Path

from schemas.models import ToolResult, WorkflowState
from tools.base import BaseTool
from utils.file_utils import demo_path, read_json


class NewsTool(BaseTool):
    """Reads player and team news from a local JSON file."""

    tool_name = "NewsTool"

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or demo_path()

    def _load_news(self) -> dict[str, list[dict[str, str]]]:
        return read_json(self.data_dir / "news.json")

    def fetch_player_news(self, state: WorkflowState, player_names: list[str] | None = None) -> ToolResult:
        payload = self._load_news()
        news = payload["player_news"]
        if player_names:
            wanted = {name.lower() for name in player_names}
            news = [item for item in news if item["player_name"].lower() in wanted]
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="fetch_player_news",
            data=news,
            supporting_points=[f"Found {len(news)} player news items in demo mode."],
            summary="Loaded player news.",
        )
        return self._record(state, "fetch_player_news", {"player_names": player_names or []}, result)

    def fetch_team_news(self, state: WorkflowState, team_names: list[str] | None = None) -> ToolResult:
        payload = self._load_news()
        news = payload["team_news"]
        if team_names:
            wanted = {name.lower() for name in team_names}
            news = [item for item in news if item["team"].lower() in wanted]
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="fetch_team_news",
            data=news,
            supporting_points=[f"Found {len(news)} team news items in demo mode."],
            summary="Loaded team news.",
        )
        return self._record(state, "fetch_team_news", {"team_names": team_names or []}, result)
