"""nba_api merge behavior (mocked HTTP)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from schemas.models import UserQuery, WorkflowState
from utils.file_utils import demo_path


@pytest.fixture
def enable_nba_api(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FANDRAGEN_NBA_API", "1")
    from utils import env as env_mod

    env_mod._flags.cache_clear()


def test_merge_attaches_nba_fields_when_enabled(enable_nba_api: object) -> None:
    from integrations import nba_api_stats

    fake = {
        "nba_source": "nba_api.playergamelog",
        "nba_season": "2024-25",
        "nba_player_id": 1629029,
        "nba_games_in_log": 5,
        "nba_pts_last10_avg": 28.0,
        "nba_reb_last10_avg": 7.0,
        "nba_ast_last10_avg": 8.0,
        "nba_pts_season_avg": 27.0,
        "nba_reb_season_avg": 7.0,
        "nba_ast_season_avg": 8.0,
    }
    with patch.object(nba_api_stats, "_fetch_playergamelog_snapshot", return_value=fake):
        nba_api_stats.clear_nba_cache_for_tests()
        state = WorkflowState(original_user_query=UserQuery(text="test"))
        rows = [{"player_id": "p001", "player_name": "Luka Vance", "projected_points": "40", "recent_points_avg": "38"}]
        out = nba_api_stats.merge_demo_rows_with_nba(rows, state, demo_path())
    assert out[0].get("nba_pts_last10_avg") == 28.0
    assert "effective_projected_points" in out[0]


def test_merge_noop_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FANDRAGEN_NBA_API", raising=False)
    from utils import env as env_mod

    env_mod._flags.cache_clear()
    from integrations import nba_api_stats

    nba_api_stats.clear_nba_cache_for_tests()
    state = WorkflowState(original_user_query=UserQuery(text="test"))
    rows = [{"player_id": "p001", "player_name": "Luka Vance", "projected_points": "40", "recent_points_avg": "38"}]
    out = nba_api_stats.merge_demo_rows_with_nba(rows, state, demo_path())
    assert len(out) == 1
    assert "nba_source" not in out[0]
