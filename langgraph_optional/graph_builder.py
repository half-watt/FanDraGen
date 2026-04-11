"""Optional LangGraph builder.

The plain Python path is the source of truth. This module demonstrates how the
same steps could be represented as graph nodes without forcing LangGraph to be a
required dependency.
"""

from __future__ import annotations


def build_graph() -> dict[str, list[str]]:
    """Return a simple node description or raise a clear optional-dependency error."""

    try:
        import langgraph  # type: ignore # pragma: no cover
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("LangGraph is optional and not installed. The plain Python workflow still works.") from exc
    return {
        "nodes": [
            "routing",
            "boss",
            "worker_or_tool",
            "evaluators",
            "delivery",
            "approval",
        ]
    }
