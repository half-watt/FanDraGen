"""Routing prompt-like guidance.

These constants are not used as LLM prompts in the mocked build. They exist to
document the intended routing criteria and to make a future model-backed router
easy to add.
"""

ROUTING_GUIDANCE = {
    "supported_intents": [
        "onboarding/help",
        "draft advice",
        "lineup optimization",
        "trade evaluation",
        "waiver/free agent pickup",
        "roster news summary",
        "explanation / why reasoning",
        "missing data / fallback explanation",
    ],
    "domain_rule": "Prefer NBA routing when the query references basketball, NBA, roster, lineup, waiver, trade, or draft context.",
}