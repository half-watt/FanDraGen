# FanDraGen presentation script

Use these prompts in order for a tight live demo (`make run` for the UI, or `make cli` for the terminal).

## 1. Onboarding (no approval gate)

**Prompt:** `I am new to fantasy basketball. How does this league work?`

**Point out:** routing intent `onboarding/help`, `RulesTool` + `LeagueDataTool`, evaluators pass, no approval.

## 2. Recommendation + approval gate

**Prompt:** `Who is the best waiver pickup right now?`

**Point out:** waiver intent, `RecommendationTool`, `approval_required: true`, proposed action is **not** executed.

## 3. Fallback / assumptions (optional)

**Prompt:** `What assumptions are you making because data is missing?`

**Point out:** fallback flags, revision loop (at most one), explicit assumptions.

---

**Artifacts:** Export trace JSON from the UI **Raw JSON** tab or terminal `main.py` output for screenshots.

**Env (optional):** `GEMINI_API_KEY` for summary polish (`gemini_enrichment_applied` in payload). `FANDRAGEN_LIVE_ESPN=1` for ESPN headlines/standings. `FANDRAGEN_NBA_API=1` for real stats.nba.com game logs via [`nba_api`](https://github.com/swar/nba_api) (see `data/demo/nba_player_map.json`).
