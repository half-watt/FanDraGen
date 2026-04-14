# WorkflowState Field Usage and Conventions

This document summarizes the intended usage of all fields in `WorkflowState` (schemas/models.py) for contributors and reviewers.

## Core Fields
- **original_user_query**: The normalized user request (UserQuery model).
- **route_decision**: Output of the routing step (RouteDecision model).
- **invoked_agents**: List of agent names called during the workflow.
- **tool_call_history**: Chronological list of all tool invocations (ToolCallRecord model).
- **intermediate_outputs**: Dictionary for passing structured data between workflow steps. 
  - Typical keys: 'agent_results', 'roster_rows', 'players_by_id', etc.
  - Avoid using as a generic catch-all; document new keys in this file.
- **evaluator_results**: List of all evaluation results (EvaluationResult model).
- **fallback_flags**: List of fallback reasons triggered during the run.
- **final_delivery_payload**: The final output (FinalResponse model).
- **approval_status**: Human checkpoint metadata (ApprovalStatus model).
- **logs**: List of structured log events. Each event should include:
  - timestamp, event name, and details dict.
  - Example events: 'route_decision', 'boss_start', 'tool_call', 'evaluator_result', 'delivery_complete'.
- **trace_metadata**: Dictionary for scenario, mode, and run context.
  - Typical keys: 'mode', 'architecture', 'scenario_name', 'calendar_window', 'live_espn_enrichment_enabled', etc.
  - Avoid storing step-specific data here; use for run-wide metadata only.
- **league_context**: League rules/settings (LeagueContext model).
- **metrics**: Dictionary of numeric metrics for the run.
- **revision_count**: Number of evaluator-driven revisions performed.

## Best Practices
- Prefer explicit, typed fields over generic dicts.
- Document any new keys added to `intermediate_outputs` or `trace_metadata` here.
- Use `logs` for all major state transitions and decisions.
- Keep state transitions and updates easy to trace for debugging and demo purposes.

---

_Last updated: 2026-04-14_
