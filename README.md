# FanDraGen

FanDraGen is a research-demo-grade, local-first NBA fantasy sports assistant scaffold. It demonstrates multi-agent orchestration, explicit shared state, tool usage, evaluator behavior, fallback handling, simulated approval checkpoints, and traceability. **Core demos use deterministic `data/demo` files** so tests and CI stay keyless. **Optional integrations** can enrich outputs: public ESPN JSON (no key) and an optional Gemini API key for natural-language polish that still relies on attached tool evidence.

The primary implementation is plain Python. An optional LangGraph mirror layer is included to show how the same workflow could be expressed as a stateful graph, but the core system runs entirely without LangGraph.

The current mock scenario is the final week of the 2024-25 NBA regular season, immediately before fantasy playoffs begin. That gives the demo a clear late-season context instead of a generic basketball dataset.

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
- `langgraph_optional/*`: Optional mirror layer that reuses the same schemas and orchestration boundaries.

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
    demo/
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
  utils/
    env.py
    gemini_enrichment.py
    logging_utils.py
    trace_utils.py
    file_utils.py
    metrics.py
  langgraph_optional/
    graph_state.py
    graph_builder.py
    graph_runner.py
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
| `FANDRAGEN_LIVE_ESPN` | Set to `1` or `true` to merge **live** NBA headlines and a small standings snapshot from ESPN public JSON into `NewsTool` / `PlayerStatsTool` results. Roster and player rows remain demo CSV/JSON. If ESPN is unreachable, a fallback flag is recorded and demo data still drives recommendations. |
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

## Mock Data And Fallback Mode

All tools read from `data/demo`. No external API calls are required.

The current demo dataset is intentionally set in the week of `2025-04-07` through `2025-04-13`, representing the final regular-season week before a fantasy playoff bracket starts.

Fallback behavior is explicit:

- The system always labels that demo data is active.
- Missing-data requests surface `fallback_flags` in the workflow state and final JSON.
- Recommendation execution is never sent to a real fantasy platform.
- Trade, lineup, draft, and waiver recommendations are marked `approval_required = true`.

## What Is Mocked

- League rosters, matchups, scoring rules, and free agents (CSV/JSON under `data/demo/`).
- Player stat rows, projections, and curated news used for ranking and explanations.
- Recommendation scoring (heuristic in `tools/recommendation_tool.py`, with injury/status penalties).
- User memory persistence.
- Human approval checkpoints (simulated; no real platform execution).
- LangGraph integration, unless the optional dependency is installed.

Optional **live ESPN** snippets supplement context only; they do not replace fictional roster rows unless you extend the data layer.

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

## Optional LangGraph Layer

The `langgraph_optional` package mirrors the same boundaries used by the plain Python path:

- routing node
- boss node
- worker or tool nodes
- evaluator nodes
- delivery node
- approval node

If LangGraph is not installed, the optional layer fails with a clear message while the plain Python workflow continues to run normally.

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
      "proposed_action": "Set starters to Luka Vance, Owen Price, DeAndre Knox, Mason Reed, Victor Hale.",
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
  "summary": "Explained the assumptions FanDraGen makes when demo data is missing or incomplete.",
  "fallback_demo_data_usage": {
    "using_demo_data": true,
    "fallback_flags": ["missing_projection_source_in_demo_mode"]
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
- No external APIs
- No multisport implementation beyond minimal NBA helper logic
- No web or graphical UI
- No production deployment setup

## End-To-End Summary

At runtime, a user prompt is routed by deterministic intent rules, decomposed by the NBA boss agent, fulfilled by one of the worker agents through mocked tools, checked by two evaluators, optionally revised once, and then formatted by the delivery agent into both JSON and markdown. Recommendation-style outputs are deliberately blocked behind a simulated approval checkpoint so the demo clearly shows decision support without any real platform execution.