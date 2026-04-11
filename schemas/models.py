"""Pydantic models that define FanDraGen shared state.

The project intentionally keeps workflow state explicit. Every routing decision,
tool call, evaluator output, and delivery artifact is represented here so the
demo can clearly show how state moves through the system.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class UserQuery(BaseModel):
    """Normalized representation of the incoming user request."""

    text: str
    sport: str = "NBA"
    user_id: str = "demo_user"
    league_id: str = "nba_league_01"
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RouteDecision(BaseModel):
    """Structured output of the routing step."""

    intent: str
    domain: Literal["nba", "general"]
    route_target: str
    confidence: float
    reasoning: str


class AgentTask(BaseModel):
    """Unit of work created by a boss agent for a worker or helper."""

    task_type: str
    description: str
    assigned_agent: str
    input_payload: dict[str, Any] = Field(default_factory=dict)
    requires_tools: list[str] = Field(default_factory=list)


class ToolCallRecord(BaseModel):
    """Log entry for a tool invocation."""

    tool_name: str
    method_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    status: Literal["success", "fallback", "error"] = "success"
    summary: str = ""
    fallback_used: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ToolResult(BaseModel):
    """Structured result returned from a tool."""

    tool_name: str
    method_name: str
    data: Any
    supporting_points: list[str] = Field(default_factory=list)
    fallback_used: bool = False
    missing_fields: list[str] = Field(default_factory=list)
    summary: str = ""
    enrichment: dict[str, Any] | None = None


class LeagueContext(BaseModel):
    """League rules and settings loaded for reasoning."""

    league_id: str
    sport: str
    team_id: str = "team_001"
    roster_slots: list[str] = Field(default_factory=list)
    scoring_settings: dict[str, float | int | str] = Field(default_factory=dict)
    trade_notes: str = ""
    waiver_notes: str = ""
    lineup_lock_assumptions: str = ""


class Recommendation(BaseModel):
    """Canonical recommendation payload used across intents."""

    item_id: str
    title: str
    details: str
    confidence: float
    score: float
    action_type: str
    approval_required: bool = False
    proposed_action: str | None = None
    action_not_executed: bool = True
    rationale: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)


class AgentResult(BaseModel):
    """Structured response from a worker agent."""

    agent_name: str
    summary: str
    confidence: float
    rationale: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    supporting_tool_results: list[ToolResult] = Field(default_factory=list)
    structured_payload: dict[str, Any] = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    """Evaluator decision for a given workflow attempt."""

    evaluator_name: str
    passed: bool
    confidence: float
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    attempt_number: int = 1


class ApprovalStatus(BaseModel):
    """Human checkpoint metadata for recommendation-style outputs."""

    approval_required: bool = False
    approved: bool | None = None
    proposed_action: str | None = None
    action_not_executed: bool = True
    checkpoint_reason: str = "No approval required."


class FinalResponse(BaseModel):
    """Delivered output in both machine-readable and markdown forms."""

    json_payload: dict[str, Any]
    markdown_summary: str


class WorkflowState(BaseModel):
    """Shared explicit state for the full workflow."""

    original_user_query: UserQuery
    route_decision: RouteDecision | None = None
    invoked_agents: list[str] = Field(default_factory=list)
    tool_call_history: list[ToolCallRecord] = Field(default_factory=list)
    intermediate_outputs: dict[str, Any] = Field(default_factory=dict)
    evaluator_results: list[EvaluationResult] = Field(default_factory=list)
    fallback_flags: list[str] = Field(default_factory=list)
    final_delivery_payload: FinalResponse | None = None
    approval_status: ApprovalStatus = Field(default_factory=ApprovalStatus)
    logs: list[dict[str, Any]] = Field(default_factory=list)
    trace_metadata: dict[str, Any] = Field(default_factory=dict)
    league_context: LeagueContext | None = None
    metrics: dict[str, float | int] = Field(default_factory=dict)
    revision_count: int = 0

    def log(self, event: str, details: dict[str, Any]) -> None:
        """Append a structured log event to state."""

        self.logs.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": event,
                "details": details,
            }
        )

    def add_fallback(self, reason: str) -> None:
        """Record a fallback reason once."""

        if reason not in self.fallback_flags:
            self.fallback_flags.append(reason)
