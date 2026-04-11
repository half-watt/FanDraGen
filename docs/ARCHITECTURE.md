# Architecture Notes

## Scenario

The demo dataset represents the final week of the 2024-25 NBA regular season, immediately before fantasy playoffs. This matters because the recommendation logic should feel like late-season decision support: seeding pressure, rest risk, role changes, waiver urgency, and lineup volatility.

## System Shape

The plain Python workflow is the source of truth:

1. route the user query
2. decompose the task in the NBA boss agent
3. call worker agents and tools
4. evaluate quality and grounding
5. allow one revision if needed
6. deliver JSON and markdown
7. mark simulated approval gating when actions are proposed

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

## Future Improvements

- swap the heuristic scorer with a trained model
- add richer roster-need logic
- expand the optional LangGraph mirror into a real runnable graph
- add stricter static analysis in CI
- replace mocked tools with real APIs without changing the state contracts
