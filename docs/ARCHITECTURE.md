# Architecture Notes

## Scenario

The demo dataset represents the final week of the 2024-25 NBA regular season, immediately before fantasy playoffs. This matters because the recommendation logic should feel like late-season decision support: seeding pressure, rest risk, role changes, waiver urgency, and lineup volatility.


## System Shape: Orchestration Flow

The workflow is implemented in plain Python, with all major steps explicit and test-validated:

1. **Route the user query** (via `RoutingAgent` and canonical intent registry)
2. **Decompose the task** in the NBA boss agent (assigns worker agents and tools)
3. **Call worker agents and tools** (task execution, tool invocation, and result collection)
4. **Evaluate quality and grounding** (evaluator agents check outputs)
5. **Allow one revision if needed** (revision loop, if evaluation fails)
6. **Deliver JSON and markdown** (final response is structured and human-readable)
7. **Mark simulated approval gating** when actions are proposed (approval status in state)

### Orchestration Trace, Logging, and Metadata

- Every major orchestration step records a trace metadata entry (`trace_metadata['workflow_steps']`)
- Structured logs (`logs` field, `LogEvent` objects) are appended for all key events (dispatch, fallback, completion, errors)
- Trace and logs are test-validated for coverage and order (see `test_trace_metadata.py`, `test_orchestration_logging.py`)

### State Contract Enforcement and Testing

- `WorkflowState` is the explicit contract for all orchestration, agent, and tool state
- All fields are documented and type-checked (see `schemas/models.py`)
- A dedicated test (`test_workflow_state_contract.py`) ensures the state can be fully serialized/deserialized with all fields populated, guarding against contract drift

### How to Extend the System

To add a new user intent or workflow:
1. Add the intent and keywords to `workflows/intent_registry.py` (`INTENT_KEYWORDS`)
2. Add the intent to `INTENT_PRIORITY` in the desired order
3. Map the intent to a workflow builder in `INTENT_TO_WORKFLOW`
4. Implement the workflow builder (see `workflows/`)
5. Add or update tests to cover the new path

To add a new agent or tool:
1. Implement the agent/tool in the appropriate folder (`agents/`, `tools/`)
2. Register the agent/tool in the relevant workflow builder
3. Update tests and documentation as needed

All changes to state contracts or orchestration logic should be accompanied by updated tests and, if needed, doc updates.

## Why Shared State Is Explicit

This project is meant for a team and for a class demo. Hidden state would make it harder to debug and harder for a new teammate to follow. `WorkflowState` is the contract for everything important that happens in the run.

## Team-Friendly Module Boundaries

- `schemas/` defines contracts. Change carefully.
- `tools/` defines external data access and scoring seams.
- `agents/general/` contains task-specific behavior.
- `agents/boss/` owns orchestration, not business detail.
- `agents/evaluators/` controls answer quality and grounding.
- `agents/delivery/` controls final output shape.
- `workflows/` maps intents to tasks.

## Orchestration Contracts (Workstream 1)

- Canonical intent keywords and priority now live in `workflows/intent_registry.py`.
- `agents/routing_agent.py` imports those canonical definitions so routing and task-building stay in sync.
- `workflows/intent_registry.py` uses a table-driven mapping (`intent -> workflow builder`) instead of a long conditional chain.
- Unknown intents are handled by one explicit fallback task and a fallback flag (`unknown_intent:<intent>`) for traceability.
- `workflows/orchestrator.py` routes known boss targets directly and logs deterministic fallback dispatch for unsupported targets.
- `agents/boss/nba_boss.py` guards against missing worker assignments and falls back to a safe explanation task instead of crashing.

## Future Improvements

- swap the heuristic scorer with a trained model
- add richer roster-need logic
- add stricter static analysis in CI
- replace mocked tools with real APIs without changing the state contracts
