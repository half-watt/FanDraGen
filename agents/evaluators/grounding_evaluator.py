"""Evaluator that checks grounding against tool outputs."""

from __future__ import annotations

from schemas.models import AgentResult, EvaluationResult, WorkflowState


class GroundingEvaluator:
    """Ensures conclusions are supported by tool outputs."""

    evaluator_name = "GroundingEvaluator"

    def evaluate(self, state: WorkflowState, result: AgentResult, attempt_number: int) -> EvaluationResult:
        issues = []
        if not result.supporting_tool_results:
            issues.append("No tool outputs were attached to the result.")
        elif any(not tr.summary.strip() for tr in result.supporting_tool_results):
            issues.append("A tool result is missing a summary, reducing auditability.")
        if result.recommendations and not all(item.supporting_evidence for item in result.recommendations):
            issues.append("One or more recommendations are missing supporting evidence.")
        if state.original_user_query.text.lower().startswith("what assumptions") and not result.assumptions:
            issues.append("Fallback explanation request did not surface explicit assumptions.")
        passed = not issues
        recommendations = [] if passed else ["Reference specific tool evidence and fallback state explicitly."]
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            passed=passed,
            confidence=0.8 if passed else 0.65,
            issues=issues,
            recommendations=recommendations,
            attempt_number=attempt_number,
        )
