"""Deterministic routing agent for the mocked demo path."""

from __future__ import annotations

from schemas.models import RouteDecision, UserQuery, WorkflowState
from utils.logging_utils import log_event
from workflows.intent_registry import INTENT_KEYWORDS, INTENT_PRIORITY


class RoutingAgent:
    """Classifies intent and routes NBA requests to the NBA boss agent."""

    intent_keywords = INTENT_KEYWORDS
    intent_priority = INTENT_PRIORITY

    nba_keywords = ["nba", "basketball", "lineup", "roster", "waiver", "draft", "trade", "league"]

    def route(self, query: UserQuery, state: WorkflowState) -> RouteDecision:
        """Return a deterministic route decision for the incoming query."""

        lowered = query.text.lower()
        matched_intent = "onboarding/help"
        confidence = 0.62
        for intent in self.intent_priority:
            keywords = self.intent_keywords[intent]
            if any(keyword in lowered for keyword in keywords):
                matched_intent = intent
                confidence = 0.9 if intent != "onboarding/help" else 0.78
                break

        supported_demo_intents = set(self.intent_keywords.keys())
        domain = "nba" if any(keyword in lowered for keyword in self.nba_keywords) or matched_intent in supported_demo_intents else "general"
        route_target = "NBABossAgent" if domain == "nba" else "OnboardingAgent"
        reasoning = f"Matched intent '{matched_intent}' using deterministic keyword rules (priority order); domain={domain}."
        decision = RouteDecision(
            intent=matched_intent,
            domain=domain,
            route_target=route_target,
            confidence=confidence,
            reasoning=reasoning,
        )
        state.route_decision = decision
        log_event(
            state,
            "route_decision",
            intent=decision.intent,
            domain=decision.domain,
            target=decision.route_target,
            confidence=decision.confidence,
        )
        return decision
