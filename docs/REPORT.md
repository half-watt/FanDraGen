# FanDraGen: An NBA Fantasy Decision Support System Using a Multi-Agent Orchestration Architecture

---

## Methodology

### Agent Architecture

FanDraGen is built around a hierarchical multi-agent architecture implemented in plain Python. Rather than relying on a third-party LLM framework, the system defines clear agent roles through abstract base classes and explicit inter-agent contracts, making every orchestration decision readable, testable, and traceable.

The agent hierarchy consists of five distinct layers:

**1. RoutingAgent**

The `RoutingAgent` sits at the entry point of every workflow. It classifies incoming user queries against a registry of canonical intents using a keyword-priority matching algorithm. Eight supported intents are ranked in `INTENT_PRIORITY` order, from most specific to most general, so that queries containing overlapping keywords are resolved deterministically. The agent produces a typed `RouteDecision` object containing the matched intent, routing target, confidence score, and a plain-English reasoning string.

**2. NBABossAgent**

Once a route decision is produced, the `NBABossAgent` acts as the orchestration layer. It inherits from `BaseBossAgent`, which defines a single abstract method `run()`. The boss agent is responsible for three things: building the task list from the intent registry, dispatching tasks to the correct worker agents, and running the evaluator–revision loop. It does not implement any business logic itself — it owns control flow, not domain reasoning.

**3. Worker Agents**

Five worker agents handle domain-specific tasks. Each extends `BaseAgent`, which provides a `_start()` registration hook (writing the agent name to `state.invoked_agents` and logging an `agent_start` event) and a `revise()` method for the evaluator feedback loop.

| Agent | Intent(s) Handled |
|---|---|
| `OnboardingAgent` | `onboarding/help` |
| `DraftingAgent` | `draft advice`, `explanation / why reasoning` |
| `ManagingAgent` | `lineup optimization`, `waiver/free agent pickup`, `missing data / fallback explanation` |
| `TradeEvaluationAgent` | `trade evaluation` |
| `NewsSummarizationAgent` | `roster news summary` |

**4. Evaluator Agents**

Two evaluators run after each worker result. `OutputQualityEvaluator` checks structural correctness: it rejects results with summaries shorter than 30 characters, recommendation-style answers missing a structured `Recommendation` object, trade evaluations that omit a computed delta, and results missing rationale. `GroundingEvaluator` checks evidential grounding: it rejects results not backed by at least one `ToolResult`, recommendations without `supporting_evidence`, and fallback-explanation answers that omit explicit assumptions. If either evaluator rejects the result, the boss agent calls `worker.revise()` and re-evaluates, up to two times.

**5. DeliveryAgent**

The `DeliveryAgent` produces the final output — a `FinalResponse` containing both a structured `json_payload` and a readable `markdown_summary`. It also sets `ApprovalStatus` on shared state: if any recommendation carries `approval_required=True`, the proposed action is held at a human-in-the-loop checkpoint and is never automatically executed.

---

### System Workflow and State Management

The orchestration follows a seven-step pipeline, each step explicitly recorded:

```
Route → Plan → Trace Injection → Boss Dispatch → Worker + Evaluate (+ Revise) → Deliver → Metrics
```

1. **Route** — `RoutingAgent` classifies the query and returns a `RouteDecision`.
2. **Plan** — The orchestrator calls `build_tasks_for_route()` against a temporary state to produce the `original_plan` before the live state is constructed.
3. **Trace Injection** — Configuration metadata (mode, architecture, scenario name, calendar window, enrichment flags) is written to `state.trace_metadata`.
4. **Boss Dispatch** — `NBABossAgent.run(state)` decomposes the task list, runs workers, runs evaluators, and calls `DeliveryAgent`.
5. **Evaluate + Revise** — After each worker result, both evaluators run. If feedback is non-empty, `worker.revise()` appends issues to assumptions, strengthens rationale from existing tool outputs, decrements confidence by 0.05, and re-evaluates. The loop terminates after two revisions or when all evaluators pass.
6. **Deliver** — `DeliveryAgent` serializes the result and sets `state.final_delivery_payload`.
7. **Metrics** — `update_metrics()` populates nine counters on `state.metrics`.

**Shared State Contract**

All information produced during a run is stored in a single Pydantic `WorkflowState` object:

| Field | Type | Purpose |
|---|---|---|
| `original_user_query` | `UserQuery` | Normalized incoming request |
| `route_decision` | `RouteDecision` | Intent, domain, target, confidence |
| `invoked_agents` | `list[str]` | Agents called in order |
| `tool_call_history` | `list[ToolCallRecord]` | Every tool call with status and timestamp |
| `intermediate_outputs` | `dict` | Agent scratchpad (roster rows, player IDs, etc.) |
| `evaluator_results` | `list[EvaluationResult]` | Per-attempt evaluation decisions |
| `fallback_flags` | `list[str]` | All fallback reasons, deduplicated |
| `final_delivery_payload` | `FinalResponse` | JSON and markdown output |
| `approval_status` | `ApprovalStatus` | Approval checkpoint metadata |
| `logs` | `list[LogEvent]` | Structured event log |
| `trace_metadata` | `dict` | Ordered workflow steps and mode metadata |
| `metrics` | `dict[str, float]` | Nine evaluation counters |
| `revision_count` | `int` | Evaluator revision loop depth |
| `original_plan` | `list[dict]` | Pre-execution agent plan |

Workers are explicitly prevented from mutating orchestration-owned fields (`route_decision`, `fallback_flags`, `approval_status`, `logs`, `trace_metadata`, `original_plan`). This separation is enforced as a team convention and verified at test time via AST analysis of every worker agent source file.

**Malicious Input Guard**

Before any routing or tool invocation, the orchestrator scans the query for 14 adversarial keyword patterns (SQL injection, data exfiltration, privilege escalation, destructive commands, phishing, prompt injection). Any match triggers an immediate short-circuit: a `FinalResponse` with `"blocked": True` is returned, `task_completion_rate` is set to `0.0`, and the `blocked_malicious_input` flag is recorded. No agent or tool is invoked.

---

### Tool Integration

FanDraGen defines five tools, each extending `BaseTool`, which provides a `_record()` method that appends a typed `ToolCallRecord` to `state.tool_call_history` after every invocation.

**RecommendationTool**

The core scoring and recommendation engine. Its `_score_player()` method implements a weighted multi-factor heuristic:

$$s = 0.48p + 0.24r + 0.11(\sigma + \delta_n) \cdot 10 + 0.09(6 - m) \cdot 2.5 - 4.2I - 0.35P_s$$

Where:
- $p$ = projected points (Kaggle season average, or nba_api last-10 blended value when enrichment is active)
- $r$ = recent points average
- $\sigma$ = base sentiment score
- $\delta_n$ = news-feed sentiment delta
- $m$ = matchup difficulty (1–5 scale)
- $I$ = injury flag (0 or 1)
- $P_s$ = status penalty: 0.0 (healthy), 2.0 (probable), 5.5 (questionable), 12.0 (out/doubtful)

The tool exposes `rank_players()`, `recommend_draft_pick()`, `recommend_waiver_pickup()`, `suggest_lineup()`, and `evaluate_trade()`. Player names are resolved through a four-level cascade: exact match → Unicode-normalized match → substring fuzzy match → ranked-position fallback. Each fallback level writes a typed flag to `state.fallback_flags` for auditability.

**PlayerStatsTool**

Loads player rows from the Kaggle CSV and optionally enriches them with live nba_api PlayerGameLog data (`FANDRAGEN_NBA_API=1`) or ESPN standings context (`FANDRAGEN_LIVE_ESPN=1`). Returns a `ToolResult` with row data, supporting points, and a summary string.

**LeagueDataTool**

Reads local league files: roster assignments, free-agent pool, weekly matchups, standings, and scoring rules. Each method returns a `ToolResult` with missing-field detection.

**NewsTool**

Reads `data/nba/news.json` and returns news items for a given list of player names. The schema exposes `headline`, `narrative`, `status`, `injury_detail`, `team`, and `stat_projection`.

**External Integrations (Optional)**

Two optional integrations can be enabled by environment variable:
- `integrations/espn_nba.py` — fetches live headlines and standings from ESPN's public JSON API using only `urllib` (no API key required).
- `integrations/nba_api_stats.py` — fetches per-player game logs from the `nba_api` library and merges `nba_pts_last10_avg`, `nba_reb_last10_avg`, `nba_ast_last10_avg`, and an `effective_projected_points` blended field into the player row.

Both integrations are off by default in mocked mode and off in all test runs.

---

### Data

**Primary Dataset — Kaggle NBA Player Stats 2024-25**

The main data source is the Kaggle dataset *NBA Player Stats Season 24/25* (Eduardo Palmieri, 2025), loaded from `data/kaggle/nba_player_stats_2425.csv`. The raw CSV is in game-log format — one row per player per game. The loader (`utils/kaggle_nba_loader.py`) detects this format automatically and aggregates rows per player, computing per-game averages for points, rebounds, assists, and minutes. After aggregation the dataset contains **561 unique players**. Column headers are matched through a normalized alias dictionary to handle naming variants (`pts`, `points`, `ppg` all resolve to the same internal column).

**League Template Data**

Seven local files under `data/nba/` define the fantasy league context:

| File | Contents |
|---|---|
| `roster_template.csv` | 24 roster slots for `team_001`, mapped to top-ranked players |
| `free_agents_template.csv` | Available free-agent pool |
| `matchups.csv` | Current week's head-to-head matchups |
| `standings.csv` | League standings |
| `news.json` | Player news items (headline, narrative, status, injury detail) |
| `league_rules.json` | Scoring settings, roster slots, trade and waiver notes |
| `season_context.json` | Scenario description, calendar window, narrative signals |

The scenario is fixed at the final week of the 2024-25 NBA regular season (April 7–13, 2025), immediately before the fantasy playoff bracket, providing a realistic late-season decision context: rest risk for locked seeds, must-win games for play-in bubble teams, waiver urgency, and lineup volatility.

**Test Fixture**

All tests run against `tests/fixtures/kaggle_minimal.csv`, a synthetic 30-row table with known player IDs, positions, and ordered projected-point values. The top player (`kg_00001`, "Top Player Omega") carries a known NBA person ID (`203507`) to exercise the nba_api merge path. The fixture is injected by overriding `FANDRAGEN_KAGGLE_NBA_CSV` in `conftest.py`, completely isolating the test suite from the 561-player production CSV.

---

### Evaluation Metrics

Nine metrics are computed at the end of every workflow run and stored on `state.metrics`:

| Metric | Definition | Ideal Value |
|---|---|---|
| `task_completion_rate` | 1.0 if `final_delivery_payload` is not None | 1.0 |
| `routing_accuracy` | 1.0 if route target is `NBABossAgent` | 1.0 |
| `tool_invocation_correctness` | 1.0 if at least one tool was called | 1.0 |
| `evaluator_rejection_rate` | Fraction of evaluator runs that failed | 0.0 |
| `revision_success_rate` | 1.0 if revision loop converged in ≤1 cycle | 1.0 |
| `response_grounding_coverage` | 1.0 if any tool call succeeded | 1.0 |
| `deterministic_consistency` | Fixed at 1.0 (deterministic router) | 1.0 |
| `fallback_event_count` | Count of tool calls that used a fallback | 0 |
| `approval_checkpoint_count` | 1 if an approval gate was raised, else 0 | Intent-dependent |

Evaluator confidence per attempt: `OutputQualityEvaluator` reports 0.82 on pass and 0.67 on fail; `GroundingEvaluator` reports 0.80 on pass and 0.65 on fail. Worker agents emit fixed per-agent confidence values: `DraftingAgent` (0.84), `NewsSummarizationAgent` (0.86), `ManagingAgent` waiver path (0.81), `TradeEvaluationAgent` (0.76), `ManagingAgent` fallback path (0.79). Confidence decrements by 0.05 per revision cycle.

---

## Implementation and Results

### Experimental Setup

All experiments were conducted on a Windows 11 machine using Python 3.11.9 inside a project-local virtual environment (`.venv/`). The system operated in **mocked mode** (`mode: "mocked"`, `architecture: "plain_python"`) as configured in `configs/default_config.yaml`. All three optional enrichment integrations were disabled: no `GEMINI_API_KEY`, no `FANDRAGEN_LIVE_ESPN`, no `FANDRAGEN_NBA_API`. The production Kaggle CSV (`data/kaggle/nba_player_stats_2425.csv`) was present and used for all demo runs; tests ran against the 30-row synthetic fixture.

Run commands:
- Test suite: `./run_tests.ps1` (invokes `pytest tests/ -v`)
- Demo: `./run_demo.ps1 -Sample N` for N = 0–7 (invokes `main.py --sample N`)

All outputs were captured to `artifacts/demo_runs/`.

---

### Testing Cases

The test suite comprises **48 tests across 21 test files** in four categories:

**End-to-End Integration (8 cases)** — The full 8-prompt demo set run parametrically through `WorkflowOrchestrator.run()`. These are the exact prompts used in the live demo.

**Safety and Robustness (10 cases)** — Ten adversarial inputs covering SQL injection, prompt injection, data exfiltration, privilege escalation, destructive commands, and phishing.

**Functional Unit Tests (20 cases)** — Routing, intent registry mapping, boss decomposition, worker fallback, evaluator rejection criteria, delivery output format, and tool determinism.

**Contract and Structural Tests (10 cases)** — Trace step ordering, log event content, state serialization round-trip (`model_dump` / `model_validate`), and static AST analysis of worker agent state mutation.

The 8 demo prompts and the intents they target:

| Sample | Prompt | Intent |
|:---:|---|---|
| 0 | "I am new to fantasy basketball. How does this league work?" | onboarding/help |
| 1 | "Who should I draft first from the available player pool?" | draft advice |
| 2 | "Set my best lineup for this week." | lineup optimization |
| 3 | "Should I trade Player A for Player B?" | trade evaluation |
| 4 | "Who is the best waiver pickup right now?" | waiver/free agent pickup |
| 5 | "Summarize important news for my roster." | roster news summary |
| 6 | "Why did you rank these players this way?" | explanation / why reasoning |
| 7 | "What assumptions are you making because data is missing?" | missing data / fallback explanation |

---

### Testing Results

**Test Suite**

All 48 tests pass. One non-blocking deprecation warning is emitted from `test_workflow_state_contract.py` related to Pydantic's `model_fields` introspection API. It does not affect correctness and is noted for a future Pydantic migration update.

**Demo Run Results**

All 8 demo samples executed to completion with no uncaught exceptions. Artifacts are captured in `artifacts/demo_runs/`.

| Sample | Intent | Route Conf. | Output Conf. | Approval Required | Fallback Flags | Revisions | Tool Calls |
|:---:|---|:---:|:---:|:---:|---|:---:|:---:|
| 0 | onboarding/help | 0.78 | — | No | — | 0 | 0 |
| 1 | draft advice | 0.90 | 0.83 | Yes | — | 0 | 3 |
| 2 | lineup optimization | 0.90 | 0.81 | Yes | — | 0 | 3 |
| 3 | trade evaluation | 0.90 | 0.76 | Yes | — | 0 | 2 |
| 4 | waiver/free agent pickup | 0.90 | 0.81 | Yes | — | 0 | 3 |
| 5 | roster news summary | 0.90 | 0.86 | No | — | 0 | 2 |
| 6 | explanation / why reasoning | 0.90 | 0.84 | No | — | 0 | 2 |
| 7 | missing data / fallback | 0.90 | **0.69** | No | `missing_projection_source_local_mode` | **2** | 0 |

Routing confidence was 0.90 for all specific intents and 0.78 for the onboarding query, consistent with the router's intentional lower-confidence tier for the catch-all `onboarding/help` intent. Output confidence was highest for informational paths (news summary: 0.86, explanation: 0.84) and lowest for the fallback path (0.69), reflecting the 0.05-per-cycle confidence penalty applied by the revision loop.

**Sample 3 — Trade Evaluation**

The `TradeEvaluationAgent` resolved "Player A" and "Player B" to their configured aliases (LeBron James and Nikola Jokić) via `NBAPlayerContextHelper`, fetched stat rows for both via `PlayerStatsTool`, and called `RecommendationTool.evaluate_trade()`. The heuristic score for Nikola Jokić was 36.98 versus 29.53 for LeBron James, yielding a net delta of +7.45 in favor of accepting the trade. The result was delivered with `approval_required=true` and the proposed action held at the checkpoint without execution.

**Sample 7 — Fallback / Revision Loop**

The `ManagingAgent` recognized the `"missing data / fallback explanation"` task type, populated `state.fallback_flags` with `"missing_projection_source_local_mode"`, and returned a result explaining the system's data source assumptions. Both evaluators ran; `GroundingEvaluator` flagged that no tool outputs were attached and that the explanation did not reference tool evidence explicitly. After two revision cycles the issues remained unresolved — the fallback path has no tool calls to surface — and the evaluator feedback was surfaced transparently in the final output's `assumptions` and `rationale` fields. Output confidence dropped to 0.69 after two 0.05 decrements. This is expected and intentional behavior: the system makes its own uncertainty visible rather than suppressing it.

**Bugs Identified and Resolved During Development**

Five runtime issues were identified and fixed during the evidence-capture run. None were detected by the pre-existing test suite because all affected the live demo path while tests isolated or mocked the impacted components:

| # | Error | Root Cause | Fix Applied |
|---|---|---|---|
| 1 | `KeyError: 'LeBron James'` | `evaluate_trade()` used direct dict lookup; exact string key from alias resolution did not match CSV casing | Added `_normalize_player_name()` (Unicode NFKD fold, casefold, ASCII-only) and `_resolve_trade_player()` with four-level matching cascade |
| 2 | `TypeError: 'LogEvent' object is not subscriptable` | `test_boss_agent.py` and `logging_utils.py` used `entry["event"]` dict syntax on a typed Pydantic `LogEvent` object after an API migration | Updated both files to attribute access: `entry.event_type`, `entry.details` |
| 3 | `KeyError: 'sentiment_delta'` | `_news_delta()` assumed a `sentiment_delta` field in `news.json`; the local schema does not include that field | Changed to `item.get("sentiment_delta", 0.0)` with safe `float()` conversion |
| 4 | `KeyError: 'summary'` | `news_summarization_agent.py` read `item['summary']`; the news schema uses `headline` and `narrative` | Changed to `item.get('headline') or item.get('narrative') or fallback string` |
| 5 | `UnicodeEncodeError` on accented characters | Windows PowerShell default encoding (cp1252) cannot encode Unicode characters in names like Jokić or Dončić | Added `stdout.reconfigure(encoding="utf-8", errors="replace")` guard in `main.py` |

---

### Testing Limitations

**Mocked mode only.** All 48 tests and all 8 demo artifacts were produced with live enrichment disabled. The ESPN and nba_api code paths were validated only through their dedicated mock-patched tests, not through end-to-end demo execution.

**Heuristic scorer is unvalidated against outcomes.** The `_score_player()` formula uses manually tuned coefficients derived from fantasy basketball conventions. There is no training set, no held-out validation, and no comparison against actual fantasy results. The formula produces correct relative ordering but no validated absolute accuracy.

**Test prompts are fixed and literal.** Behavior on paraphrased, multilingual, or syntactically varied queries has not been tested. The keyword router is known to be brittle against novel phrasing that does not contain a recognized keyword verbatim.

**Static mutation test is incomplete.** `test_worker_agent_state_mutation.py` checks for direct assignment patterns on a fixed list of forbidden fields. It does not detect in-place mutation through method calls such as `state.fallback_flags.append(...)`.

**Confidence values are fixed constants.** Worker agent confidence values are hard-coded per agent. They are not derived from a probabilistic model and convey relative ranking across agents rather than calibrated probability estimates.

---

## Discussion and Error Analysis

### Successes

**Explicit state made debugging fast.** Every bug encountered during the evidence run was diagnosed entirely from the `WorkflowState` object — trace metadata, fallback flags, tool call history, and log events formed a complete audit trail without a debugger or print-statement instrumentation. The architecture is legible to a new contributor within a single reading of `orchestrator.py` and `schemas/models.py`.

**Deterministic routing was consistent across all runs.** The keyword-priority router produced identical routing decisions across all 48 tests and all 8 demo samples. Routing confidence was 0.90 for all non-onboarding intents on every run. The `test_intent_mapping.py` completeness checks guard against the most common extension mistake — adding an intent to one registry table but not the others.

**State contract enforcement caught a breaking change in real time.** The migration of `WorkflowState.logs` from `list[dict]` to `list[LogEvent]` was immediately flagged by the `test_workflow_state_contract.py` serialization round-trip test, and the `TypeError` runtime failures confirmed which files had not been updated. The contract test functions as a structural guardrail for the shared state schema.

**Evaluator transparency was preserved under failure.** When the grounding evaluator could not be satisfied on the fallback path (Sample 7), the system surfaced the unresolved issues in the final output's `assumptions` and `rationale` fields rather than silently downgrading the answer. This is more honest than a system that masks its own uncertainty, and it demonstrates that the evaluation layer functions correctly even in the adversarial case where no tool evidence is available.

**Zero regressions across five live code changes.** After each of the five source file patches applied during the evidence run, the full 48-test suite was re-run before proceeding. All tests continued to pass after every individual fix, confirming meaningful regression coverage across the core workflow paths.

---

### Challenges

**Schema drift between the test path and the live data path.** The most impactful category of bugs involved field name mismatches between what the code assumed and what the local data files actually provided. `news.json` uses `headline` and `narrative`; the agent code assumed `summary`. The scoring code assumed a `sentiment_delta` field the file does not have. These were invisible to the test suite because the test fixture data was isolated from the production data files, and mock data always returned safe defaults that never triggered the missing-key branches. The root problem is that the test isolation strategy — overriding the CSV path — isolates only player data, not the news feed, scoring fields, or any other local file.

**Player name resolution across heterogeneous data sources.** Player names exist simultaneously in at least four forms: the Kaggle CSV column value, the alias dictionary entry, the news feed's `player_name` field, and the user query text. Unicode accented characters, full legal versus common names, and alias substitutions all need to be resolved at a single point in the tool layer. The initial implementation used direct dictionary lookup and failed on any name not byte-for-byte identical to the CSV value. Resolution required building a four-level fallback chain with Unicode NFKD normalization and ASCII casefold, adding meaningful complexity to a function most engineers would expect to be trivial.

**LogEvent API contract break was silent.** The migration of `WorkflowState.logs` from `list[dict]` to `list[LogEvent]` passed import-time checks but raised `TypeError` at runtime when dict-subscript access was reached. The break was not caught by the test suite because the affected code paths were not exercised by the tested prompts or lived in utility functions reached only through stubs.

---

### Limitations

**No live language model.** In mocked mode, agent reasoning is entirely template-driven. The `revise()` method in `BaseAgent` appends evaluator feedback text and copies existing tool summaries — it does not generate novel language. Gemini enrichment is available as an optional step but was inactive during all reported runs. The system demonstrates orchestration correctness, not the output quality a live LLM integration would produce.

**Heuristic scoring has no validation.** The `_score_player()` formula produces scores with relative ordering validity within a single run but no validated absolute accuracy. The formula is not derived from a learned model and uses manually set coefficients. The tool interface is designed to allow the scorer to be replaced without changing calling code, but the replacement has not been built.

**Approval gating is informational only.** The system correctly marks proposed actions as `action_not_executed: true` but there is no persistent queue, user callback, or confirmation flow. The approval checkpoint is a design statement rather than a functional safety control.

**Intent coverage is narrow and routing is brittle.** Eight intents are supported; routing is keyword-based. It does not handle multi-intent queries, negation, paraphrase variation, or domain shifts. Adding a new intent requires synchronizing four separate structures, creating an extension surface that is error-prone without the completeness tests to catch mistakes.

**Single-tenant, single-league design.** All data and logic is scoped to a single league and team. There is no multi-user session management, authentication, or per-user state isolation. The system would require significant architectural work to support multiple concurrent users.

---

## Conclusion and Future Directions

### Summary

FanDraGen successfully demonstrates a multi-agent orchestration architecture for NBA fantasy decision support. The system accepts user queries in natural language, routes them deterministically to a domain-specific boss agent, decomposes them into typed worker tasks, invokes a heuristic scoring engine against a real 561-player NBA season dataset, evaluates the quality and evidential grounding of worker outputs through two independent evaluators, executes a revision loop when evaluation fails, and delivers structured JSON and human-readable Markdown with human-in-the-loop approval gating on all action-type recommendations.

All 48 tests pass across 21 test files covering routing, intent registry completeness, boss agent decomposition, worker fallback, evaluator correctness, delivery formatting, trace fidelity, state contract stability, static code analysis, data loading, malicious input blocking, and mocked external API integration. All 8 supported intent paths executed end-to-end with no uncaught exceptions.

Five runtime issues were identified and resolved during the evidence-capture session. All five — a player name resolution failure, two `LogEvent` API contract breaks, and two data schema mismatches — were caught by the live demo path and not by the existing test suite. This reveals a meaningful gap between test-path coverage and demo-path coverage in the current fixture design, which represents the highest-priority item for the next development cycle.

The architecture achieves its primary design goals: state is fully explicit and auditable, module boundaries are enforced, agent behavior is inspectable via structured logs and trace metadata, and the system degrades gracefully under missing data, unknown intents, and unresolvable grounding issues rather than crashing or returning silent errors.

---

### Future Work

**Replace the heuristic scorer with a trained model.** The `_score_player()` formula is isolated to a single method with a stable interface, designed explicitly to be replaceable. A gradient-boosted tree trained on historical fantasy scoring outcomes with the same input features would improve prediction accuracy without requiring changes to any calling code. The weights currently assigned to projected points (0.48), recent form (0.24), sentiment (0.11), and matchup difficulty (0.09) could be derived from regression rather than set by hand.

**Enable live API enrichment in a validated configuration.** The ESPN and nba_api integrations are wired and tested in isolation but were not active in the reported runs. An integration test suite running against live endpoints with known fallback assertions, paired with a nightly CI job monitoring for schema changes, would enable these paths to be activated confidently.

**Replace the keyword router with an intent classifier.** A sentence-embedding classifier or fine-tuned small language model could replace the keyword-priority router, enabling the system to handle paraphrased queries, negation, multi-intent requests, and domain shifts without manual keyword list maintenance. The `RouteDecision` schema already carries a `confidence` field designed to accommodate probabilistic routing.

**Add a real approval workflow.** A lightweight persistent queue — even a local SQLite table — could hold pending recommendations across sessions. Adding a `POST /approve/<action_id>` endpoint to `web/app.py` would close the loop between recommendation and execution, making the approval checkpoint a functional safety control.

**Broaden intent coverage and data realism.** The current eight intents omit category-specific streaming, playoff scheduling optimization, keeper trade valuation, and league standings simulation. The local league data would benefit from a semi-automated weekly refresh pipeline that populates files from real box scores rather than relying on static templates.

**Close the test-versus-demo fixture gap.** The highest-priority near-term testing improvement is expanding `tests/fixtures/kaggle_minimal.csv` and associated mock data to include the full news schema, sentiment fields, and all column variants present in the production data files. This would allow `test_end_to_end.py` to catch the class of schema mismatch bugs that required manual demo-run debugging in this cycle.

**Add a continuous integration pipeline.** A GitHub Actions workflow running `./run_tests.ps1` on every pull request and blocking merges on test failure would prevent regressions from reaching the demo branch. The `test_intent_mapping.py` completeness check and `test_worker_agent_state_mutation.py` static analysis are particularly valuable in CI — they catch structural mistakes that do not produce import errors and would otherwise slip through code review undetected.
