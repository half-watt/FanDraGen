"""Tool-layer tests."""

from __future__ import annotations

from schemas.models import UserQuery, WorkflowState
from tools.league_data_tool import LeagueDataTool
from tools.recommendation_tool import RecommendationTool
from utils.file_utils import league_data_path
from utils.nba_data_source import get_free_agent_rows, load_players_table


def _state() -> WorkflowState:
    return WorkflowState(original_user_query=UserQuery(text="test"))


def test_league_data_tool_fetches_rosters() -> None:
    state = _state()
    result = LeagueDataTool().fetch_rosters(state)
    assert len(result.data) >= 5
    assert result.summary == "Loaded roster assignments."


def test_recommendation_tool_ranks_waiver_pool_deterministically() -> None:
    state = _state()
    players = {r["player_id"]: r for r in load_players_table(league_data_path())}
    fa_ids = [r["player_id"] for r in get_free_agent_rows(league_data_path())][:4]
    top_id = max(fa_ids, key=lambda pid: float(players[pid]["projected_points"]))
    result = RecommendationTool().rank_players(state, player_ids=fa_ids)
    assert result.data[0]["player_id"] == top_id
