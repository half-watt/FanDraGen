"""Load and normalize the Kaggle *NBA Player Stats Season 24/25* CSV.

Dataset: https://www.kaggle.com/datasets/eduardopalmieri/nba-player-stats-season-2425

Supports (1) **per-player season** tables with ``GP`` / totals and (2) **game logs**
(e.g. ``database_24_25.csv`` with ``Data``, ``Opp``, one row per game) by aggregating
per player before building fantasy rows.

The app loads this file from the path returned by ``resolve_nba_stats_csv_path()`` in
``utils/nba_data_source`` (default ``data/kaggle/nba_player_stats_2425.csv``, or ``FANDRAGEN_KAGGLE_NBA_CSV``).
Column names are matched flexibly (common variants).
"""

from __future__ import annotations

import csv
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Any

logger = logging.getLogger("fandragen.kaggle")

# Normalized internal names -> possible CSV header aliases (lowercased for match)
_ALIASES: dict[str, tuple[str, ...]] = {
    "player": ("player", "name", "player_name"),
    "team": ("team", "tm", "team_abbr"),
    "pos": ("pos", "position"),
    "gp": ("gp", "g", "games"),
    "pts": ("pts", "points", "ppg"),
    "reb": ("reb", "trb", "rebounds", "rpg"),
    "ast": ("ast", "assists", "apg"),
    "min": ("min", "mp", "minutes", "mpg"),
    "nba_id": ("player_id", "id", "nba_id", "person_id"),
}


def _norm_key(h: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", h.strip().lower())


def _header_map(fieldnames: list[str] | None) -> dict[str, str]:
    """Map normalized alias -> actual CSV header string."""

    if not fieldnames:
        return {}
    inv: dict[str, str] = {}
    for h in fieldnames:
        inv[_norm_key(h)] = h
    out: dict[str, str] = {}
    for canon, aliases in _ALIASES.items():
        for a in aliases:
            nk = _norm_key(a)
            if nk in inv:
                out[canon] = inv[nk]
                break
    return out


def _float_cell(row: dict[str, str], header: str | None, default: float = 0.0) -> float:
    if not header:
        return default
    raw = (row.get(header) or "").strip()
    if not raw:
        return default
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return default


def _is_game_log_format(hm: dict[str, str], fieldnames: list[str] | None) -> bool:
    """True when the file looks like game-by-game rows (no GP column, date/opponent style)."""

    if hm.get("gp"):
        return False
    if not hm.get("pts") or not hm.get("player"):
        return False
    fnk = {_norm_key(f or "") for f in (fieldnames or [])}
    has_game_marker = "data" in fnk or "date" in fnk or "opp" in fnk or "opponent" in fnk
    return bool(has_game_marker and hm.get("team"))


def _aggregate_game_log(rows: list[dict[str, str]], hm: dict[str, str]) -> list[dict[str, str]]:
    """Sum game logs per player; emit per-game averages."""

    agg: dict[str, dict[str, Any]] = {}
    for row in rows:
        name = (row.get(hm["player"]) or "").strip()
        if not name or name.lower() in {"player", "nan"}:
            continue
        if name not in agg:
            agg[name] = {
                "gp": 0,
                "spts": 0.0,
                "sreb": 0.0,
                "sast": 0.0,
                "smin": 0.0,
                "teams": Counter(),
            }
        a = agg[name]
        a["gp"] += 1
        a["spts"] += _float_cell(row, hm.get("pts"))
        a["sreb"] += _float_cell(row, hm.get("reb"))
        a["sast"] += _float_cell(row, hm.get("ast"))
        a["smin"] += _float_cell(row, hm.get("min"))
        if hm.get("team"):
            tm = (row.get(hm["team"]) or "").strip()
            if tm:
                a["teams"][tm] += 1

    rows_out: list[dict[str, str]] = []
    for name, a in agg.items():
        gp = max(1, int(a["gp"]))
        team = a["teams"].most_common(1)[0][0] if a["teams"] else "UNK"
        pts_pg = a["spts"] / gp
        reb_pg = a["sreb"] / gp
        ast_pg = a["sast"] / gp
        mpg = a["smin"] / gp if a["smin"] > 0 else 28.0
        pos = "UTIL"
        projected = round(pts_pg * 1.08 + reb_pg * 1.1 + ast_pg * 1.4, 2)
        recent = round(pts_pg * 1.02, 2)
        rows_out.append(
            {
                "player_id": "kg_tmp",
                "player_name": name,
                "sport": "NBA",
                "team": team[:8],
                "position": pos[:8],
                "status": "healthy",
                "projected_points": f"{projected:.2f}",
                "recent_points_avg": f"{recent:.2f}",
                "injury_flag": "0",
                "sentiment_score": "0",
                "matchup_difficulty": "3",
                "gp": str(gp),
                "mpg": f"{mpg:.1f}",
                "pts": f"{pts_pg:.2f}",
                "reb": f"{reb_pg:.2f}",
                "ast": f"{ast_pg:.2f}",
                "kaggle_source": "1",
                "kaggle_nba_person_id": "",
            }
        )
    return rows_out


def load_kaggle_players_csv(path: Path) -> list[dict[str, str]]:
    """Read Kaggle CSV and emit rows compatible with ``players.csv`` tool schema."""

    if not path.exists():
        raise FileNotFoundError(f"Kaggle NBA CSV not found: {path}")

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        hm = _header_map(list(fieldnames or []))
        if "player" not in hm:
            raise ValueError(
                f"Could not find a Player column in {path}. Headers: {fieldnames}. "
                "Expected a column like 'Player' or 'PLAYER'."
            )

        raw_rows = [row for row in reader if (row.get(hm["player"]) or "").strip()]

    if _is_game_log_format(hm, list(fieldnames or [])):
        logger.info("Detected game-log format; aggregating per player from %s", path)
        rows_out = _aggregate_game_log(raw_rows, hm)
    else:
        rows_out = []
        for idx, row in enumerate(raw_rows):
            name = (row.get(hm["player"]) or "").strip()
            if not name or name.lower() in {"player", "nan"}:
                continue
            team = (row.get(hm.get("team", ""), "") if hm.get("team") else "").strip() or "UNK"
            pos = (row.get(hm.get("pos", ""), "") if hm.get("pos") else "").strip() or "UTIL"
            gp = max(1, int(_float_cell(row, hm.get("gp"), 1)))
            pts = _float_cell(row, hm.get("pts"))
            reb = _float_cell(row, hm.get("reb"))
            ast = _float_cell(row, hm.get("ast"))
            mpg = _float_cell(row, hm.get("min"))
            if mpg <= 0 and gp > 0:
                mpg = 28.0
            pts_pg = pts
            if pts > 80 and gp > 0:
                pts_pg = pts / gp
            reb_pg = reb / gp if reb > 40 and gp else reb
            ast_pg = ast / gp if ast > 40 and gp else ast

            nba_pid = ""
            if hm.get("nba_id"):
                raw_id = (row.get(hm["nba_id"]) or "").strip()
                if raw_id.isdigit():
                    nba_pid = raw_id

            projected = round(pts_pg * 1.08 + reb_pg * 1.1 + ast_pg * 1.4, 2)
            recent = round(pts_pg * 1.02, 2)

            rows_out.append(
                {
                    "player_id": f"kg_{idx + 1:05d}",
                    "player_name": name,
                    "sport": "NBA",
                    "team": team[:8],
                    "position": pos[:8],
                    "status": "healthy",
                    "projected_points": f"{projected:.2f}",
                    "recent_points_avg": f"{recent:.2f}",
                    "injury_flag": "0",
                    "sentiment_score": "0",
                    "matchup_difficulty": "3",
                    "gp": str(gp),
                    "mpg": f"{mpg:.1f}",
                    "pts": f"{pts_pg:.2f}",
                    "reb": f"{reb_pg:.2f}",
                    "ast": f"{ast_pg:.2f}",
                    "kaggle_source": "1",
                    "kaggle_nba_person_id": nba_pid,
                }
            )

    rows_out.sort(key=lambda r: float(r["projected_points"]), reverse=True)
    for i, r in enumerate(rows_out):
        r["player_id"] = f"kg_{i + 1:05d}"

    logger.info("Loaded %s players from Kaggle CSV %s", len(rows_out), path)
    return rows_out
