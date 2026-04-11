"""Roster management agent for lineup and waiver requests."""

from __future__ import annotations

from agents.base import BaseAgent
from agents.nba.nba_matchup_interpreter import NBAMatchupInterpreter
from schemas.models import AgentResult, AgentTask, Recommendation, WorkflowState
from tools.league_data_tool import LeagueDataTool
from tools.player_stats_tool import PlayerStatsTool
from tools.recommendation_tool import RecommendationTool


class ManagingAgent(BaseAgent):
    """Handles lineup optimization, waivers, and fallback explanation requests."""

    agent_name = "ManagingAgent"

    def __init__(self) -> None:
        self.league_data_tool = LeagueDataTool()
        self.stats_tool = PlayerStatsTool()
        self.recommendation_tool = RecommendationTool()
        self.matchup_helper = NBAMatchupInterpreter()

    def execute(self, task: AgentTask, state: WorkflowState) -> AgentResult:
        self._start(state, task)
        if task.task_type == "waiver/free agent pickup":
            free_agents = self.league_data_tool.fetch_free_agents(state)
            pickup = self.recommendation_tool.recommend_waiver_pickup(
                state,
                [row["player_id"] for row in free_agents.data],
            )
            recommendation = Recommendation(**pickup.data)
            return AgentResult(
                agent_name=self.agent_name,
                summary=pickup.summary,
                confidence=0.81,
                rationale=recommendation.rationale,
                assumptions=recommendation.assumptions,
                recommendations=[recommendation],
                supporting_tool_results=[free_agents, pickup],
                structured_payload={"waiver_pickup": pickup.data},
            )

        if task.task_type == "missing data / fallback explanation":
            if not state.fallback_flags:
                state.add_fallback("missing_projection_source_local_mode")
            summary = "Explained the assumptions FanDraGen makes when local data is missing or incomplete."
            rationale = [
                "The system uses the local NBA stats CSV and league files and does not invent external data sources.",
                "When a file or field is missing, the workflow surfaces a fallback flag and uses the best available local evidence.",
            ]
            return AgentResult(
                agent_name=self.agent_name,
                summary=summary,
                confidence=0.79,
                rationale=rationale,
                assumptions=state.fallback_flags,
                structured_payload={"fallback_flags": state.fallback_flags},
            )

        roster_result = self.league_data_tool.fetch_rosters(state)
        roster_rows = [row for row in roster_result.data if row["fantasy_team_id"] == "team_001"]
        state.intermediate_outputs["roster_rows"] = roster_rows
        lineup_result = self.recommendation_tool.suggest_lineup(state, roster_rows)
        starters = lineup_result.data["starters"]
        starter_names = [item["player_name"] for item in starters]
        form_result = self.stats_tool.fetch_recent_form(state, starter_names)
        recommendation = Recommendation(
            item_id="lineup-week-18",
            title="Start the highest-scoring five rostered players",
            details=(
                f"Recommended starters: {', '.join(starter_names)}. "
                f"Late-season context: prioritize healthy bodies, favorable matchups, and minutes stability "
                f"before the fantasy playoff bracket."
            ),
            confidence=0.82,
            score=float(starters[0]["heuristic_score"]),
            action_type="lineup optimization",
            approval_required=True,
            proposed_action=f"Set starters to {', '.join(starter_names)}.",
            rationale=[
                (
                    f"{item['player_name']}: {self.matchup_helper.explain_difficulty(int(item['matchup_difficulty']))} "
                    f"(difficulty {item['matchup_difficulty']}/5), status={item.get('status', 'unknown')}, "
                    f"heuristic={item['heuristic_score']}"
                )
                for item in starters
            ],
            assumptions=[
                "Lineup advice assumes one scoring period aligned with the demo calendar window.",
                "Injury or rest news after lock is not modeled beyond the local news feed.",
            ],
            supporting_evidence=[
                "LeagueDataTool.fetch_rosters",
                "RecommendationTool.suggest_lineup",
                "PlayerStatsTool.fetch_recent_form",
            ],
        )
        return AgentResult(
            agent_name=self.agent_name,
            summary="Built a lineup recommendation for the current scoring period.",
            confidence=0.82,
            rationale=recommendation.rationale,
            assumptions=recommendation.assumptions,
            recommendations=[recommendation],
            supporting_tool_results=[roster_result, lineup_result, form_result],
            structured_payload=lineup_result.data,
        )
