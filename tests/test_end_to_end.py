"""Deterministic end-to-end tests covering the required demo prompts."""

from __future__ import annotations

import pytest

from workflows.orchestrator import WorkflowOrchestrator


PROMPTS = [
    "I am new to fantasy basketball. How does this league work?",
    "Who should I draft first from the available player pool?",
    "Set my best lineup for this week.",
    "Should I trade Player A for Player B?",
    "Who is the best waiver pickup right now?",
    "Summarize important news for my roster.",
    "Why did you rank these players this way?",
    "What assumptions are you making because data is missing?",
]


@pytest.mark.parametrize("prompt", PROMPTS)
def test_mock_mode_end_to_end(prompt: str) -> None:
    state = WorkflowOrchestrator().run(prompt)
    assert state.final_delivery_payload is not None
    assert state.final_delivery_payload.json_payload["fallback_demo_data_usage"]["using_demo_data"] is True
    assert state.metrics["task_completion_rate"] == 1.0
