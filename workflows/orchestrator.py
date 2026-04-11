"""End-to-end workflow orchestrator."""

from __future__ import annotations

from schemas.models import UserQuery, WorkflowState
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

    def run(self, query_text: str) -> WorkflowState:
        query = UserQuery(text=query_text)
        state = WorkflowState(original_user_query=query)
        config = read_yaml(__import__("pathlib").Path("configs/default_config.yaml"))
        add_trace_metadata(
            state,
            mode="mocked",
            architecture="plain_python",
            scenario_name=config["demo"]["scenario_name"],
            calendar_window=config["demo"]["calendar_window"],
        )
        route = self.router.route(query, state)
        if route.route_target == "NBABossAgent":
            self.nba_boss.run(state)
        else:
            state.add_fallback("non_nba_request_routed_to_general_help")
            self.nba_boss.run(state)
        update_metrics(state)
        log_event(state, "workflow_complete", metrics=state.metrics)
        return state
