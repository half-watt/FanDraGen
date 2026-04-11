"""Environment loading and feature flags for optional live APIs and Gemini."""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path

_logging_configured = False


def _configure_logging_once() -> None:
    global _logging_configured
    if _logging_configured:
        return
    level = logging.DEBUG if os.getenv("FANDRAGEN_DEBUG", "").strip() in {"1", "true", "yes"} else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s [%(name)s] %(message)s")
    _logging_configured = True


def load_env() -> None:
    """Load `.env` from the project root when `python-dotenv` is available."""

    _configure_logging_once()
    # Pytest sets this in `tests/conftest.py` so tests never read a developer `.env` file.
    if os.getenv("PYTEST_RUNNING"):
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env")


@lru_cache(maxsize=1)
def _flags() -> dict[str, bool | str]:
    load_env()
    return {
        "live_espn": os.getenv("FANDRAGEN_LIVE_ESPN", "").strip().lower() in {"1", "true", "yes"},
        "gemini_key": os.getenv("GEMINI_API_KEY", "").strip(),
        "nba_api": os.getenv("FANDRAGEN_NBA_API", "").strip().lower() in {"1", "true", "yes"},
        "nba_season": os.getenv("NBA_STATS_SEASON", "").strip(),
        "gemini_model": os.getenv("GEMINI_MODEL", "").strip(),
    }


def live_espn_enabled() -> bool:
    """When True, tools may attach live ESPN snapshots (no API key required for ESPN public JSON)."""

    return bool(_flags()["live_espn"])


def gemini_api_key() -> str:
    """Google AI Studio / Gemini API key for optional rationale polish."""

    return str(_flags()["gemini_key"])


def gemini_model_override() -> str | None:
    """Optional single model id to try first (e.g. ``gemini-2.0-flash-001``)."""

    m = _flags()["gemini_model"]
    return str(m) if m else None


def nba_api_enabled() -> bool:
    """When True, merge live stats.nba.com data via ``nba_api`` (see integrations/nba_api_stats)."""

    return bool(_flags()["nba_api"])


def nba_stats_season() -> str | None:
    """Override season for PlayerGameLog, e.g. ``2024-25``. Falls back to ``nba_player_map.json``."""

    s = _flags()["nba_season"]
    return s if s else None
