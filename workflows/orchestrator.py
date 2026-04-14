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
            from utils.trace_utils import record_workflow_step
            record_workflow_step(state, "dispatch_boss_agent", route_target=route_target)
            log_event(
                state,
                event_type="route_target_dispatched",
                agent="WorkflowOrchestrator",
                tool="N/A",
                status="success",
                message=f"Route target {route_target} dispatched successfully.",
                details={"route_target": route_target},
            )
            self.nba_boss.run(state)
            return
        state.add_fallback(f"unsupported_route_target:{route_target}")
        from utils.trace_utils import record_workflow_step
        record_workflow_step(state, "route_target_fallback", route_target=route_target)
        log_event(
            state,
            event_type="route_target_fallback",
            agent="WorkflowOrchestrator",
            tool="N/A",
            status="warning",
            message=f"Route target {route_target} not supported, falling back to NBABossAgent.",
            details={"route_target": route_target, "fallback_target": "NBABossAgent"},
        )
        self.nba_boss.run(state)

    def run(self, query_text: str) -> WorkflowState:
        load_env()
        query = UserQuery(text=query_text)
        # Build the plan before creating the state
        from workflows.intent_registry import build_tasks_for_route
        temp_state = WorkflowState(original_user_query=query)
        planned_route = self.router.route(query, temp_state)
        from utils.trace_utils import record_workflow_step
        record_workflow_step(temp_state, "route_decision", intent=planned_route.intent, route_target=planned_route.route_target)
        temp_state.route_decision = planned_route
        planned_tasks = build_tasks_for_route(temp_state)
        plan = []
        for task in planned_tasks:
            plan.append({
                "agent": task.assigned_agent,
                "task_type": task.task_type,
                "tools": task.requires_tools,
                "description": task.description,
            })
        state = WorkflowState(original_user_query=query, original_plan=plan)
        # Merge workflow_steps from temp_state into state
        temp_steps = temp_state.trace_metadata.get("workflow_steps", [])
        if temp_steps:
            if "workflow_steps" not in state.trace_metadata:
                state.trace_metadata["workflow_steps"] = []
            state.trace_metadata["workflow_steps"].extend(temp_steps)
        # Malicious input detection (simple keyword-based for now)
        MALICIOUS_KEYWORDS = [
            "drop table", "leak", "hack", "admin access", "sql injection", "bypass", "delete everything", "raw database", "phishing", "cheat", "exploit", "ignore previous instructions", "dangerous", "unsafe", "malicious"
        ]
        lowered = query_text.lower()
        if any(kw in lowered for kw in MALICIOUS_KEYWORDS):
            # Block and return explicit payload
            state.final_delivery_payload = __import__("schemas.models", fromlist=["FinalResponse"]).FinalResponse(
                json_payload={
                    "blocked": True,
                    "summary": "Blocked: Malicious or unsafe input detected. No action taken.",
                },
                markdown_summary="**Blocked:** Malicious or unsafe input detected. No action taken."
            )
            state.metrics["task_completion_rate"] = 0.0
            state.add_fallback("blocked_malicious_input")
            record_workflow_step(state, "blocked_malicious_input")
            log_event(
                state,
                event_type="blocked_malicious_input",
                agent="WorkflowOrchestrator",
                tool="N/A",
                status="error",
                message="Blocked malicious or unsafe input.",
                details={"query": query_text},
            )
            return state
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
        record_workflow_step(state, "trace_metadata_injected")
        # Set the route_decision on the real state
        state.route_decision = planned_route
        self._dispatch_route_target(planned_route.route_target, state)
        record_workflow_step(state, "boss_agent_dispatched", route_target=planned_route.route_target)
        update_metrics(state)
        record_workflow_step(state, "metrics_updated")
        log_event(
            state,
            event_type="workflow_complete",
            agent="WorkflowOrchestrator",
            tool="N/A",
            status="success",
            message="Workflow complete.",
            details={"metrics": state.metrics},
        )
        return state
