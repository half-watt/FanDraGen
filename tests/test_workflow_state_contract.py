"""Test that WorkflowState can be fully serialized and deserialized with all fields populated."""

from schemas.models import WorkflowState, UserQuery, RouteDecision, ToolCallRecord, EvaluationResult, ApprovalStatus, FinalResponse, LogEvent, LeagueContext
from datetime import datetime, timezone

def test_workflow_state_serialization_roundtrip():
    # Populate all fields
    state = WorkflowState(
        original_user_query=UserQuery(text="test query"),
        route_decision=RouteDecision(
            intent="trade evaluation",
            domain="nba",
            route_target="NBABossAgent",
            confidence=0.99,
            reasoning="test"
        ),
        invoked_agents=["RoutingAgent", "NBABossAgent"],
        tool_call_history=[
            ToolCallRecord(
                tool_name="PlayerStatsTool",
                method_name="get_stats",
                arguments={"player": "LeBron James"},
                status="success",
                summary="ok"
            )
        ],
        intermediate_outputs={"draft": {"pick": 1}},
        evaluator_results=[
            EvaluationResult(
                evaluator_name="OutputQualityEvaluator",
                passed=True,
                confidence=1.0
            )
        ],
        fallback_flags=["missing_data"],
        final_delivery_payload=FinalResponse(
            json_payload={"result": "ok"},
            markdown_summary="**ok**"
        ),
        approval_status=ApprovalStatus(approval_required=True, approved=True),
        logs=[
            LogEvent(
                event_type="test",
                agent="TestAgent",
                tool="TestTool",
                status="success",
                message="test log"
            )
        ],
        trace_metadata={"step": "end"},
        league_context=LeagueContext(league_id="nba_league_01", sport="NBA"),
        metrics={"score": 100},
        revision_count=2,
        original_plan=[{"agent": "NBABossAgent", "task_type": "trade evaluation"}]
    )
    # Serialize and deserialize
    data = state.model_dump()
    restored = WorkflowState.model_validate(data)
    assert restored == state
    # Check that all fields survived round-trip
    for field in state.model_fields:
        assert getattr(restored, field) == getattr(state, field)
