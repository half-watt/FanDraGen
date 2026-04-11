"""Player stats tool for deterministic demo data."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from schemas.models import ToolResult, WorkflowState
from tools.base import BaseTool
from utils.file_utils import demo_path, read_csv


class PlayerStatsTool(BaseTool):
    """Reads player stats, recent form, and projection slices from players.csv."""

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

    def fetch_player_stats(self, state: WorkflowState, player_names: list[str] | None = None) -> ToolResult:
        rows = self._filter(player_names)
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="fetch_player_stats",
            data=rows,
            supporting_points=[f"Retrieved base stat rows for {len(rows)} players."],
            summary="Loaded player stat rows.",
            fallback_used=not bool(rows) and bool(player_names),
        )
        return self._record(state, "fetch_player_stats", {"player_names": player_names or []}, result, status="fallback" if result.fallback_used else "success")

    def fetch_recent_form(self, state: WorkflowState, player_names: list[str] | None = None) -> ToolResult:
        rows = [
            {"player_name": row["player_name"], "recent_points_avg": float(row["recent_points_avg"]), "status": row["status"]}
            for row in self._filter(player_names)
        ]
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="fetch_recent_form",
            data=rows,
            supporting_points=["Recent form uses recent_points_avg from the demo player table."],
            summary="Loaded recent form.",
        )
        return self._record(state, "fetch_recent_form", {"player_names": player_names or []}, result)

    def fetch_projections(self, state: WorkflowState, player_names: list[str] | None = None) -> ToolResult:
        rows = [
            {
                "player_name": row["player_name"],
                "projected_points": float(row["projected_points"]),
                "matchup_difficulty": int(row["matchup_difficulty"]),
                "injury_flag": int(row["injury_flag"]),
            }
            for row in self._filter(player_names)
        ]
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="fetch_projections",
            data=rows,
            supporting_points=["Projection data comes from the deterministic players.csv dataset."],
            summary="Loaded projections.",
        )
        return self._record(state, "fetch_projections", {"player_names": player_names or []}, result)
