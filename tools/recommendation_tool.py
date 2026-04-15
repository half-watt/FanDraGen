"""Heuristic recommendation engine.

The logic here is intentionally simple and deterministic. It is written so the
`_score_player` method can later be replaced by a learned model without forcing
the rest of the tool interface to change.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from integrations.nba_api_stats import merge_demo_rows_with_nba
from schemas.models import Recommendation, ToolResult, WorkflowState
from tools.base import BaseTool
from utils.file_utils import league_data_path, read_json
from utils.nba_data_source import data_source_label, load_players_table


class RecommendationTool(BaseTool):
    """Calculates player rankings, lineup suggestions, trades, and draft picks."""

    tool_name = "RecommendationTool"

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or league_data_path()

    def _load_players(self, state: WorkflowState | None = None) -> list[dict[str, Any]]:
        rows = load_players_table(self.data_dir)
        if state is not None:
            return merge_demo_rows_with_nba(rows, state, self.data_dir)
        return rows

    def _load_news(self) -> list[dict[str, Any]]:
        return read_json(self.data_dir / "news.json")["player_news"]

    def _news_delta(self, player_name: str) -> float:
        for item in self._load_news():
            if item["player_name"] == player_name:
                raw = item.get("sentiment_delta", 0.0)
                try:
                    return float(raw)
                except (TypeError, ValueError):
                    return 0.0
        return 0.0

    def _status_penalty(self, row: dict[str, str]) -> float:
        """Late-season injury / rest risk from demo status column."""

        status = (row.get("status") or "healthy").lower()
        if status in {"out", "doubtful"}:
            return 12.0
        if status == "questionable":
            return 5.5
        if status == "probable":
            return 2.0
        return 0.0

    def _normalize_player_name(self, name: str) -> str:
        """Normalize player names for resilient matching across aliases and accents."""

        folded = unicodedata.normalize("NFKD", name or "")
        ascii_name = "".join(ch for ch in folded if not unicodedata.combining(ch))
        ascii_name = ascii_name.casefold()
        ascii_name = re.sub(r"[^a-z0-9]+", " ", ascii_name)
        return re.sub(r"\s+", " ", ascii_name).strip()

    def _resolve_trade_player(
        self,
        state: WorkflowState,
        players_by_name: dict[str, dict[str, Any]],
        requested_name: str,
        fallback_rank_index: int,
    ) -> dict[str, Any]:
        """Resolve a requested trade name using exact/normalized/fuzzy matching.

        Falls back to a deterministic ranked player when no name variant matches.
        """

        exact = players_by_name.get(requested_name)
        if exact is not None:
            return exact

        requested_norm = self._normalize_player_name(requested_name)
        by_norm = {self._normalize_player_name(name): row for name, row in players_by_name.items()}
        normalized_match = by_norm.get(requested_norm)
        if normalized_match is not None:
            return normalized_match

        for norm_name, row in by_norm.items():
            if requested_norm and (requested_norm in norm_name or norm_name in requested_norm):
                state.add_fallback(f"trade_name_fuzzy_match:{requested_name}")
                return row

        ranked = sorted(players_by_name.values(), key=lambda r: self._score_player(r), reverse=True)
        safe_index = max(0, min(fallback_rank_index, len(ranked) - 1))
        state.add_fallback(f"trade_name_missing:{requested_name}")
        return ranked[safe_index]

    def _score_player(self, row: dict[str, Any], roster_need_weight: float = 0.0) -> float:
        projected = float(row.get("effective_projected_points") or row["projected_points"])
        recent = float(row.get("effective_recent_points_avg") or row["recent_points_avg"])
        injury = int(row["injury_flag"])
        matchup = int(row["matchup_difficulty"])
        base_sentiment = float(row["sentiment_score"])
        news_bonus = self._news_delta(row["player_name"])
        status_penalty = self._status_penalty(row)
        return (
            projected * 0.48
            + recent * 0.24
            + (base_sentiment + news_bonus) * 10 * 0.11
            + (6 - matchup) * 2.5 * 0.09
            - injury * 4.2
            - status_penalty * 0.35
            + roster_need_weight
        )

    def rank_players(
        self,
        state: WorkflowState,
        player_ids: list[str] | None = None,
        roster_need_by_position: dict[str, float] | None = None,
    ) -> ToolResult:
        roster_need_by_position = roster_need_by_position or {}
        rows = self._load_players(state)
        if player_ids:
            wanted = set(player_ids)
            rows = [row for row in rows if row["player_id"] in wanted]
        ranked = []
        for row in rows:
            score = self._score_player(row, roster_need_by_position.get(row["position"], 0.0))
            ranked.append({**row, "heuristic_score": round(score, 2)})
        ranked.sort(key=lambda row: row["heuristic_score"], reverse=True)
        rp = "Ranking uses projected points, recent form, injury, matchup, and news."
        if any(r.get("nba_source") for r in ranked):
            rp += " Live NBA last-10 game logs (nba_api) are blended into projections when enabled."
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="rank_players",
            data=ranked,
            supporting_points=[rp],
            summary=f"Ranked {len(ranked)} players using heuristic scoring.",
            grounding=["data/nba/roster_template.csv", "data/nba/season_context.json", "RecommendationTool._score_player"]
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
            assumptions=["This assumes standard head-to-head points scoring from league_rules.json."],
            supporting_evidence=[
                "RecommendationTool.rank_players",
                "RecommendationTool.recommend_draft_pick",
                data_source_label(),
            ],
        )
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="recommend_draft_pick",
            data=recommendation.model_dump(),
            supporting_points=recommendation.rationale,
            summary=f"Recommended {top['player_name']} as the top draft pick.",
            grounding=["RecommendationTool.rank_players", "RecommendationTool._score_player", "data/nba/roster_template.csv"]
        )
        return self._record(state, "recommend_draft_pick", {"player_ids": player_ids}, result)

    def suggest_lineup(self, state: WorkflowState, roster_rows: list[dict[str, str]]) -> ToolResult:
        players = {row["player_id"]: row for row in self._load_players(state)}
        ranked = []
        for roster_row in roster_rows:
            player = players[roster_row["player_id"]]
            ranked.append(
                {
                    **roster_row,
                    "player_name": player["player_name"],
                    "position": player["position"],
                    "matchup_difficulty": int(player["matchup_difficulty"]),
                    "status": player["status"],
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
            grounding=["RecommendationTool._score_player", "data/nba/roster_template.csv"]
        )
        return self._record(state, "suggest_lineup", {"roster_size": len(roster_rows)}, result)

    def evaluate_trade(self, state: WorkflowState, give_player: str, receive_player: str) -> ToolResult:
        players = {row["player_name"]: row for row in self._load_players(state)}
        give = self._resolve_trade_player(state, players, give_player, fallback_rank_index=0)
        receive = self._resolve_trade_player(state, players, receive_player, fallback_rank_index=1)
        resolved_give = give.get("player_name", give_player)
        resolved_receive = receive.get("player_name", receive_player)
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
            proposed_action=f"Trade {resolved_give} for {resolved_receive}." if delta > 0 else f"Decline the trade of {resolved_give} for {resolved_receive}.",
            rationale=[
                f"{resolved_receive} score: {round(receive_score, 2)}",
                f"{resolved_give} score: {round(give_score, 2)}",
            ],
            assumptions=["The trade is evaluated as a one-for-one points-league swap."],
            supporting_evidence=[
                "RecommendationTool.evaluate_trade",
                "PlayerStatsTool.fetch_player_stats",
                data_source_label(),
            ],
        )
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="evaluate_trade",
            data=recommendation.model_dump(),
            supporting_points=recommendation.rationale,
            summary=f"Trade delta between {resolved_give} and {resolved_receive}: {delta}.",
            grounding=["RecommendationTool._score_player", "PlayerStatsTool.fetch_player_stats", "data/nba/roster_template.csv"]
        )
        return self._record(state, "evaluate_trade", {"give_player": give_player, "receive_player": receive_player}, result)

    def recommend_waiver_pickup(self, state: WorkflowState, player_ids: list[str]) -> ToolResult:
        ranked = self.rank_players(state, player_ids=player_ids).data
        top = ranked[0]
        recommendation = Recommendation(
            item_id=top["player_id"],
            title=f"Add {top['player_name']} from waivers",
            details=f"Best free-agent score in the current pool: {top['heuristic_score']}.",
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
            supporting_evidence=["RecommendationTool.rank_players", "RecommendationTool.recommend_waiver_pickup", "LeagueDataTool.fetch_free_agents"],
        )
        result = ToolResult(
            tool_name=self.tool_name,
            method_name="recommend_waiver_pickup",
            data=recommendation.model_dump(),
            supporting_points=recommendation.rationale,
            summary=f"Recommended {top['player_name']} as the top waiver pickup.",
            grounding=["RecommendationTool.rank_players", "LeagueDataTool.fetch_free_agents", "data/nba/free_agents_template.csv"]
        )
        return self._record(state, "recommend_waiver_pickup", {"player_ids": player_ids}, result)
