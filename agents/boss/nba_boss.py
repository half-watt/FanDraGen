"""Concrete NBA boss agent."""

from __future__ import annotations

from agents.boss.base_boss import BaseBossAgent
from agents.delivery.delivery_agent import DeliveryAgent
from agents.evaluators.grounding_evaluator import GroundingEvaluator
from agents.evaluators.output_quality_evaluator import OutputQualityEvaluator
from agents.general.drafting_agent import DraftingAgent
from agents.general.managing_agent import ManagingAgent
from agents.general.news_summarization_agent import NewsSummarizationAgent
from agents.general.onboarding_agent import OnboardingAgent
from agents.general.trade_evaluation_agent import TradeEvaluationAgent
from schemas.models import AgentResult, AgentTask, WorkflowState
from utils.logging_utils import log_event
from workflows import draft_workflow, lineup_workflow, news_workflow, onboarding_workflow, trade_workflow, waiver_workflow


class NBABossAgent(BaseBossAgent):
    """Coordinates worker agents, evaluators, and delivery for NBA requests."""

    boss_name = "NBABossAgent"

    def __init__(self) -> None:
        self.workers = {
            "OnboardingAgent": OnboardingAgent(),
            "DraftingAgent": DraftingAgent(),
            "ManagingAgent": ManagingAgent(),
            "TradeEvaluationAgent": TradeEvaluationAgent(),
            "NewsSummarizationAgent": NewsSummarizationAgent(),
        }
        self.evaluators = [OutputQualityEvaluator(), GroundingEvaluator()]
        self.delivery_agent = DeliveryAgent()

    def _build_tasks(self, state: WorkflowState) -> list[AgentTask]:
        intent = state.route_decision.intent if state.route_decision else "onboarding/help"
        if intent == "onboarding/help":
            return onboarding_workflow.build_tasks(state)
        if intent in {"draft advice", "explanation / why reasoning"}:
            return draft_workflow.build_tasks(state)
        if intent == "lineup optimization":
            return lineup_workflow.build_tasks(state)
        if intent == "trade evaluation":
            return trade_workflow.build_tasks(state)
        if intent == "waiver/free agent pickup":
            return waiver_workflow.build_tasks(state)
        if intent == "roster news summary":
            return news_workflow.build_tasks(state)
        return [
            AgentTask(
                task_type="missing data / fallback explanation",
                description="Explain fallback and missing-data behavior.",
                assigned_agent="ManagingAgent",
            )
        ]

    def _evaluate(self, state: WorkflowState, result: AgentResult, attempt_number: int) -> list[str]:
        feedback = []
        for evaluator in self.evaluators:
            evaluation_result = evaluator.evaluate(state, result, attempt_number)
            state.evaluator_results.append(evaluation_result)
            log_event(
                state,
                "evaluator_result",
                evaluator=evaluation_result.evaluator_name,
                passed=evaluation_result.passed,
                issues=evaluation_result.issues,
            )
            if not evaluation_result.passed:
                feedback.extend(evaluation_result.issues + evaluation_result.recommendations)
        return feedback

    def run(self, state: WorkflowState) -> AgentResult:
        log_event(state, "boss_start", boss=self.boss_name)
        tasks = self._build_tasks(state)
        log_event(
            state,
            "boss_decomposition",
            tasks=[task.model_dump() for task in tasks],
        )
        aggregated_results = []
        for task in tasks:
            worker = self.workers[task.assigned_agent]
            aggregated_results.append(worker.execute(task, state))

        primary_result = aggregated_results[0]
        state.intermediate_outputs["agent_results"] = [result.model_dump() for result in aggregated_results]
        feedback = self._evaluate(state, primary_result, attempt_number=1)
        if feedback and state.revision_count < 1:
            state.revision_count += 1
            worker = self.workers[tasks[0].assigned_agent]
            primary_result = worker.revise(tasks[0], primary_result, feedback, state)
            self._evaluate(state, primary_result, attempt_number=2)

        self.delivery_agent.deliver(state, primary_result)
        log_event(state, "boss_complete", boss=self.boss_name)
        return primary_result
