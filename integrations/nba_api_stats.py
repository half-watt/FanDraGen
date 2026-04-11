"""Live NBA statistics via `nba_api` (stats.nba.com endpoints).

Maps fantasy `player_id` values from optional `data/nba/nba_player_map.json` (or
`kaggle_nba_person_id` on each row) to real `PERSON_ID` values, then pulls game logs for the configured season.

See: https://github.com/swar/nba_api
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from schemas.models import WorkflowState
from utils.env import nba_api_enabled, nba_stats_season
from utils.file_utils import read_json

logger = logging.getLogger("fandragen.nba_api")

# In-process cache to avoid repeated HTTP calls within one Python process.
_snapshot_cache: dict[tuple[int, str], dict[str, Any] | None] = {}


def load_nba_player_map(data_dir: Path) -> dict[str, Any]:
    path = data_dir / "nba_player_map.json"
    if not path.exists():
        return {}
    return read_json(path)


def _fetch_playergamelog_snapshot(nba_player_id: int, season: str) -> dict[str, Any] | None:
    """Return last-10 and season game-log averages (PTS/REB/AST) from PlayerGameLog."""

    cache_key = (nba_player_id, season)
    if cache_key in _snapshot_cache:
        return _snapshot_cache[cache_key]

    try:
        from nba_api.stats.endpoints import playergamelog
    except ImportError:
        logger.warning("nba_api package not installed; pip install nba_api")
        _snapshot_cache[cache_key] = None
        return None

    try:
        # stats.nba.com can be slow; default nba_api timeout is 30s.
        gl = playergamelog.PlayerGameLog(
            player_id=str(nba_player_id),
            season=season,
            timeout=90,
        )
        df = gl.get_data_frames()[0]
    except Exception as exc:
        logger.warning("nba_api PlayerGameLog failed for id=%s season=%s: %s", nba_player_id, season, exc)
        _snapshot_cache[cache_key] = None
        return None

    if df is None or df.empty:
        logger.info("No game log rows for nba_player_id=%s season=%s", nba_player_id, season)
        _snapshot_cache[cache_key] = None
        return None

    # Newest games first
    last10 = df.head(10)
    snap: dict[str, Any] = {
        "nba_source": "nba_api.playergamelog",
        "nba_season": season,
        "nba_player_id": nba_player_id,
        "nba_games_in_log": int(len(df)),
        "nba_pts_last10_avg": float(last10["PTS"].mean()),
        "nba_reb_last10_avg": float(last10["REB"].mean()),
        "nba_ast_last10_avg": float(last10["AST"].mean()),
        "nba_pts_season_avg": float(df["PTS"].mean()),
        "nba_reb_season_avg": float(df["REB"].mean()),
        "nba_ast_season_avg": float(df["AST"].mean()),
    }
    _snapshot_cache[cache_key] = snap
    return snap


def merge_demo_rows_with_nba(
    rows: list[dict[str, str]],
    state: WorkflowState,
    data_dir: Path,
) -> list[dict[str, Any]]:
    """Attach real NBA game-log averages to player rows when `FANDRAGEN_NBA_API=1`."""

    if not nba_api_enabled():
        return list(rows)

    nba_map = load_nba_player_map(data_dir)
    players_map = nba_map.get("players") or {}
    season = nba_stats_season() or str(nba_map.get("season_default") or "2024-25")

    merged: list[dict[str, Any]] = []
    ok = 0
    failed = 0
    for row in rows:
        pid = row.get("player_id")
        entry = players_map.get(pid) if pid else None
        out: dict[str, Any] = dict(row)
        nba_id: int | None = None
        mapped_name = ""
        if entry:
            nba_id = int(entry["nba_player_id"])
            mapped_name = str(entry.get("nba_full_name") or "")
        elif (row.get("kaggle_nba_person_id") or "").strip().isdigit():
            nba_id = int(str(row["kaggle_nba_person_id"]).strip())
            mapped_name = str(row.get("player_name") or "")
        if nba_id is None:
            merged.append(out)
            continue
        snap = _fetch_playergamelog_snapshot(nba_id, season)
        if snap:
            ok += 1
            out.update(snap)
            out["nba_mapped_full_name"] = mapped_name
            # Blend table projection with NBA scoring signal (same scale ~25–55).
            try:
                demo_proj = float(row.get("projected_points", 0))
                nba_signal = float(snap["nba_pts_last10_avg"]) * 1.15
                out["effective_projected_points"] = round(0.45 * demo_proj + 0.55 * nba_signal, 2)
                demo_recent = float(row.get("recent_points_avg", 0))
                out["effective_recent_points_avg"] = round(0.35 * demo_recent + 0.65 * float(snap["nba_pts_last10_avg"]), 2)
            except (TypeError, ValueError):
                pass
        else:
            failed += 1
            state.add_fallback(f"nba_api_no_gamelog:{pid}")
        merged.append(out)

    if ok:
        state.trace_metadata["nba_api_players_enriched"] = ok
    if failed:
        state.trace_metadata["nba_api_partial_failures"] = failed
    return merged


def clear_nba_cache_for_tests() -> None:
    """Reset HTTP cache (used by tests)."""

    _snapshot_cache.clear()
