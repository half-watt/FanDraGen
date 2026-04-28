# Appendix — Representative JSON Output Snippets
**Run date:** 2026-04-15  
**Mode:** mocked / plain\_python  
**Data source:** `data/kaggle/nba_player_stats_2425.csv` (561 players, 2024-25 season)  
**All samples passed with zero tracebacks.**

---

## A. Trade Evaluation (Sample 3)
**Query:** "Should I trade Player A for Player B?"  
**Intent matched:** `trade evaluation` (confidence 0.90)  
**Agent chain:** `RoutingAgent → NBABossAgent → TradeEvaluationAgent → OutputQualityEvaluator → GroundingEvaluator → DeliveryAgent`  
**Notable:** `approval_required = true`; action held at checkpoint pending human confirmation.

```json
{
  "query": {
    "text": "Should I trade Player A for Player B?",
    "sport": "NBA",
    "user_id": "demo_user",
    "league_id": "nba_league_01",
    "received_at": "2026-04-15T01:26:28.927765Z"
  },
  "route": {
    "intent": "trade evaluation",
    "domain": "nba",
    "route_target": "NBABossAgent",
    "confidence": 0.9,
    "reasoning": "Matched intent 'trade evaluation' using deterministic keyword rules (priority order); domain=nba."
  },
  "recommendations": [
    {
      "item_id": "trade-kg_00006-kg_00001",
      "title": "Trade evaluation",
      "details": "Net heuristic delta: 7.45 in favor of accepting the deal.",
      "confidence": 0.76,
      "score": 7.45,
      "action_type": "trade evaluation",
      "approval_required": true,
      "proposed_action": "Trade LeBron James for Nikola Jokić.",
      "action_not_executed": true,
      "rationale": [
        "Nikola Jokić score: 36.98",
        "LeBron James score: 29.53"
      ],
      "assumptions": [
        "The trade is evaluated as a one-for-one points-league swap."
      ],
      "supporting_evidence": [
        "RecommendationTool.evaluate_trade",
        "PlayerStatsTool.fetch_player_stats",
        "NBA stats CSV (Kaggle format)"
      ]
    }
  ],
  "summary": "Trade delta between LeBron James and Nikola Jokić: 7.45.",
  "confidence": 0.76,
  "approval_status": {
    "approval_required": true,
    "approved": null,
    "proposed_action": "Trade LeBron James for Nikola Jokić.",
    "action_not_executed": true,
    "checkpoint_reason": "Recommendation-style output requires simulated human approval."
  },
  "trace": {
    "agents": ["TradeEvaluationAgent"],
    "tool_calls": [
      {
        "tool_name": "PlayerStatsTool",
        "method_name": "fetch_player_stats",
        "arguments": { "player_names": ["LeBron James", "Nikola Jokić"] },
        "status": "success",
        "fallback_used": false
      },
      {
        "tool_name": "RecommendationTool",
        "method_name": "evaluate_trade",
        "arguments": { "give_player": "LeBron James", "receive_player": "Nikola Jokić" },
        "status": "success",
        "summary": "Trade delta between LeBron James and Nikola Jokić: 7.45.",
        "fallback_used": false
      }
    ],
    "fallback_flags": [],
    "revision_count": 0
  }
}
```

**Key fields for results table:**

| Field | Value |
|---|---|
| Intent | trade evaluation |
| Route confidence | 0.90 |
| Output confidence | 0.76 |
| approval_required | **true** |
| fallback_flags | (none) |
| revision_count | 0 |
| Tool calls | 2 (PlayerStatsTool, RecommendationTool) |
| Net delta | +7.45 (favor Jokić) |

---

## B. Waiver / Approval Gate (Sample 4)
**Query:** "Who is the best waiver pickup right now?"  
**Intent matched:** `waiver/free agent pickup` (confidence 0.90)  
**Agent chain:** `RoutingAgent → NBABossAgent → ManagingAgent → Evaluators → DeliveryAgent`  
**Notable:** Demonstrates the human-in-the-loop approval gate — `approval_required = true`, action held; Jaren Jackson Jr. identified as top pickup.

```json
{
  "query": {
    "text": "Who is the best waiver pickup right now?",
    "sport": "NBA",
    "user_id": "demo_user",
    "league_id": "nba_league_01",
    "received_at": "2026-04-15T01:26:29.458484Z"
  },
  "route": {
    "intent": "waiver/free agent pickup",
    "domain": "nba",
    "route_target": "NBABossAgent",
    "confidence": 0.9,
    "reasoning": "Matched intent 'waiver/free agent pickup' using deterministic keyword rules (priority order); domain=nba."
  },
  "recommendations": [
    {
      "item_id": "kg_00025",
      "title": "Add Jaren Jackson Jr. from waivers",
      "details": "Best free-agent score in the current pool: 26.29.",
      "confidence": 0.81,
      "score": 26.29,
      "action_type": "waiver/free agent pickup",
      "approval_required": true,
      "proposed_action": "Submit a waiver claim for Jaren Jackson Jr..",
      "action_not_executed": true,
      "rationale": [
        "Recent average: 27.09",
        "News sentiment: 0"
      ],
      "assumptions": [
        "Assumes waiver priority is available in mocked mode."
      ],
      "supporting_evidence": [
        "RecommendationTool.rank_players",
        "RecommendationTool.recommend_waiver_pickup",
        "LeagueDataTool.fetch_free_agents"
      ]
    }
  ],
  "summary": "Recommended Jaren Jackson Jr. as the top waiver pickup.",
  "confidence": 0.81,
  "approval_status": {
    "approval_required": true,
    "approved": null,
    "proposed_action": "Submit a waiver claim for Jaren Jackson Jr..",
    "action_not_executed": true,
    "checkpoint_reason": "Recommendation-style output requires simulated human approval."
  },
  "trace": {
    "agents": ["ManagingAgent"],
    "tool_calls": [
      {
        "tool_name": "LeagueDataTool",
        "method_name": "fetch_free_agents",
        "status": "success",
        "fallback_used": false
      },
      {
        "tool_name": "RecommendationTool",
        "method_name": "rank_players",
        "arguments": { "player_ids": ["kg_00025","kg_00026","kg_00027","kg_00028","kg_00029","kg_00030"] },
        "status": "success",
        "summary": "Ranked 6 players using heuristic scoring.",
        "fallback_used": false
      },
      {
        "tool_name": "RecommendationTool",
        "method_name": "recommend_waiver_pickup",
        "status": "success",
        "summary": "Recommended Jaren Jackson Jr. as the top waiver pickup.",
        "fallback_used": false
      }
    ],
    "fallback_flags": [],
    "revision_count": 0
  }
}
```

**Key fields for results table:**

| Field | Value |
|---|---|
| Intent | waiver/free agent pickup |
| Route confidence | 0.90 |
| Output confidence | 0.81 |
| approval_required | **true** |
| fallback_flags | (none) |
| revision_count | 0 |
| Tool calls | 3 (LeagueDataTool, RecommendationTool ×2) |
| Top pickup | Jaren Jackson Jr. (score 26.29) |

---

## C. News Summarization (Sample 5)
**Query:** "Summarize important news for my roster."  
**Intent matched:** `roster news summary` (confidence 0.90)  
**Agent chain:** `RoutingAgent → NBABossAgent → NewsSummarizationAgent → Evaluators → DeliveryAgent`  
**Notable:** `approval_required = false` — informational output, no action checkpoint needed. Five players summarized from local news feed.

```json
{
  "query": {
    "text": "Summarize important news for my roster.",
    "sport": "NBA",
    "user_id": "demo_user",
    "league_id": "nba_league_01",
    "received_at": "2026-04-15T01:26:30.010533Z"
  },
  "route": {
    "intent": "roster news summary",
    "domain": "nba",
    "route_target": "NBABossAgent",
    "confidence": 0.9,
    "reasoning": "Matched intent 'roster news summary' using deterministic keyword rules (priority order); domain=nba."
  },
  "recommendations": [],
  "summary": "Summarized the most relevant player news for the current roster.",
  "rationale": [
    "LeBron James: Resting for playoff preparation",
    "Shai Gilgeous-Alexander: Probable for must-win game",
    "Nikola Jokić: Expected to play, team clinched #1 seed",
    "Cade Cunningham: Out for season finale (knee)"
  ],
  "assumptions": [
    "Only roster-related news from the local news feed is included."
  ],
  "confidence": 0.86,
  "approval_status": {
    "approval_required": false,
    "approved": null,
    "proposed_action": null,
    "action_not_executed": true,
    "checkpoint_reason": "No approval required."
  },
  "trace": {
    "agents": ["NewsSummarizationAgent"],
    "tool_calls": [
      {
        "tool_name": "LeagueDataTool",
        "method_name": "fetch_rosters",
        "status": "success",
        "fallback_used": false
      },
      {
        "tool_name": "NewsTool",
        "method_name": "fetch_player_news",
        "arguments": {
          "player_names": [
            "Nikola Jokić", "Giannis Antetokounmpo",
            "Luka Dončić", "Shai Gilgeous-Alexander",
            "Cade Cunningham", "LeBron James"
          ]
        },
        "status": "success",
        "summary": "Loaded player news.",
        "fallback_used": false
      }
    ],
    "fallback_flags": [],
    "revision_count": 0
  }
}
```

**Key fields for results table:**

| Field | Value |
|---|---|
| Intent | roster news summary |
| Route confidence | 0.90 |
| Output confidence | 0.86 |
| approval_required | **false** |
| fallback_flags | (none) |
| revision_count | 0 |
| Tool calls | 2 (LeagueDataTool, NewsTool) |
| Players summarized | 4 (news items in rationale) |

---

## D. Fallback / Missing Data Explanation (Sample 7)
**Query:** "What assumptions are you making because data is missing?"  
**Intent matched:** `missing data / fallback explanation` (confidence 0.90)  
**Agent chain:** `RoutingAgent → NBABossAgent → ManagingAgent → Evaluators (2 revision cycles) → DeliveryAgent`  
**Notable:** Triggered the evaluator-driven revision loop (`revision_count = 2`). Output confidence dropped to 0.69. `fallback_flags` populated with `missing_projection_source_local_mode`. Unresolved evaluator feedback surfaced transparently in `assumptions` and `rationale`.

```json
{
  "query": {
    "text": "What assumptions are you making because data is missing?",
    "sport": "NBA",
    "user_id": "demo_user",
    "league_id": "nba_league_01",
    "received_at": "2026-04-15T01:26:31.111156Z"
  },
  "route": {
    "intent": "missing data / fallback explanation",
    "domain": "nba",
    "route_target": "NBABossAgent",
    "confidence": 0.9,
    "reasoning": "Matched intent 'missing data / fallback explanation' using deterministic keyword rules (priority order); domain=nba."
  },
  "recommendations": [],
  "summary": "Explained the assumptions FanDraGen makes when local data is missing or incomplete. Revised once to address evaluator feedback. (Evaluator feedback could not be fully resolved after 2 attempts.)",
  "rationale": [
    "The system uses the local NBA stats CSV and league files and does not invent external data sources.",
    "When a file or field is missing, the workflow surfaces a fallback flag and uses the best available local evidence.",
    "Evaluator feedback could not be fully resolved: No tool outputs were attached to the result., Reference specific tool evidence and fallback state explicitly."
  ],
  "assumptions": [
    "missing_projection_source_local_mode",
    "Revision note: No tool outputs were attached to the result.",
    "Revision note: Reference specific tool evidence and fallback state explicitly.",
    "Unresolved evaluator issues after 2 revisions: No tool outputs were attached to the result., Reference specific tool evidence and fallback state explicitly."
  ],
  "supporting_evidence": [
    "Fallback flags: missing_projection_source_local_mode"
  ],
  "confidence": 0.69,
  "data_source": {
    "fallback_flags": ["missing_projection_source_local_mode"],
    "live_espn_enrichment_enabled": false,
    "nba_api_enrichment_enabled": false,
    "gemini_configured": false,
    "gemini_enrichment_applied": false
  },
  "approval_status": {
    "approval_required": false,
    "approved": null,
    "proposed_action": null,
    "action_not_executed": true,
    "checkpoint_reason": "No approval required."
  },
  "trace": {
    "agents": ["ManagingAgent"],
    "tool_calls": [],
    "fallback_flags": ["missing_projection_source_local_mode"],
    "revision_count": 2
  }
}
```

**Key fields for results table:**

| Field | Value |
|---|---|
| Intent | missing data / fallback explanation |
| Route confidence | 0.90 |
| Output confidence | **0.69** (penalized by unresolved evaluator flags) |
| approval_required | false |
| fallback_flags | `missing_projection_source_local_mode` |
| revision_count | **2** |
| Tool calls | 0 (no external data available for this intent) |

---

## Cross-Sample Summary Table

| Sample | Intent | Route Conf. | Output Conf. | Approval Gate | Fallback Flags | Revisions | Tool Calls |
|:---:|---|:---:|:---:|:---:|---|:---:|:---:|
| 3 | Trade evaluation | 0.90 | 0.76 | ✅ Yes | — | 0 | 2 |
| 4 | Waiver pickup | 0.90 | 0.81 | ✅ Yes | — | 0 | 3 |
| 5 | Roster news summary | 0.90 | 0.86 | ❌ No | — | 0 | 2 |
| 7 | Missing data / fallback | 0.90 | 0.69 | ❌ No | `missing_projection_source_local_mode` | 2 | 0 |

> **Routing confidence is consistently 0.90** across all intents — the deterministic keyword-priority router produces stable, predictable routing. Output confidence varies by task complexity and evaluator outcomes, with confidence penalties applied when grounding or quality evaluators flag unresolvable issues (sample 7: 0.69).
