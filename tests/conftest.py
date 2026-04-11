"""Shared test fixtures for FanDraGen."""

from __future__ import annotations

import pytest

from workflows.orchestrator import WorkflowOrchestrator


@pytest.fixture
def orchestrator() -> WorkflowOrchestrator:
    return WorkflowOrchestrator()
