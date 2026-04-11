"""ESPN client tests with mocked HTTP (no network)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from integrations import espn_nba


def test_fetch_nba_news_headlines_parses_articles() -> None:
    payload = {
        "articles": [
            {"headline": "H1", "description": "D1", "published": "2026-01-01"},
            {"headline": "H2", "description": "D2", "published": "2026-01-02"},
        ]
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(payload).encode("utf-8")
    cm = MagicMock()
    cm.__enter__.return_value = mock_resp
    cm.__exit__.return_value = None

    with patch("integrations.espn_nba.urllib.request.urlopen", return_value=cm):
        out = espn_nba.fetch_nba_news_headlines(limit=2)

    assert out["ok"] is True
    assert len(out["headlines"]) == 2
    assert out["headlines"][0]["headline"] == "H1"


def test_fetch_nba_standings_snapshot_handles_entries() -> None:
    payload = {
        "children": [
            {
                "standings": {
                    "entries": [
                        {
                            "team": {"displayName": "Test Team", "abbreviation": "TST"},
                            "stats": [
                                {"name": "wins", "value": 50.0},
                                {"name": "losses", "value": 20.0},
                            ],
                        }
                    ]
                }
            }
        ]
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(payload).encode("utf-8")
    cm = MagicMock()
    cm.__enter__.return_value = mock_resp
    cm.__exit__.return_value = None

    with patch("integrations.espn_nba.urllib.request.urlopen", return_value=cm):
        out = espn_nba.fetch_nba_standings_snapshot(max_teams=3)

    assert out["ok"] is True
    assert out["entries"][0]["team"] == "Test Team"
    assert out["entries"][0]["wins"] == 50.0


def test_fetch_returns_not_ok_on_network_error() -> None:
    with patch("integrations.espn_nba.urllib.request.urlopen", side_effect=OSError("no network")):
        out = espn_nba.fetch_nba_news_headlines(limit=1)
    assert out["ok"] is False
    assert out["headlines"] == []
