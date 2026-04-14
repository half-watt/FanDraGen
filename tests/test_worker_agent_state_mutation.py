"""Test that worker agents do not mutate orchestration state (routing, fallback, approval logic)."""

import inspect
import ast
import os

AGENT_DIR = os.path.join(os.path.dirname(__file__), "..", "agents", "general")

# Fields that should only be mutated by orchestrator/boss, not worker agents
FORBIDDEN_MUTATIONS = [
    "route_decision",
    "fallback_flags",
    "approval_status",
    "logs",
    "trace_metadata",
    "original_plan",
]


def test_worker_agents_do_not_mutate_orchestration_state():
    for fname in os.listdir(AGENT_DIR):
        if not fname.endswith("_agent.py"):
            continue
        path = os.path.join(AGENT_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=fname)
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                if (
                    isinstance(node.value, ast.Name)
                    and node.value.id == "state"
                    and node.attr in FORBIDDEN_MUTATIONS
                ):
                    # Check if this attribute is being assigned to
                    parent = getattr(node, "parent", None)
                    if parent is None:
                        continue
                    if isinstance(parent, ast.Assign) or isinstance(parent, ast.AugAssign):
                        raise AssertionError(
                            f"Worker agent {fname} mutates forbidden state field: state.{node.attr}"
                        )
        # Attach parent pointers for assignment detection
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node
