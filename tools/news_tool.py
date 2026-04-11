"""Player and team news: demo JSON plus optional live ESPN headlines."""

from __future__ import annotations

from pathlib import Path

from integrations import espn_nba
from schemas.models import ToolResult, WorkflowState
from tools.base import BaseTool
from utils.env import live_espn_enabled
from utils.file_utils import demo_path, read_json


class NewsTool(BaseTool):
    """Reads player and team news from a local JSON file; may merge live ESPN headlines."""

    tool_name = "NewsTool"

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or demo_path()

    def _load_news(self) -> dict[str, list[dict[str, str]]]:
        return read_json(self.data_dir / "news.json")

    def _live_headlines_enrichment(self, state: WorkflowState) -> tuple[dict | None, bool]:
        if not live_espn_enabled():
            return None, False
        snap = espn_nba.fetch_nba_news_headlines(limit=5)
        if not snap.get("ok"):
            state.add_fallback("live_espn_news_unavailable")
            return {"espn_live_headlines": snap, "note": "Live ESPN headlines unavailable."}, True
        return {"espn_live_headlines": snap, "note": "Supplemented with live ESPN NBA headlines (public JSON)."}, False

    def fetch_player_news(self, state: WorkflowState, player_names: list[str] | None = None) -> ToolResult:
        payload = self._load_news()
        news = payload["player_news"]
        if player_names:
            wanted = {name.lower() for name in player_names}
            news = [item for item in news if item["player_name"].lower() in wanted]
        enrichment, live_fb = self._live_headlines_enrichment(state)
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="fetch_player_news",
            data=news,
            supporting_points=[f"Found {len(news)} player news items in demo mode."]
            + ([enrichment["note"]] if enrichment else []),
            summary="Loaded player news.",
            enrichment=enrichment,
            fallback_used=not bool(news) and bool(player_names),
        )
        return self._record(
            state,
            "fetch_player_news",
            {"player_names": player_names or []},
            result,
            status="fallback" if (live_fb or result.fallback_used) else "success",
        )

    def fetch_team_news(self, state: WorkflowState, team_names: list[str] | None = None) -> ToolResult:
        payload = self._load_news()
        news = payload["team_news"]
        if team_names:
            wanted = {name.lower() for name in team_names}
            news = [item for item in news if item["team"].lower() in wanted]
        enrichment, live_fb = self._live_headlines_enrichment(state)
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="fetch_team_news",
            data=news,
            supporting_points=[f"Found {len(news)} team news items in demo mode."]
            + ([enrichment["note"]] if enrichment else []),
            summary="Loaded team news.",
            enrichment=enrichment,
            fallback_used=not bool(news) and bool(team_names),
        )
        return self._record(
            state,
            "fetch_team_news",
            {"team_names": team_names or []},
            result,
            status="fallback" if (live_fb or result.fallback_used) else "success",
        )
