"""Tool-layer tests."""

from __future__ import annotations

from schemas.models import UserQuery, WorkflowState
from tools.league_data_tool import LeagueDataTool
from tools.recommendation_tool import RecommendationTool


def _state() -> WorkflowState:
    return WorkflowState(original_user_query=UserQuery(text="test"))


def test_league_data_tool_fetches_rosters() -> None:
    state = _state()
    result = LeagueDataTool().fetch_rosters(state)
    assert len(result.data) >= 5
    assert result.summary == "Loaded roster assignments."


def test_recommendation_tool_ranks_waiver_pool_deterministically() -> None:
    state = _state()
    result = RecommendationTool().rank_players(state, player_ids=["p011", "p012", "p013", "p014"])
    assert result.data[0]["player_name"] == "Zion Mercer"
