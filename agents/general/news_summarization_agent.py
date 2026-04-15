"""Roster news summarization worker."""

from __future__ import annotations

from agents.base import BaseAgent
from agents.nba.nba_player_context_helper import NBAPlayerContextHelper
from schemas.models import AgentResult, AgentTask, WorkflowState
from tools.league_data_tool import LeagueDataTool
from tools.news_tool import NewsTool
from utils.file_utils import league_data_path
from utils.nba_data_source import load_players_table


class NewsSummarizationAgent(BaseAgent):
    """Summarizes important news for the user's roster."""

    agent_name = "NewsSummarizationAgent"

    def __init__(self) -> None:
        self.league_data_tool = LeagueDataTool()
        self.news_tool = NewsTool()
        self.player_helper = NBAPlayerContextHelper()

    def execute(self, task: AgentTask, state: WorkflowState) -> AgentResult:
        self._start(state, task)
        rosters = self.league_data_tool.fetch_rosters(state)
        roster_rows = [row for row in rosters.data if row["fantasy_team_id"] == "team_001"]
        state.intermediate_outputs["roster_rows"] = roster_rows
        player_rows = load_players_table(league_data_path())
        players_by_id = {row["player_id"]: row for row in player_rows}
        state.intermediate_outputs["players_by_id"] = players_by_id
        roster_names = self.player_helper.roster_player_names(state)
        player_news = self.news_tool.fetch_player_news(state, roster_names)
        summary = "Summarized the most relevant player news for the current roster."
        rationale = [
            f"{item['player_name']}: {item.get('headline') or item.get('narrative') or 'No detail available.'}"
            for item in player_news.data
        ]
        return AgentResult(
            agent_name=self.agent_name,
            summary=summary,
            confidence=0.86,
            rationale=rationale,
            assumptions=["Only roster-related news from the local news feed is included."],
            supporting_tool_results=[rosters, player_news],
            structured_payload={"player_news": player_news.data},
        )
