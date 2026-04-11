"""Evaluator policy notes."""

EVALUATOR_GUIDANCE = {
    "strictness": "moderate",
    "fail_conditions": [
        "answer does not address the user request",
        "claims are unsupported by tool results",
        "response is too vague to justify the recommendation",
    ],
}