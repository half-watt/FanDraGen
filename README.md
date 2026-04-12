# FanDraGen

FanDraGen is a research-grade, local-first NBA fantasy sports assistant scaffold. It demonstrates multi-agent orchestration, explicit shared state, tool usage, evaluator behavior, fallback handling, simulated approval checkpoints, and traceability. **Player stats come from a required Kaggle-format NBA season CSV** (see `data/kaggle/` and `utils/nba_data_source.py`). League structure (rules, matchups, roster slot pattern) lives under **`data/nba/`**. **Optional integrations** can enrich outputs: public ESPN JSON (no key) and an optional Gemini API key for natural-language polish that still relies on attached tool evidence.

The implementation is plain Python end to end.

The current mock scenario is the final week of the 2024-25 NBA regular season, immediately before fantasy playoffs begin. That gives the demo a clear late-season context instead of a generic basketball dataset.

## Latest Sprint Update (Workstream 1)

- centralized canonical intent keywords and priority in `workflows/intent_registry.py`, with `agents/routing_agent.py` importing from that source
- replaced route-to-workflow condition chains with table-driven intent mapping plus explicit unknown-intent fallback logging
- reduced duplication across workflow builders using shared helper in `workflows/task_builder.py`
- tightened orchestrator route-target fallback metadata in `workflows/orchestrator.py`
- added boss-agent guardrails for missing worker assignments in `agents/boss/nba_boss.py`
- extended coverage in `tests/test_intent_registry.py` and `tests/test_boss_agent.py`
- validated full suite in project venv: 31 passed

## Purpose

This project is a class-demo prototype, not a production application. It intentionally excludes authentication, real platform account actions, production deployment, and multi-sport scope beyond a minimal NBA-specific reasoning layer. A **local Streamlit UI** (`web/app.py`) is included for demos; it does not change league accounts.

## Architecture Overview

The main workflow is:

User Query -> Routing Agent -> NBA Boss Agent -> Worker Agents / Tools -> Evaluation Agents -> Delivery Agent -> Human Approval Checkpoint

The system keeps state explicit through `WorkflowState` in `schemas/models.py`. That state stores the original query, route decision, invoked agents, tool call history, intermediate outputs, evaluator results, fallback flags, final delivery payload, approval status, trace metadata, logs, and demo metrics.

### Core Components

- `agents/routing_agent.py`: Deterministic intent classification and NBA-domain routing.
- `agents/boss/nba_boss.py`: Task decomposition, worker selection, aggregation, evaluator loop, and final delivery.
- `agents/general/*`: Worker agents for onboarding, drafting, lineup and waiver management, trade evaluation, and roster news.
- `agents/nba/*`: Minimal NBA helper layer for roster rules, matchup interpretation, and demo alias resolution.
- `agents/evaluators/*`: Moderately strict quality and grounding evaluators with one retry.
- `agents/delivery/delivery_agent.py`: Formats final JSON and markdown output and marks simulated approval requirements.
- `tools/*`: Mocked tool wrappers for league data, stats, news, rules, recommendations, and local memory.
- `workflows/*`: Intent-specific workflow builders and the main orchestrator.

## Folder Structure

```text
FanDraGen/
  agents/
    base.py
    routing_agent.py
    boss/
      base_boss.py
      nba_boss.py
    general/
      onboarding_agent.py
      drafting_agent.py
      managing_agent.py
      trade_evaluation_agent.py
      news_summarization_agent.py
    nba/
      nba_rules_interpreter.py
      nba_player_context_helper.py
      nba_matchup_interpreter.py
    evaluators/
      output_quality_evaluator.py
      grounding_evaluator.py
    delivery/
      delivery_agent.py
  tools/
    base.py
    league_data_tool.py
    player_stats_tool.py
    news_tool.py
    rules_tool.py
    recommendation_tool.py
    memory_tool.py
  workflows/
    orchestrator.py
    intent_registry.py
    onboarding_workflow.py
    draft_workflow.py
    lineup_workflow.py
    trade_workflow.py
    waiver_workflow.py
    news_workflow.py
  schemas/
    models.py
  data/
    nba/
      league_rules.json
      roster_template.csv
      season_context.json
    kaggle/
      nba_player_stats_2425.csv  (from Kaggle or scripts/download_kaggle_nba_csv.py; gitignored)
  scripts/
    download_kaggle_nba_csv.py
  configs/
    default_config.yaml
  prompts/
    routing_prompts.py
    boss_prompts.py
    agent_prompts.py
    evaluator_prompts.py
    delivery_prompts.py
  integrations/
    espn_nba.py
    nba_api_stats.py
  utils/
    env.py
    gemini_enrichment.py
    logging_utils.py
    trace_utils.py
    file_utils.py
    kaggle_nba_loader.py
    nba_data_source.py
    metrics.py
  tests/
    conftest.py
    test_routing.py
    test_tools.py
    test_boss_agent.py
    test_evaluators.py
    test_delivery.py
    test_fallback.py
    test_end_to_end.py
    test_intent_registry.py
    test_espn_integration.py
  web/
    app.py
  .streamlit/
    config.toml
  docs/
    DEMO_SCRIPT.md
  main.py
  Makefile
  run_demo.ps1
  run_tests.ps1
  CONTRIBUTING.md
  pyproject.toml
  README.md
  requirements.txt
```

## Team Collaboration

If you are joining this as one of the four contributors, start with these files in order:

1. `README.md`
2. `docs/TEAM_START_HERE.md`
3. `docs/WORKSTREAMS.md`
4. `docs/FINAL_PROTOTYPE_PLAN.md`
5. `docs/ARCHITECTURE.md`
6. `CONTRIBUTING.md`

This keeps the repo understandable before anyone starts editing code.

The four primary ownership areas are:

- System Architecture And Orchestration
- Agents And Tools
- Data / RAG / API
- Training, Eval, Demo, Results

Those are described in detail in `docs/WORKSTREAMS.md`, including first tasks, deliverables, and definitions of done.

## Install And Run

### Quick start (macOS / Linux, with Make)

**Use Python 3.11+** when possible (see `.python-version`; `pyenv` / `uv` can pin it). Older versions may need `eval_type_backport` from `requirements.txt`.

One-time setup, then launch the **web UI** (opens Streamlit, default port **8501**):

```bash
make setup
make run
```

Terminal demo (no browser): `make cli` (same as `python main.py`).

Other targets: `make test`, `make sample N=3`, `make prompt P="Who is the best waiver pickup?"`, `make help`.

Presentation prompts are listed in [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).

### Manual setup (any OS)

1. Create and activate a Python environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the default demo prompt:

```powershell
python main.py
```

4. Run a specific sample prompt:

```powershell
.\run_demo.ps1 -Sample 3
```

5. Run a custom prompt:

```powershell
.\run_demo.ps1 -Prompt "Who is the best waiver pickup right now?"
```

6. Run tests:

```powershell
.\run_tests.ps1
```

### Environment variables (optional)

Copy `.env.example` to `.env` locally (never commit `.env`).

| Variable | Purpose |
|----------|---------|
| `GEMINI_API_KEY` | If set, the boss may rewrite summary/rationale for readability **after** evaluators pass, using only tool evidence already attached. Implemented with the supported **`google-genai`** SDK. If unset, behavior stays fully deterministic. |
| `GEMINI_MODEL` | Optional. Pin one model id (e.g. `gemini-2.0-flash-001`) if the default candidate list returns 404 or you want to avoid quota retries across multiple names. |
| `FANDRAGEN_LIVE_ESPN` | Set to `1` or `true` to merge **live** NBA headlines and a small standings snapshot from ESPN public JSON into `NewsTool` / `PlayerStatsTool` results. If ESPN is unreachable, a fallback flag is recorded. |
| `FANDRAGEN_NBA_API` | Set to `1` to pull **real** per-game stats from stats.nba.com using the [`nba_api`](https://github.com/swar/nba_api) package. Optional [`data/nba/nba_player_map.json`](data/nba/nba_player_map.json) can map `player_id` → NBA `PERSON_ID`; otherwise a numeric `Player_ID` / `PLAYER_ID` (or `kaggle_nba_person_id` after load) column in the stats CSV is used. `PlayerStatsTool` and `RecommendationTool` blend last-10 PTS/REB/AST with table projections. First run may take longer (HTTP + rate limits). |
| `FANDRAGEN_KAGGLE_NBA_CSV` | Path to the [Kaggle 2024–25 NBA player stats CSV](https://www.kaggle.com/datasets/eduardopalmieri/nba-player-stats-season-2425). **Default if unset:** `data/kaggle/nba_player_stats_2425.csv` (relative to the project root). This file is **required** at runtime. Roster and waiver **slots** follow `data/nba/roster_template.csv` / `free_agents_template.csv`; player IDs are assigned from the CSV in projection order. |
| `NBA_STATS_SEASON` | Optional season string for game logs, e.g. `2024-25`. Defaults to `2024-25` when no `nba_player_map.json` season is present. |
| `FANDRAGEN_DEBUG` | Set to `1` for more verbose logs (including Gemini enrichment diagnostics). |

Enrichment failures are logged to stderr at **INFO**/**WARNING** (e.g. model errors or JSON parse issues) so `gemini_enrichment_applied: false` is explainable without silent failures.

## How Shared State Moves Through The System

1. `WorkflowOrchestrator` creates `WorkflowState` from the incoming query.
2. `RoutingAgent` attaches a `RouteDecision` with confidence and reasoning.
3. `NBABossAgent` decomposes the request into one or more `AgentTask` objects.
4. Worker agents execute tasks and attach structured `AgentResult` objects plus `ToolResult` evidence.
5. Evaluators inspect answer quality and grounding. If they fail, the boss triggers one revision only.
6. `DeliveryAgent` emits final JSON and markdown while marking simulated approval checkpoints.
7. Metrics and trace data are added for demo inspection.

## Data And Fallback Mode

Place the downloaded Kaggle CSV at **`data/kaggle/nba_player_stats_2425.csv`** (or set `FANDRAGEN_KAGGLE_NBA_CSV`). Alternatively, with [Kaggle API credentials](https://www.kaggle.com/docs/api) configured, run **`pip install kagglehub`** and **`python scripts/download_kaggle_nba_csv.py`** from the repo root to fetch `eduardopalmieri/nba-player-stats-season-2425` and copy `database_24_25.csv` into place. Game-level exports are aggregated to one row per player automatically. No API key is required for the base stats path. Optional ESPN / `nba_api` / Gemini integrations are env-gated.

The scenario in `data/nba/season_context.json` is set in the week of `2025-04-07` through `2025-04-13`, representing the final regular-season week before a fantasy playoff bracket starts.

Fallback behavior is explicit:

- The delivery payload includes `data_source.nba_stats_csv` and `using_synthetic_players: false`.
- Missing-data requests surface `fallback_flags` in the workflow state and final JSON.
- Recommendation execution is never sent to a real fantasy platform.
- Trade, lineup, draft, and waiver recommendations are marked `approval_required = true`.

## What Is Local / Simulated

- League **structure**: matchups, scoring rules, roster slot pattern, and empty news shell (`data/nba/`).
- **Player stats**: real season table from the Kaggle-format CSV (names, teams, PTS/REB/AST, etc.).
- Recommendation scoring (heuristic in `tools/recommendation_tool.py`, with injury/status penalties).
- User memory persistence (`data/nba/user_memory.json`, gitignored when customized).
- Human approval checkpoints (simulated; no real platform execution).

Optional **live ESPN** snippets supplement context when enabled.

## Current Recommendation Engine

The first version uses a deterministic heuristic engine in `tools/recommendation_tool.py`. It combines:

- projected points
- recent average points
- injury flag
- matchup difficulty
- sentiment and news deltas
- optional roster-need weighting

The scoring seam is isolated in `_score_player`, making it straightforward to replace with:

- a scoring function from another module
- a tree-based model such as Random Forest or XGBoost
- a richer predictive service later

## How To Add A New Worker Agent

1. Create a new class under `agents/general` that extends `BaseAgent`.
2. Return an `AgentResult` with rationale, assumptions, and attached `ToolResult` objects.
3. Add a workflow builder under `workflows` if the new intent needs dedicated task construction.
4. Register the agent in `NBABossAgent.workers`.
5. Extend the deterministic router keywords if the new intent needs routing support.
6. Add tests for routing, tool use, and end-to-end behavior.

## How To Replace Mocked Tools With Real APIs Later

1. Preserve the existing method names on each tool wrapper.
2. Swap file-backed internals for HTTP or SDK-backed implementations (see `integrations/espn_nba.py` for a no-key JSON example).
3. Continue returning `ToolResult` (and optional `enrichment`) so evaluators and delivery stay unchanged.
4. Preserve tool call logging in `BaseTool._record`.
5. Keep fallback behavior explicit when external data is unavailable.

## Repo Hygiene And Tooling

The repo now includes a few collaboration basics so the project looks more serious and is easier for multiple people to work in:

- `pyproject.toml` for package metadata and dev tooling configuration
- `.editorconfig` for shared formatting defaults
- `.gitattributes` for line-ending consistency across Windows and non-Windows machines
- `.github/pull_request_template.md` for consistent PR reviews
- `CONTRIBUTING.md` for branch, commit, and review guidance
- `docs/` notes for architecture and team onboarding

You can install the extra dev tools with:

```powershell
pip install -e .[dev]
```

These tools are optional for running the demo, but they make the repo easier to maintain as a team.

## Sample Prompts

- I am new to fantasy basketball. How does this league work?
- Who should I draft first from the available player pool?
- Set my best lineup for this week.
- Should I trade Player A for Player B?
- Who is the best waiver pickup right now?
- Summarize important news for my roster.
- Why did you rank these players this way?
- What assumptions are you making because data is missing?

## Sample Outputs

### Draft Advice

```json
{
  "recommendations": [
    {
      "title": "Draft Zion Mercer first",
      "proposed_action": "Select Zion Mercer with the next pick.",
      "approval_required": true
    }
  ],
  "confidence": 0.84
}
```

Summary: Zion Mercer leads the deterministic free-agent pool because his projection, recent form, and favorable matchup combine into the highest heuristic score in demo mode.

### Lineup Optimization

```json
{
  "recommendations": [
    {
      "title": "Start the highest-scoring five rostered players",
      "proposed_action": "Set starters to … (top five heuristic scores from your NBA stats CSV roster).",
      "approval_required": true
    }
  ],
  "confidence": 0.82
}
```

Summary: The lineup path promotes the top five rostered heuristic scores and labels the suggestion as a simulated action requiring approval.

### Missing-Data Explanation

```json
{
  "summary": "Explained the assumptions FanDraGen makes when local data is missing or incomplete.",
  "data_source": {
    "using_synthetic_players": false,
    "fallback_flags": ["missing_projection_source_local_mode"]
  },
  "trace": {
    "revision_count": 1
  }
}
```

Summary: The fallback path intentionally demonstrates evaluator behavior by surfacing assumptions, logging a fallback flag, and performing one revision cycle.

## Traditional Metrics Included

- task completion rate
- routing accuracy
- tool invocation correctness
- evaluator rejection rate
- revision success rate
- response grounding coverage
- deterministic consistency

These are lightweight demo metrics rather than a full benchmarking framework.

## Limitations And Excluded Scope

- No authentication
- No real fantasy account actions
- No external APIs in the default configuration (optional ESPN / `nba_api` / Gemini when enabled)
- No multisport implementation beyond minimal NBA helper logic
- No web or graphical UI
- No production deployment setup

## End-To-End Summary

At runtime, a user prompt is routed by deterministic intent rules, decomposed by the NBA boss agent, fulfilled by one of the worker agents through mocked tools, checked by two evaluators, optionally revised once, and then formatted by the delivery agent into both JSON and markdown. Recommendation-style outputs are deliberately blocked behind a simulated approval checkpoint so the demo clearly shows decision support without any real platform execution.