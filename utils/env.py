"""Environment loading and feature flags for optional live APIs and Gemini."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


def load_env() -> None:
    """Load `.env` from the project root when `python-dotenv` is available."""

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
    }


def live_espn_enabled() -> bool:
    """When True, tools may attach live ESPN snapshots (no API key required for ESPN public JSON)."""

    return bool(_flags()["live_espn"])


def gemini_api_key() -> str:
    """Google AI Studio / Gemini API key for optional rationale polish."""

    return str(_flags()["gemini_key"])
