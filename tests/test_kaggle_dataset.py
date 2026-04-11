"""NBA stats CSV data source (tests use ``tests/fixtures/kaggle_minimal.csv`` via conftest)."""

from __future__ import annotations

from utils.file_utils import league_data_path
from utils.nba_data_source import get_roster_rows, load_players_table


def test_kaggle_load_orders_best_player_first() -> None:
    rows = load_players_table(league_data_path())
    assert len(rows) >= 30
    assert rows[0]["player_id"] == "kg_00001"
    assert rows[0]["player_name"] == "Top Player Omega"
    assert rows[0].get("kaggle_nba_person_id") == "203507"


def test_kaggle_rosters_map_top_players_to_template_slots() -> None:
    roster = get_roster_rows(league_data_path())
    assert len(roster) == 24
    assert roster[0]["fantasy_team_id"] == "team_001"
    assert roster[0]["roster_slot"] == "PG"
    players = {r["player_id"]: r for r in load_players_table(league_data_path())}
    assert players[roster[0]["player_id"]]["player_name"] == "Top Player Omega"
