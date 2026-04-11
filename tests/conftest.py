"""Shared test fixtures for FanDraGen."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_TEST_NBA_CSV = Path(__file__).resolve().parent / "fixtures" / "kaggle_minimal.csv"

# Prevent loading developer `.env` during tests (deterministic, no real API calls).
os.environ["PYTEST_RUNNING"] = "1"

import integrations.nba_api_stats as nba_api_stats  # noqa: E402
import utils.env as env_mod  # noqa: E402
from utils.nba_data_source import reset_nba_dataset_cache  # noqa: E402


@pytest.fixture(autouse=True)
def reset_api_env_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("FANDRAGEN_LIVE_ESPN", raising=False)
    monkeypatch.delenv("FANDRAGEN_NBA_API", raising=False)
    monkeypatch.delenv("NBA_STATS_SEASON", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setenv("FANDRAGEN_KAGGLE_NBA_CSV", str(_TEST_NBA_CSV))
    env_mod._flags.cache_clear()
    nba_api_stats.clear_nba_cache_for_tests()
    reset_nba_dataset_cache()


from workflows.orchestrator import WorkflowOrchestrator  # noqa: E402


@pytest.fixture
def orchestrator() -> WorkflowOrchestrator:
    return WorkflowOrchestrator()
