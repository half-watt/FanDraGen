"""Base boss-agent abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod

from schemas.models import AgentResult, WorkflowState


class BaseBossAgent(ABC):
    """Base interface for boss agents that orchestrate workers and tools."""

    boss_name = "BaseBossAgent"

    @abstractmethod
    def run(self, state: WorkflowState) -> AgentResult:
        """Execute the orchestration for the routed workflow state."""
