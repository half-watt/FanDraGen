"""End-to-end workflow orchestrator."""

from __future__ import annotations

from schemas.models import UserQuery, WorkflowState
from utils.env import gemini_api_key, live_espn_enabled, load_env, nba_api_enabled
from utils.file_utils import read_yaml
from utils.logging_utils import log_event
from utils.metrics import update_metrics
from utils.trace_utils import add_trace_metadata
from agents.boss.nba_boss import NBABossAgent
from agents.routing_agent import RoutingAgent


class WorkflowOrchestrator:
    """Runs the full FanDraGen flow from routing through delivery."""

    def __init__(self) -> None:
        self.router = RoutingAgent()
        self.nba_boss = NBABossAgent()

    def _dispatch_route_target(self, route_target: str, state: WorkflowState) -> None:
        """Dispatch to a known boss target or apply deterministic fallback."""

        if route_target == "NBABossAgent":
            self.nba_boss.run(state)
            return
        state.add_fallback(f"unsupported_route_target:{route_target}")
        log_event(
            state,
            "route_target_fallback",
            route_target=route_target,
            fallback_target="NBABossAgent",
        )
        self.nba_boss.run(state)

    def run(self, query_text: str) -> WorkflowState:
        load_env()
        query = UserQuery(text=query_text)
        state = WorkflowState(original_user_query=query)
        config = read_yaml(__import__("pathlib").Path("configs/default_config.yaml"))
        add_trace_metadata(
            state,
            mode="mocked",
            architecture="plain_python",
            scenario_name=config["demo"]["scenario_name"],
            calendar_window=config["demo"]["calendar_window"],
            live_espn_enrichment_enabled=live_espn_enabled(),
            gemini_configured=bool(gemini_api_key()),
            nba_api_enrichment_enabled=nba_api_enabled(),
        )
        route = self.router.route(query, state)
        self._dispatch_route_target(route.route_target, state)
        update_metrics(state)
        log_event(state, "workflow_complete", metrics=state.metrics)
        return state
