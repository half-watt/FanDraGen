"""League rules helper tool."""

from __future__ import annotations

from pathlib import Path

from schemas.models import ToolResult, WorkflowState
from tools.base import BaseTool
from utils.file_utils import demo_path, read_json


class RulesTool(BaseTool):
    """Reads league rules and presents readable summaries."""

    tool_name = "RulesTool"

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or demo_path()

    def fetch_league_rules(self, state: WorkflowState) -> ToolResult:
        payload = read_json(self.data_dir / "league_rules.json")
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="fetch_league_rules",
            data=payload,
            supporting_points=["League rules loaded from local league_rules.json."],
            summary="Loaded raw league rules.",
        )
        return self._record(state, "fetch_league_rules", {}, result)

    def explain_scoring_format(self, state: WorkflowState) -> ToolResult:
        payload = read_json(self.data_dir / "league_rules.json")
        scoring = payload["scoring_settings"]
        explanation = (
            f"This league awards {scoring['points']} point per point scored, "
            f"{scoring['rebounds']} per rebound, {scoring['assists']} per assist, "
            f"and penalizes turnovers by {abs(scoring['turnovers'])}."
        )
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="explain_scoring_format",
            data={"explanation": explanation},
            supporting_points=[explanation],
            summary="Explained scoring format.",
        )
        return self._record(state, "explain_scoring_format", {}, result)
