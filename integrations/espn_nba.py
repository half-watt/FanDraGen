"""Public ESPN JSON endpoints for live NBA context (no API key).

Used to enrich demo tools with real headlines and a standings snapshot while
fictional roster rows remain file-backed.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


ESPN_NEWS_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/news"
ESPN_STANDINGS_URL = "https://site.api.espn.com/apis/v2/sports/basketball/nba/standings"


def _get_json(url: str, timeout: float = 12.0) -> dict[str, Any] | None:
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "FanDraGen/0.1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def fetch_nba_news_headlines(limit: int = 5) -> dict[str, Any]:
    """Return recent NBA headlines from ESPN (public)."""

    data = _get_json(f"{ESPN_NEWS_URL}?limit={limit}")
    if not data:
        return {"ok": False, "error": "unavailable", "headlines": []}
    articles = data.get("articles") or []
    headlines = []
    for art in articles[:limit]:
        headlines.append(
            {
                "headline": art.get("headline", ""),
                "description": (art.get("description") or "")[:280],
                "published": art.get("published"),
            }
        )
    return {"ok": True, "source": "espn_nba_news", "headlines": headlines}


def fetch_nba_standings_snapshot(max_teams: int = 8) -> dict[str, Any]:
    """Return a compact standings slice for narrative grounding."""

    data = _get_json(ESPN_STANDINGS_URL)
    if not data:
        return {"ok": False, "error": "unavailable", "entries": []}
    entries: list[dict[str, Any]] = []
    for conf in data.get("children") or []:
        standings = (conf.get("standings") or {}).get("entries") or []
        for row in standings:
            team = row.get("team") or {}
            wins = losses = None
            for s in row.get("stats") or []:
                if s.get("name") == "wins":
                    wins = s.get("value")
                if s.get("name") == "losses":
                    losses = s.get("value")
            entries.append(
                {
                    "team": team.get("displayName") or team.get("name"),
                    "abbrev": team.get("abbreviation"),
                    "wins": wins,
                    "losses": losses,
                }
            )
            if len(entries) >= max_teams:
                break
        if len(entries) >= max_teams:
            break
    return {"ok": True, "source": "espn_nba_standings", "entries": entries[:max_teams]}
