"""Heuristic recommendation engine.

The logic here is intentionally simple and deterministic. It is written so the
`_score_player` method can later be replaced by a learned model without forcing
the rest of the tool interface to change.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from schemas.models import Recommendation, ToolResult, WorkflowState
from tools.base import BaseTool
from utils.file_utils import demo_path, read_csv, read_json


class RecommendationTool(BaseTool):
    """Calculates player rankings, lineup suggestions, trades, and draft picks."""

    tool_name = "RecommendationTool"

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or demo_path()

    def _load_players(self) -> list[dict[str, str]]:
        return read_csv(self.data_dir / "players.csv")

    def _load_news(self) -> list[dict[str, Any]]:
        return read_json(self.data_dir / "news.json")["player_news"]

    def _news_delta(self, player_name: str) -> float:
        for item in self._load_news():
            if item["player_name"] == player_name:
                return float(item["sentiment_delta"])
        return 0.0

    def _score_player(self, row: dict[str, str], roster_need_weight: float = 0.0) -> float:
        projected = float(row["projected_points"])
        recent = float(row["recent_points_avg"])
        injury = int(row["injury_flag"])
        matchup = int(row["matchup_difficulty"])
        base_sentiment = float(row["sentiment_score"])
        news_bonus = self._news_delta(row["player_name"])
        return (
            projected * 0.50
            + recent * 0.25
            + (base_sentiment + news_bonus) * 10 * 0.10
            + (6 - matchup) * 2.5 * 0.10
            - injury * 4.5
            + roster_need_weight
        )

    def rank_players(
        self,
        state: WorkflowState,
        player_ids: list[str] | None = None,
        roster_need_by_position: dict[str, float] | None = None,
    ) -> ToolResult:
        roster_need_by_position = roster_need_by_position or {}
        rows = self._load_players()
        if player_ids:
            wanted = set(player_ids)
            rows = [row for row in rows if row["player_id"] in wanted]
        ranked = []
        for row in rows:
            score = self._score_player(row, roster_need_by_position.get(row["position"], 0.0))
            ranked.append({**row, "heuristic_score": round(score, 2)})
        ranked.sort(key=lambda row: row["heuristic_score"], reverse=True)
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="rank_players",
            data=ranked,
            supporting_points=["Ranking uses projected points, recent form, injury, matchup, and news sentiment."],
            summary=f"Ranked {len(ranked)} players using heuristic scoring.",
        )
        return self._record(state, "rank_players", {"player_ids": player_ids or []}, result)

    def recommend_draft_pick(self, state: WorkflowState, player_ids: list[str]) -> ToolResult:
        ranked = self.rank_players(state, player_ids=player_ids).data
        top = ranked[0]
        recommendation = Recommendation(
            item_id=top["player_id"],
            title=f"Draft {top['player_name']} first",
            details=f"Highest heuristic score in the available pool: {top['heuristic_score']}.",
            confidence=0.83,
            score=float(top["heuristic_score"]),
            action_type="draft advice",
            approval_required=True,
            proposed_action=f"Select {top['player_name']} with the next pick.",
            rationale=[
                f"Projected points: {top['projected_points']}",
                f"Recent average: {top['recent_points_avg']}",
                f"Matchup difficulty: {top['matchup_difficulty']}",
            ],
            assumptions=["This assumes standard head-to-head points scoring from the demo rules."],
            supporting_evidence=["Heuristic ranking from deterministic demo data."],
        )
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="recommend_draft_pick",
            data=recommendation.model_dump(),
            supporting_points=recommendation.rationale,
            summary=f"Recommended {top['player_name']} as the top draft pick.",
        )
        return self._record(state, "recommend_draft_pick", {"player_ids": player_ids}, result)

    def suggest_lineup(self, state: WorkflowState, roster_rows: list[dict[str, str]]) -> ToolResult:
        players = {row["player_id"]: row for row in self._load_players()}
        ranked = []
        for roster_row in roster_rows:
            player = players[roster_row["player_id"]]
            ranked.append(
                {
                    **roster_row,
                    "player_name": player["player_name"],
                    "position": player["position"],
                    "heuristic_score": round(self._score_player(player), 2),
                }
            )
        ranked.sort(key=lambda row: row["heuristic_score"], reverse=True)
        starters = ranked[:5]
        bench = ranked[5:]
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="suggest_lineup",
            data={"starters": starters, "bench": bench},
            supporting_points=[f"Suggested lineup promotes the top {len(starters)} rostered scores."],
            summary="Suggested an optimized lineup.",
        )
        return self._record(state, "suggest_lineup", {"roster_size": len(roster_rows)}, result)

    def evaluate_trade(self, state: WorkflowState, give_player: str, receive_player: str) -> ToolResult:
        players = {row["player_name"]: row for row in self._load_players()}
        give = players[give_player]
        receive = players[receive_player]
        give_score = self._score_player(give)
        receive_score = self._score_player(receive)
        delta = round(receive_score - give_score, 2)
        recommendation = Recommendation(
            item_id=f"trade-{give['player_id']}-{receive['player_id']}",
            title="Trade evaluation",
            details=f"Net heuristic delta: {delta} in favor of {'accepting' if delta > 0 else 'declining'} the deal.",
            confidence=0.76,
            score=delta,
            action_type="trade evaluation",
            approval_required=True,
            proposed_action=f"Trade {give_player} for {receive_player}." if delta > 0 else f"Decline the trade of {give_player} for {receive_player}.",
            rationale=[
                f"{receive_player} score: {round(receive_score, 2)}",
                f"{give_player} score: {round(give_score, 2)}",
            ],
            assumptions=["The trade is evaluated as a one-for-one points-league swap."],
            supporting_evidence=["Trade delta computed from the heuristic engine."],
        )
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="evaluate_trade",
            data=recommendation.model_dump(),
            supporting_points=recommendation.rationale,
            summary=f"Trade delta between {give_player} and {receive_player}: {delta}.",
        )
        return self._record(state, "evaluate_trade", {"give_player": give_player, "receive_player": receive_player}, result)

    def recommend_waiver_pickup(self, state: WorkflowState, player_ids: list[str]) -> ToolResult:
        ranked = self.rank_players(state, player_ids=player_ids).data
        top = ranked[0]
        recommendation = Recommendation(
            item_id=top["player_id"],
            title=f"Add {top['player_name']} from waivers",
            details=f"Best free-agent score in the demo pool: {top['heuristic_score']}.",
            confidence=0.81,
            score=float(top["heuristic_score"]),
            action_type="waiver/free agent pickup",
            approval_required=True,
            proposed_action=f"Submit a waiver claim for {top['player_name']}.",
            rationale=[
                f"Recent average: {top['recent_points_avg']}",
                f"News sentiment: {top['sentiment_score']}",
            ],
            assumptions=["Assumes waiver priority is available in mocked mode."],
            supporting_evidence=["Free-agent ranking from deterministic demo data."],
        )
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="recommend_waiver_pickup",
            data=recommendation.model_dump(),
            supporting_points=recommendation.rationale,
            summary=f"Recommended {top['player_name']} as the top waiver pickup.",
        )
        return self._record(state, "recommend_waiver_pickup", {"player_ids": player_ids}, result)
