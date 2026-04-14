"""Test that all intent keys and priorities are mapped in INTENT_TO_WORKFLOW, and vice versa."""

from workflows.intent_registry import INTENT_KEYWORDS, INTENT_PRIORITY, INTENT_TO_WORKFLOW

def test_intent_mapping_completeness():
    # All keys in INTENT_KEYWORDS and INTENT_PRIORITY must be in INTENT_TO_WORKFLOW
    for key in INTENT_KEYWORDS:
        assert key in INTENT_TO_WORKFLOW, f"Intent '{key}' in INTENT_KEYWORDS is not mapped in INTENT_TO_WORKFLOW."
    for key in INTENT_PRIORITY:
        assert key in INTENT_TO_WORKFLOW, f"Intent '{key}' in INTENT_PRIORITY is not mapped in INTENT_TO_WORKFLOW."
    # All INTENT_TO_WORKFLOW keys must be in INTENT_KEYWORDS
    for key in INTENT_TO_WORKFLOW:
        assert key in INTENT_KEYWORDS, f"Intent '{key}' in INTENT_TO_WORKFLOW is not in INTENT_KEYWORDS."
    # All INTENT_TO_WORKFLOW keys must be in INTENT_PRIORITY
    for key in INTENT_TO_WORKFLOW:
        assert key in INTENT_PRIORITY, f"Intent '{key}' in INTENT_TO_WORKFLOW is not in INTENT_PRIORITY."
