"""Drafting agent for ranking and pick recommendations."""

from __future__ import annotations

from agents.base import BaseAgent
from agents.nba.nba_matchup_interpreter import NBAMatchupInterpreter
from schemas.models import AgentResult, AgentTask, Recommendation, WorkflowState
from tools.league_data_tool import LeagueDataTool
from tools.player_stats_tool import PlayerStatsTool
from tools.recommendation_tool import RecommendationTool


class DraftingAgent(BaseAgent):
    """Recommends draft rankings and explains the ordering."""

    agent_name = "DraftingAgent"

    def __init__(self) -> None:
        self.league_data_tool = LeagueDataTool()
        self.stats_tool = PlayerStatsTool()
        self.recommendation_tool = RecommendationTool()
        self.matchup_helper = NBAMatchupInterpreter()

    def execute(self, task: AgentTask, state: WorkflowState) -> AgentResult:
        self._start(state, task)
        free_agents = self.league_data_tool.fetch_free_agents(state)
        player_ids = [row["player_id"] for row in free_agents.data]
        ranking_result = self.recommendation_tool.rank_players(state, player_ids=player_ids)
        top_three = ranking_result.data[:3]
        if task.task_type == "explanation / why reasoning":
            recommendations = []
            summary = "Explained the player ranking using the demo heuristic engine."
        else:
            pick_result = self.recommendation_tool.recommend_draft_pick(state, player_ids)
            recommendations = [Recommendation(**pick_result.data)]
            summary = pick_result.summary

        rationale = [
            f"{row['player_name']} scored {row['heuristic_score']} with a {self.matchup_helper.explain_difficulty(int(row['matchup_difficulty']))}."
            for row in top_three
        ]
        stats_result = self.stats_tool.fetch_projections(state, [row["player_name"] for row in top_three])
        return AgentResult(
            agent_name=self.agent_name,
            summary=summary,
            confidence=0.84,
            rationale=rationale,
            assumptions=["Draft advice assumes the currently mocked free-agent pool is the available draft pool."],
            recommendations=recommendations,
            supporting_tool_results=[ranking_result, stats_result],
            structured_payload={"ranked_players": ranking_result.data[:5]},
        )
