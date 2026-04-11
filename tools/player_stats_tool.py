"""Player stats tool: demo CSV plus optional live ESPN enrichment."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from integrations import espn_nba
from schemas.models import ToolResult, WorkflowState
from tools.base import BaseTool
from utils.env import live_espn_enabled
from utils.file_utils import demo_path, read_csv


class PlayerStatsTool(BaseTool):
    """Reads player stats from demo CSV; optionally attaches live NBA market context."""

    tool_name = "PlayerStatsTool"

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or demo_path()

    def _load_players(self) -> list[dict[str, str]]:
        return read_csv(self.data_dir / "players.csv")

    def _filter(self, player_names: Iterable[str] | None = None) -> list[dict[str, str]]:
        rows = self._load_players()
        if not player_names:
            return rows
        wanted = {name.lower() for name in player_names}
        return [row for row in rows if row["player_name"].lower() in wanted]

    def _maybe_live_enrichment(self, state: WorkflowState) -> tuple[dict[str, Any] | None, bool]:
        if not live_espn_enabled():
            return None, False
        standings = espn_nba.fetch_nba_standings_snapshot(max_teams=6)
        if not standings.get("ok"):
            state.add_fallback("live_espn_standings_unavailable")
            return {"live_espn": standings, "note": "Live ESPN standings request failed; demo rows unchanged."}, True
        return {"live_espn": standings, "note": "Live ESPN standings snapshot for late-season context."}, False

    def fetch_player_stats(self, state: WorkflowState, player_names: list[str] | None = None) -> ToolResult:
        rows = self._filter(player_names)
        enrichment, live_fb = self._maybe_live_enrichment(state)
        row_missing = not bool(rows) and bool(player_names)
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="fetch_player_stats",
            data=rows,
            supporting_points=[f"Retrieved base stat rows for {len(rows)} players."]
            + ([enrichment["note"]] if enrichment else []),
            summary="Loaded player stat rows.",
            fallback_used=row_missing,
            enrichment=enrichment,
        )
        status: str = "fallback" if (row_missing or live_fb) else "success"
        return self._record(state, "fetch_player_stats", {"player_names": player_names or []}, result, status=status)

    def fetch_recent_form(self, state: WorkflowState, player_names: list[str] | None = None) -> ToolResult:
        rows = [
            {"player_name": row["player_name"], "recent_points_avg": float(row["recent_points_avg"]), "status": row["status"]}
            for row in self._filter(player_names)
        ]
        enrichment, live_fb = self._maybe_live_enrichment(state)
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="fetch_recent_form",
            data=rows,
            supporting_points=["Recent form uses recent_points_avg from the demo player table."]
            + ([enrichment["note"]] if enrichment else []),
            summary="Loaded recent form.",
            enrichment=enrichment,
            fallback_used=False,
        )
        return self._record(
            state,
            "fetch_recent_form",
            {"player_names": player_names or []},
            result,
            status="fallback" if live_fb else "success",
        )

    def fetch_projections(self, state: WorkflowState, player_names: list[str] | None = None) -> ToolResult:
        rows = [
            {
                "player_name": row["player_name"],
                "projected_points": float(row["projected_points"]),
                "matchup_difficulty": int(row["matchup_difficulty"]),
                "injury_flag": int(row["injury_flag"]),
                "status": row["status"],
            }
            for row in self._filter(player_names)
        ]
        enrichment, live_fb = self._maybe_live_enrichment(state)
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="fetch_projections",
            data=rows,
            supporting_points=["Projection data comes from the deterministic players.csv dataset."]
            + ([enrichment["note"]] if enrichment else []),
            summary="Loaded projections.",
            enrichment=enrichment,
            fallback_used=False,
        )
        return self._record(
            state,
            "fetch_projections",
            {"player_names": player_names or []},
            result,
            status="fallback" if live_fb else "success",
        )
