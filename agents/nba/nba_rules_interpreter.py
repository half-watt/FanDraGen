"""Minimal NBA roster and scoring helper."""

from __future__ import annotations

from schemas.models import LeagueContext


class NBARulesInterpreter:
    """Provides lightweight NBA-specific league reasoning."""

    def summarize_roster_logic(self, league_context: LeagueContext | None) -> str:
        if league_context is None:
            return "Roster logic unavailable because league rules have not been loaded."
        slots = ", ".join(league_context.roster_slots)
        return f"This NBA points league uses these roster slots: {slots}."

    def interpret_scoring(self, league_context: LeagueContext | None) -> str:
        if league_context is None:
            return "Scoring format unavailable in fallback mode."
        scoring = league_context.scoring_settings
        return (
            f"Points scoring emphasizes volume stats: {scoring['points']} per point, "
            f"{scoring['rebounds']} per rebound, and {scoring['assists']} per assist."
        )
