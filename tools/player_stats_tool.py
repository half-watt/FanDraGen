"""Player stats tool: NBA stats CSV plus optional ESPN and nba_api enrichment."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from integrations import espn_nba
from integrations.nba_api_stats import merge_demo_rows_with_nba
from schemas.models import ToolResult, WorkflowState
from tools.base import BaseTool
from utils.env import live_espn_enabled
from utils.file_utils import league_data_path
from utils.nba_data_source import data_source_label, load_players_table


class PlayerStatsTool(BaseTool):
    """Reads player stats from the NBA stats CSV; optionally attaches live NBA market context."""

    tool_name = "PlayerStatsTool"

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or league_data_path()

    def _load_players(self) -> list[dict[str, str]]:
        return load_players_table(self.data_dir)

    def _filter(self, player_names: Iterable[str] | None = None) -> list[dict[str, str]]:
        rows = self._load_players()
        if not player_names:
            return rows
        wanted = {name.lower() for name in player_names}
        return [row for row in rows if row["player_name"].lower() in wanted]

    def _merge_nba(self, rows: list[dict[str, str]], state: WorkflowState) -> list[dict[str, Any]]:
        return merge_demo_rows_with_nba(rows, state, self.data_dir)

    def _maybe_live_enrichment(self, state: WorkflowState) -> tuple[dict[str, Any] | None, bool]:
        if not live_espn_enabled():
            return None, False
        standings = espn_nba.fetch_nba_standings_snapshot(max_teams=6)
        if not standings.get("ok"):
            state.add_fallback("live_espn_standings_unavailable")
            return {"live_espn": standings, "note": "Live ESPN standings request failed; stat rows unchanged."}, True
        return {"live_espn": standings, "note": "Live ESPN standings snapshot for late-season context."}, False

    def fetch_player_stats(self, state: WorkflowState, player_names: list[str] | None = None) -> ToolResult:
        rows = self._filter(player_names)
        rows = self._merge_nba(rows, state)
        enrichment, live_fb = self._maybe_live_enrichment(state)
        row_missing = not bool(rows) and bool(player_names)
        nba_note = ""
        if any(isinstance(r, dict) and r.get("nba_source") for r in rows):
            nba_note = " Includes merged nba_api PlayerGameLog fields when FANDRAGEN_NBA_API=1."
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="fetch_player_stats",
            data=rows,
            supporting_points=[
                f"Retrieved base stat rows for {len(rows)} players ({data_source_label()}).{nba_note}"
            ]
            + ([enrichment["note"]] if enrichment else []),
            summary="Loaded player stat rows.",
            fallback_used=row_missing,
            enrichment=enrichment,
        )
        status: str = "fallback" if (row_missing or live_fb) else "success"
        return self._record(state, "fetch_player_stats", {"player_names": player_names or []}, result, status=status)

    def fetch_recent_form(self, state: WorkflowState, player_names: list[str] | None = None) -> ToolResult:
        rows = self._filter(player_names)
        rows = self._merge_nba(rows, state)
        enrichment, live_fb = self._maybe_live_enrichment(state)
        out = []
        for row in rows:
            item = {
                "player_name": row["player_name"],
                "recent_points_avg": float(row.get("effective_recent_points_avg") or row["recent_points_avg"]),
                "status": row["status"],
            }
            for k in ("nba_pts_last10_avg", "nba_mapped_full_name", "nba_source"):
                if k in row:
                    item[k] = row[k]
            out.append(item)
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="fetch_recent_form",
            data=out,
            supporting_points=["Recent form blends table recent_points_avg with nba_api last-10 PTS when enabled."]
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
        base = self._filter(player_names)
        merged = self._merge_nba(base, state)
        rows = []
        for row in merged:
            entry = {
                "player_name": row["player_name"],
                "projected_points": float(row.get("effective_projected_points") or row["projected_points"]),
                "matchup_difficulty": int(row["matchup_difficulty"]),
                "injury_flag": int(row["injury_flag"]),
                "status": row["status"],
            }
            for k in ("nba_pts_last10_avg", "nba_mapped_full_name", "nba_source"):
                if k in row:
                    entry[k] = row[k]
            rows.append(entry)
        enrichment, live_fb = self._maybe_live_enrichment(state)
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="fetch_projections",
            data=rows,
            supporting_points=["Projection row blends table data with nba_api when FANDRAGEN_NBA_API=1."]
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
