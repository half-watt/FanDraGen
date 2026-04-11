"""Minimal matchup-difficulty helper."""

from __future__ import annotations


class NBAMatchupInterpreter:
    """Converts numeric matchup difficulty into readable NBA context."""

    def explain_difficulty(self, difficulty: int) -> str:
        mapping = {
            1: "excellent matchup",
            2: "good matchup",
            3: "neutral matchup",
            4: "tough matchup",
            5: "very tough matchup",
        }
        return mapping.get(difficulty, "unknown matchup difficulty")
