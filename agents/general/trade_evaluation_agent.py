"""Trade evaluation worker agent."""

from __future__ import annotations

from agents.base import BaseAgent
from agents.nba.nba_player_context_helper import NBAPlayerContextHelper
from schemas.models import AgentResult, AgentTask, Recommendation, WorkflowState
from tools.player_stats_tool import PlayerStatsTool
from tools.recommendation_tool import RecommendationTool


class TradeEvaluationAgent(BaseAgent):
    """Evaluates trade proposals using local NBA stats and heuristics."""

    agent_name = "TradeEvaluationAgent"

    def __init__(self) -> None:
        self.stats_tool = PlayerStatsTool()
        self.recommendation_tool = RecommendationTool()
        self.player_helper = NBAPlayerContextHelper()

    def execute(self, task: AgentTask, state: WorkflowState) -> AgentResult:
        self._start(state, task)
        aliases = self.player_helper.resolve_aliases(state.original_user_query.text)
        give_player = aliases.get("Player A", task.input_payload.get("give_player", "Top Player Omega"))
        receive_player = aliases.get("Player B", task.input_payload.get("receive_player", "Top Player Bravo"))
        stats_result = self.stats_tool.fetch_player_stats(state, [give_player, receive_player])
        trade_result = self.recommendation_tool.evaluate_trade(state, give_player, receive_player)
        recommendation = Recommendation(**trade_result.data)
        return AgentResult(
            agent_name=self.agent_name,
            summary=trade_result.summary,
            confidence=0.76,
            rationale=recommendation.rationale,
            assumptions=recommendation.assumptions,
            recommendations=[recommendation],
            supporting_tool_results=[stats_result, trade_result],
            structured_payload={"trade_evaluation": trade_result.data},
        )
