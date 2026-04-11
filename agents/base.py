"""Base classes for FanDraGen agents."""

from __future__ import annotations

from abc import ABC, abstractmethod

from schemas.models import AgentResult, AgentTask, WorkflowState
from utils.logging_utils import log_event


class BaseAgent(ABC):
    """Shared behavior for worker agents and helper-style agents."""

    agent_name = "BaseAgent"

    def _start(self, state: WorkflowState, task: AgentTask) -> None:
        if self.agent_name not in state.invoked_agents:
            state.invoked_agents.append(self.agent_name)
        log_event(state, "agent_start", agent=self.agent_name, task=task.task_type)

    @abstractmethod
    def execute(self, task: AgentTask, state: WorkflowState) -> AgentResult:
        """Execute an agent task against shared workflow state."""

    def revise(
        self,
        task: AgentTask,
        prior_result: AgentResult,
        feedback: list[str],
        state: WorkflowState,
    ) -> AgentResult:
        """Default single-pass revision strategy.

        The mocked system does not synthesize a brand-new answer from a model. It
        strengthens grounding by appending evaluator feedback and explicitly
        surfacing tool evidence that was already available.
        """

        revised = prior_result.model_copy(deep=True)
        revised.assumptions.extend([f"Revision note: {item}" for item in feedback])
        if revised.supporting_tool_results:
            revised.rationale.extend(
                [
                    f"Grounded by {tool_result.tool_name}.{tool_result.method_name}: {tool_result.summary}"
                    for tool_result in revised.supporting_tool_results
                ]
            )
        revised.summary = f"{prior_result.summary} Revised once to address evaluator feedback."
        revised.confidence = max(0.55, prior_result.confidence - 0.05)
        log_event(state, "agent_revision", agent=self.agent_name, task=task.task_type, feedback=feedback)
        return revised
