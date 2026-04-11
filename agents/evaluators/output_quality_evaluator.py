"""Evaluator that checks whether the response actually answers the request."""

from __future__ import annotations

from schemas.models import AgentResult, EvaluationResult, WorkflowState


class OutputQualityEvaluator:
    """Moderately strict quality evaluator."""

    evaluator_name = "OutputQualityEvaluator"

    def evaluate(self, state: WorkflowState, result: AgentResult, attempt_number: int) -> EvaluationResult:
        issues = []
        query = state.original_user_query.text.lower()
        if len(result.summary.strip()) < 30:
            issues.append("Summary is too short to be useful.")
        if any(keyword in query for keyword in ["draft", "lineup", "trade", "waiver"]) and not result.recommendations:
            issues.append("Recommendation-style request did not yield a structured recommendation.")
        if "trade" in query and result.recommendations:
            trade_rec = result.recommendations[0]
            if "delta" not in trade_rec.details.lower() and "heuristic" not in trade_rec.details.lower():
                issues.append("Trade evaluation should reference the computed delta or heuristic comparison in details.")
        if not result.rationale:
            issues.append("Result is missing rationale.")
        passed = not issues
        recommendations = [] if passed else ["Add a clearer direct answer and rationale linked to the request."]
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            passed=passed,
            confidence=0.82 if passed else 0.67,
            issues=issues,
            recommendations=recommendations,
            attempt_number=attempt_number,
        )
