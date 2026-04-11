"""Evaluator tests."""

from __future__ import annotations

from agents.evaluators.grounding_evaluator import GroundingEvaluator
from agents.evaluators.output_quality_evaluator import OutputQualityEvaluator
from schemas.models import AgentResult, UserQuery, WorkflowState


def _state(query_text: str = "Set my best lineup for this week.") -> WorkflowState:
    return WorkflowState(original_user_query=UserQuery(text=query_text))


def test_output_quality_evaluator_rejects_missing_rationale() -> None:
    result = AgentResult(agent_name="TestAgent", summary="Short answer", confidence=0.5)
    evaluation = OutputQualityEvaluator().evaluate(_state(), result, attempt_number=1)
    assert evaluation.passed is False


def test_grounding_evaluator_rejects_ungrounded_missing_data_answer() -> None:
    state = _state("What assumptions are you making because data is missing?")
    result = AgentResult(
        agent_name="TestAgent",
        summary="Explained fallback assumptions in demo mode.",
        confidence=0.7,
        assumptions=["demo_mode_only"],
    )
    evaluation = GroundingEvaluator().evaluate(state, result, attempt_number=1)
    assert evaluation.passed is False
