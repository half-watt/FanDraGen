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
from utils.gemini_enrichment import enrich_summary_with_gemini
from utils.logging_utils import log_event
from workflows.intent_registry import build_tasks_for_route


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
        return build_tasks_for_route(state)

    def _fallback_task_for_missing_worker(self, missing_agent: str) -> AgentTask:
        """Return a deterministic fallback task when a configured worker is missing."""

        return AgentTask(
            task_type="missing data / fallback explanation",
            description=f"Fallback because assigned worker '{missing_agent}' was not configured.",
            assigned_agent="ManagingAgent",
        )

    def _maybe_enrich_with_gemini(self, state: WorkflowState, result: AgentResult) -> AgentResult:
        """Optional Gemini polish after evaluators; does not add new facts."""

        snippets: list[str] = []
        for tr in result.supporting_tool_results:
            snippets.append(f"{tr.tool_name}.{tr.method_name}: {tr.summary}")
            if tr.data is not None:
                snippets.append(str(tr.data)[:2000])
        enriched = enrich_summary_with_gemini(result.summary, result.rationale, snippets)
        if not enriched:
            return result
        new_summary, new_rationale = enriched
        updated = result.model_copy(deep=True)
        updated.summary = new_summary
        updated.rationale = new_rationale
        state.trace_metadata["gemini_enrichment_applied"] = True
        return updated

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
        aggregated_results: list[AgentResult] = []
        executed_tasks: list[AgentTask] = []
        for task in tasks:
            worker = self.workers.get(task.assigned_agent)
            if worker is None:
                state.add_fallback(f"missing_worker:{task.assigned_agent}")
                log_event(
                    state,
                    "boss_worker_fallback",
                    missing_worker=task.assigned_agent,
                    fallback_worker="ManagingAgent",
                )
                task = self._fallback_task_for_missing_worker(task.assigned_agent)
                worker = self.workers[task.assigned_agent]
            executed_tasks.append(task)
            aggregated_results.append(worker.execute(task, state))

        if not aggregated_results:
            raise RuntimeError("Boss decomposition produced no executable tasks.")

        primary_result = aggregated_results[0]
        state.intermediate_outputs["agent_results"] = [result.model_dump() for result in aggregated_results]
        max_revisions = 2
        revision_attempt = 1
        feedback = self._evaluate(state, primary_result, attempt_number=revision_attempt)
        while feedback and state.revision_count < max_revisions:
            state.revision_count += 1
            primary_task = executed_tasks[0]
            worker = self.workers[primary_task.assigned_agent]
            primary_result = worker.revise(primary_task, primary_result, feedback, state)
            revision_attempt += 1
            feedback = self._evaluate(state, primary_result, attempt_number=revision_attempt)

        # If unresolved evaluator issues remain, surface them in the final output
        if feedback:
            if not hasattr(primary_result, "assumptions") or primary_result.assumptions is None:
                primary_result.assumptions = []
            primary_result.assumptions.append(
                f"Unresolved evaluator issues after {max_revisions} revisions: {', '.join(feedback)}"
            )
            # Optionally, also append to rationale or summary for visibility
            primary_result.rationale.append(
                f"Evaluator feedback could not be fully resolved: {', '.join(feedback)}"
            )
            primary_result.summary += f" (Evaluator feedback could not be fully resolved after {max_revisions} attempts.)"

        primary_result = self._maybe_enrich_with_gemini(state, primary_result)
        self.delivery_agent.deliver(state, primary_result)
        log_event(state, "boss_complete", boss=self.boss_name)
        return primary_result
