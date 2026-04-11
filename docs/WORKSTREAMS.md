# Team Workstreams

This project is best split into four workstreams that match how the codebase is already organized. Each person should own one workstream first, then help with integration once their area is stable.

The goal is not to isolate people forever. The goal is to reduce confusion and merge conflicts while the project is still taking shape.

## Workstream 1: System Architecture And Orchestration

### Mission

Own the overall flow of the system so the prototype remains coherent, stateful, and technically sound.

### Primary Folders

- `workflows/`
- `schemas/`
- `agents/boss/`
- `langgraph_optional/`
- parts of `utils/` related to trace and state flow

### What This Person Should Do First

1. Read `docs/ARCHITECTURE.md`.
2. Read `schemas/models.py` closely.
3. Trace one request through `workflows/orchestrator.py` and `agents/boss/nba_boss.py`.
4. Write down any state fields that feel unclear or overloaded before changing them.

### Near-Term Deliverables

- keep `WorkflowState` clean and understandable
- tighten route-to-workflow mapping
- reduce duplication across workflow builders
- improve trace metadata and orchestration logging
- make the optional LangGraph layer mirror the plain Python flow more faithfully

### Final Product Responsibilities

- make sure all major user intents have a clean end-to-end path
- ensure the system has a stable state contract that other teammates can build against
- keep the architecture explainable in a final presentation
- make sure the plain Python path remains the source of truth

### Definition Of Done For This Workstream

- every supported prompt goes through a predictable orchestration path
- shared state is easy to inspect in logs and tests
- boss-agent behavior is documented and covered by tests
- no important flow logic is hidden inside random worker modules

## Workstream 2: Agents And Tools

### Mission

Own the actual reasoning behavior of the system: routing logic, worker agents, tool wrappers, recommendation behavior, and delivery formatting.

### Primary Folders

- `agents/`
- `tools/`
- parts of `utils/` related to metrics or logging if needed

### What This Person Should Do First

1. Read `agents/routing_agent.py`.
2. Read one worker agent fully, then compare it to the others.
3. Read `tools/recommendation_tool.py` and understand the heuristic scoring logic.
4. Run one prompt from `main.py` and inspect the final JSON.

### Near-Term Deliverables

- improve agent-specific rationale quality
- strengthen evaluator feedback and revision behavior
- refine delivery formatting for clarity and consistency
- make tool outputs more structured and easier to ground
- improve recommendation heuristics for draft, lineup, trade, and waivers

### Final Product Responsibilities

- ensure every recommendation is grounded in tool results
- make agent outputs look polished and technically credible
- reduce vague or boilerplate answers
- ensure approval-required actions are always labeled correctly

### Definition Of Done For This Workstream

- each worker agent has a clear purpose and clean inputs and outputs
- tool calls are visible in the trace and attached to agent outputs
- evaluator behavior is meaningful, not decorative
- the final response reads like a serious prototype result, not a placeholder

## Workstream 3: Data / RAG / API

### Mission

Own the realism and future extensibility of the information layer.

Right now this means mock data quality, retrieval quality, and tool readiness for future APIs. Later it can expand into real data integrations, better retrieval, and richer context handling.

### Primary Folders

- `data/nba/` and `data/kaggle/` (NBA stats CSV)
- `tools/league_data_tool.py`
- `tools/player_stats_tool.py`
- `tools/news_tool.py`
- `tools/rules_tool.py`
- `tools/memory_tool.py`

### What This Person Should Do First

1. Read league templates under `data/nba/` and the NBA stats CSV path from `utils/nba_data_source.py`.
2. Check whether the data story feels like the final week before fantasy playoffs.
3. Compare tool methods to the data files they load.
4. Identify fields that would matter if the team later swaps in a real API.

### Near-Term Deliverables

- make demo data more like actual late-season NBA conditions
- expand news, matchup, and standings realism
- add clearer season context and roster context where needed
- make retrieval and lookup logic more robust
- prepare tool interfaces so real APIs can replace local files later with minimal changes

### RAG Scope For This Project

This repo does not yet have a true embedding-based RAG system. In the current prototype, this workstream owns retrieval-like behavior through:

- local news retrieval
- rules retrieval
- roster and matchup retrieval
- future design for richer document or knowledge retrieval if the team adds it

### Final Product Responsibilities

- make the data feel current, believable, and scenario-consistent
- ensure the mock inputs support all demo prompts well
- make the project look ready for API replacement even if APIs are not implemented yet
- document what a future real data pipeline would look like

### Definition Of Done For This Workstream

- demo outputs clearly reflect late-season NBA realities
- the dataset supports strong examples for draft, lineup, trade, waiver, and news tasks
- tool interfaces are stable enough that API integration feels like a next step, not a rewrite
- missing-data and fallback behavior is explicit and testable

## Workstream 4: Training, Eval, Demo, Results

### Mission

Own the quality bar of the project: testing, evaluation behavior, demo polish, metrics, sample outputs, and evidence that the system works.

### Primary Folders

- `tests/`
- `agents/evaluators/`
- `README.md`
- `docs/`
- `main.py`
- `run_demo.ps1`
- `run_tests.ps1`

### What This Person Should Do First

1. Run the full test suite.
2. Run multiple sample prompts.
3. Read the evaluator modules and compare them to actual outputs.
4. Identify which demo prompts feel strongest and weakest.

### Near-Term Deliverables

- add stronger deterministic tests
- improve evaluator coverage and rejection behavior
- clean up demo outputs so they look presentation-ready
- add clearer sample results and benchmark-style metrics summaries
- document known limitations and what still needs strengthening

### Training Scope For This Project

This prototype does not currently train a model. In this workstream, “training” should be interpreted as improving evaluation discipline, experimental rigor, and the path toward future learned components.

### Final Product Responsibilities

- make sure the prototype is stable enough for a live demo
- show evidence that recommendations are grounded and tested
- ensure the final README and demo scripts tell a convincing story
- prepare final results, screenshots, traces, and sample outputs for class presentation

### Definition Of Done For This Workstream

- the demo works reliably from a clean setup
- the test suite covers core behavior and regressions
- evaluators and metrics support claims about system quality
- the project is easy to present to a professor or teammate without code archaeology

## Cross-Team Rules

These workstreams are separate, but some changes will overlap. Use these rules:

1. If you need to change `schemas/models.py`, tell the architecture owner first.
2. If you need to change `data/nba/` or the stats CSV schema, tell the data owner and update tests if behavior changes.
3. If you need to change `README.md` or `docs/`, coordinate with the eval/demo owner.
4. If you need to change a public tool method, notify both the agents/tools owner and the data owner.

## Recommended First Assignments

- System Architecture And Orchestration: simplify workflow task construction and strengthen trace metadata
- Agents And Tools: improve one recommendation path end to end, starting with lineup or trade
- Data / RAG / API: enrich the demo dataset so the outputs feel closer to actual late-season NBA context
- Training, Eval, Demo, Results: add stronger demo assertions and prepare a clean presentation flow
