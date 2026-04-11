"""Mocked league-data tool backed by local demo files."""

from __future__ import annotations

from pathlib import Path

from schemas.models import LeagueContext, ToolResult, WorkflowState
from tools.base import BaseTool
from utils.file_utils import demo_path, missing_fields, read_csv, read_json


class LeagueDataTool(BaseTool):
    """Loads rosters, free agents, matchups, standings, and scoring rules."""

    tool_name = "LeagueDataTool"

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or demo_path()

    def fetch_rosters(self, state: WorkflowState) -> ToolResult:
        rows = read_csv(self.data_dir / "rosters.csv")
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="fetch_rosters",
            data=rows,
            supporting_points=[f"Loaded {len(rows)} roster assignments from demo data."],
            summary="Loaded roster assignments.",
            missing_fields=missing_fields(rows, ["fantasy_team_id", "player_id", "roster_slot"]),
        )
        return self._record(state, "fetch_rosters", {}, result)

    def fetch_free_agents(self, state: WorkflowState) -> ToolResult:
        rows = read_csv(self.data_dir / "free_agents.csv")
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="fetch_free_agents",
            data=rows,
            supporting_points=[f"Loaded {len(rows)} free-agent ids from demo data."],
            summary="Loaded free-agent pool.",
            missing_fields=missing_fields(rows, ["player_id"]),
        )
        return self._record(state, "fetch_free_agents", {}, result)

    def fetch_matchups(self, state: WorkflowState) -> ToolResult:
        rows = read_csv(self.data_dir / "matchups.csv")
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="fetch_matchups",
            data=rows,
            supporting_points=[f"Loaded matchup rows for week {rows[0]['week']}."] if rows else [],
            summary="Loaded matchup context.",
        )
        return self._record(state, "fetch_matchups", {}, result)

    def fetch_standings(self, state: WorkflowState) -> ToolResult:
        rows = read_csv(self.data_dir / "standings.csv")
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="fetch_standings",
            data=rows,
            supporting_points=["Loaded current standings snapshot."],
            summary="Loaded standings.",
        )
        return self._record(state, "fetch_standings", {}, result)

    def fetch_scoring_rules(self, state: WorkflowState) -> ToolResult:
        payload = read_json(self.data_dir / "league_rules.json")
        league_context = LeagueContext(
            league_id=payload["league_id"],
            sport=payload["sport"],
            roster_slots=payload["roster_slots"],
            scoring_settings=payload["scoring_settings"],
            trade_notes=payload["trade_notes"],
            waiver_notes=payload["waiver_notes"],
            lineup_lock_assumptions=payload["lineup_lock_assumptions"],
        )
        state.league_context = league_context
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="fetch_scoring_rules",
            data=league_context.model_dump(),
            supporting_points=["Loaded league scoring rules and roster slots."],
            summary="Loaded league rules.",
        )
        return self._record(state, "fetch_scoring_rules", {}, result)
