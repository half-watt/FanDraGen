"""Onboarding and help agent."""

from __future__ import annotations

from agents.base import BaseAgent
from agents.nba.nba_rules_interpreter import NBARulesInterpreter
from schemas.models import AgentResult, AgentTask, WorkflowState
from tools.league_data_tool import LeagueDataTool
from tools.rules_tool import RulesTool
from utils.file_utils import demo_path, read_json


class OnboardingAgent(BaseAgent):
    """Explains how the demo league works for new users."""

    agent_name = "OnboardingAgent"

    def __init__(self) -> None:
        self.league_data_tool = LeagueDataTool()
        self.rules_tool = RulesTool()
        self.rules_interpreter = NBARulesInterpreter()

    def execute(self, task: AgentTask, state: WorkflowState) -> AgentResult:
        self._start(state, task)
        rules_result = self.rules_tool.fetch_league_rules(state)
        scoring_result = self.rules_tool.explain_scoring_format(state)
        self.league_data_tool.fetch_scoring_rules(state)
        scenario = read_json(demo_path("season_context.json"))
        summary = "FanDraGen uses a mocked NBA points-league setup with deterministic late-season demo data."
        rationale = [
            f"Scenario: {scenario['scenario_name']} during {scenario['calendar_window']}.",
            self.rules_interpreter.summarize_roster_logic(state.league_context),
            self.rules_interpreter.interpret_scoring(state.league_context),
            scoring_result.data["explanation"],
        ]
        return AgentResult(
            agent_name=self.agent_name,
            summary=summary,
            confidence=0.92,
            rationale=rationale,
            assumptions=["This explanation reflects mocked local rules only.", "The demo is intentionally set in the final week before fantasy playoffs."],
            supporting_tool_results=[rules_result, scoring_result],
            structured_payload={"league_rules": rules_result.data, "season_context": scenario},
        )
