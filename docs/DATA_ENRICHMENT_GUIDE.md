# Data Enrichment and Demo Alias Guide

## Demo Player Aliases
- Demo prompts like "Should I trade Player A for Player B?" use aliases defined in `configs/default_config.yaml` under `demo.player_aliases`.
- To ensure demo scenarios work, set these aliases to real player names present in your main stats CSV (e.g., "LeBron James", "Nikola Jokić").
- If you add new demo prompts, update the alias mapping accordingly.

## Adding/Enriching Data
- To enrich news, matchups, standings, or rosters, edit the corresponding files in `data/nba/`.
- For player news, include fields for status, injury, and stat projections.
- For matchups and standings, reflect late-season playoff races and rest scenarios.
- For new players, ensure their names match exactly in all relevant files.

## API Fallback
- When live API is enabled, the system will use real-time data for player status and projections.
- If API is unavailable, the system falls back to enriched local data for all tools.

## Troubleshooting
- If a demo prompt fails with a KeyError, check that the alias maps to a real player in the stats CSV.
- For new contributors: always validate with `python main.py --prompt <demo>` and run the test suite.
