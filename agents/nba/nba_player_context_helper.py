"""Minimal NBA player-resolution helper for the single-sport demo."""

from __future__ import annotations

from typing import Iterable

from schemas.models import WorkflowState
from utils.file_utils import read_yaml


class NBAPlayerContextHelper:
    """Resolves demo aliases and extracts likely player references from text."""

    def __init__(self, config_path: str = "configs/default_config.yaml") -> None:
        self.config = read_yaml(__import__("pathlib").Path(config_path))
        self.aliases = self.config.get("demo", {}).get("player_aliases", {})

    def resolve_aliases(self, text: str) -> dict[str, str]:
        found = {}
        for alias, real_name in self.aliases.items():
            if alias.lower() in text.lower():
                found[alias] = real_name
        return found

    def roster_player_names(self, state: WorkflowState) -> list[str]:
        roster_rows = state.intermediate_outputs.get("roster_rows", [])
        players_by_id = state.intermediate_outputs.get("players_by_id", {})
        names = []
        for row in roster_rows:
            player = players_by_id.get(row["player_id"])
            if player:
                names.append(player["player_name"])
        return names

    def canonical_names(self, names: Iterable[str]) -> list[str]:
        return [self.aliases.get(name, name) for name in names]
