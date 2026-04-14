"""NBA player rows from a required Kaggle-format season stats CSV.

League structure (roster slots, rules, matchups) lives under ``data/nba/``.
Download: https://www.kaggle.com/datasets/eduardopalmieri/nba-player-stats-season-2425

Default file path: ``data/kaggle/nba_player_stats_2425.csv`` (override with ``FANDRAGEN_KAGGLE_NBA_CSV``).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from utils.file_utils import PROJECT_ROOT, read_csv
from utils.kaggle_nba_loader import load_kaggle_players_csv

logger = logging.getLogger("fandragen.data_source")

DEFAULT_NBA_STATS_REL = "data/kaggle/nba_player_stats_2425.csv"

_players_cache: tuple[str, list[dict[str, str]]] | None = None


def reset_nba_dataset_cache() -> None:
    """Clear cached NBA CSV load (used by tests)."""

    global _players_cache
    _players_cache = None


def resolve_nba_stats_csv_path() -> Path:
    """Return absolute path to the NBA stats CSV; raise if missing."""

    raw = os.getenv("FANDRAGEN_KAGGLE_NBA_CSV", "").strip()
    path = Path(raw) if raw else PROJECT_ROOT / DEFAULT_NBA_STATS_REL
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    resolved = path.resolve()
    if not resolved.exists():
        hint = (
            " The variable points at a path where no file exists yet—either copy your downloaded "
            "Kaggle `.csv` there (you can rename it to match), or set `FANDRAGEN_KAGGLE_NBA_CSV` to the "
            "actual filename if Kaggle used a different name (e.g. `NBA_2024_2025.csv`)."
            if raw
            else " Download the Kaggle 'NBA Player Stats Season 24/25' CSV and save it at this path, "
            "or set `FANDRAGEN_KAGGLE_NBA_CSV`."
        )
        raise FileNotFoundError(
            f"NBA player stats CSV not found: {resolved}.{hint}"
        )
    return resolved


def nba_stats_csv_display_path() -> str:
    """Resolved path string for logging and delivery payloads."""

    return str(resolve_nba_stats_csv_path())


def exit_if_nba_stats_csv_missing() -> None:
    """Fail fast from CLI/UI with a clear message (call after ``load_env()``)."""

    import sys

    try:
        resolve_nba_stats_csv_path()
    except FileNotFoundError as exc:
        print(
            "\nFanDraGen: NBA stats CSV is missing.\n"
            "  • Download: https://www.kaggle.com/datasets/eduardopalmieri/nba-player-stats-season-2425\n"
            "  • Save as:  data/kaggle/nba_player_stats_2425.csv  (under the FanDraGen project root)\n"
            "  • Or set:   FANDRAGEN_KAGGLE_NBA_CSV=/absolute/path/to/your.csv\n",
            file=sys.stderr,
        )
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc



def load_players_table(_data_dir: Path | None = None, state=None, enrich_nba_api: bool = True) -> list[dict[str, str]]:
    """Load all player rows from the NBA stats CSV, optionally enrich with nba_api (cached per resolved path)."""

    global _players_cache
    path = resolve_nba_stats_csv_path()
    key = str(path)
    if _players_cache and _players_cache[0] == key:
        rows = list(_players_cache[1])
    else:
        rows = load_kaggle_players_csv(path)
        _players_cache = (key, rows)
        logger.info("Loaded %s NBA player rows from %s", len(rows), path)

    # Injury status propagation: ensure every row has 'injury_flag' and 'status'
    for row in rows:
        if "injury_flag" not in row:
            row["injury_flag"] = "0"
        if "status" not in row:
            row["status"] = "Active"

    # Optionally enrich with nba_api if enabled and requested
    if enrich_nba_api and state is not None:
        try:
            from integrations.nba_api_stats import merge_demo_rows_with_nba
            data_dir = _data_dir or (PROJECT_ROOT / "data/nba")
            return merge_demo_rows_with_nba(rows, state, data_dir)
        except Exception as exc:
            logger.warning(f"nba_api enrichment failed, falling back to CSV only: {exc}")
            # Fallback: just return CSV rows
            return rows
    return rows


def _roster_and_free_agents_from_pool(players: list[dict[str, str]], data_dir: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    template_roster = read_csv(data_dir / "roster_template.csv")
    template_fa = read_csv(data_dir / "free_agents_template.csv")
    roster_out: list[dict[str, str]] = []
    for i, trow in enumerate(template_roster):
        if i >= len(players):
            break
        roster_out.append(
            {
                "fantasy_team_id": trow["fantasy_team_id"],
                "player_id": players[i]["player_id"],
                "roster_slot": trow["roster_slot"],
            }
        )
    n_roster = len(roster_out)
    fa_out: list[dict[str, str]] = []
    for j in range(len(template_fa)):
        idx = n_roster + j
        if idx >= len(players):
            break
        fa_out.append({"player_id": players[idx]["player_id"]})
    return roster_out, fa_out



def get_roster_rows(data_dir: Path, state=None) -> list[dict[str, str]]:
    players = load_players_table(data_dir, state=state, enrich_nba_api=state is not None)
    roster_rows, _ = _roster_and_free_agents_from_pool(players, data_dir)
    return roster_rows



def get_free_agent_rows(data_dir: Path, state=None) -> list[dict[str, str]]:
    players = load_players_table(data_dir, state=state, enrich_nba_api=state is not None)
    _, fa_rows = _roster_and_free_agents_from_pool(players, data_dir)
    return fa_rows


def data_source_label() -> str:
    return "NBA stats CSV (Kaggle format)"
