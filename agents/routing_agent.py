"""Deterministic routing agent for the mocked demo path."""

from __future__ import annotations

from schemas.models import RouteDecision, UserQuery, WorkflowState
from utils.logging_utils import log_event


class RoutingAgent:
    """Classifies intent and routes NBA requests to the NBA boss agent."""

    intent_keywords = {
        "onboarding/help": ["new", "how does this league work", "help", "league work"],
        "draft advice": ["draft", "draft first"],
        "lineup optimization": ["best lineup", "set my best lineup", "lineup"],
        "trade evaluation": ["trade"],
        "waiver/free agent pickup": ["waiver", "pickup", "free agent"],
        "roster news summary": ["news", "summarize important news"],
        "explanation / why reasoning": ["why", "rank these players", "explain"],
        "missing data / fallback explanation": ["assumptions", "missing data", "fallback"],
    }

    nba_keywords = ["nba", "basketball", "lineup", "roster", "waiver", "draft", "trade", "league"]

    def route(self, query: UserQuery, state: WorkflowState) -> RouteDecision:
        """Return a deterministic route decision for the incoming query."""

        lowered = query.text.lower()
        matched_intent = "onboarding/help"
        confidence = 0.62
        for intent, keywords in self.intent_keywords.items():
            if any(keyword in lowered for keyword in keywords):
                matched_intent = intent
                confidence = 0.9 if len(keywords) == 1 or any(keyword in lowered for keyword in keywords[:2]) else 0.8
                break

        supported_demo_intents = set(self.intent_keywords.keys())
        domain = "nba" if any(keyword in lowered for keyword in self.nba_keywords) or matched_intent in supported_demo_intents else "general"
        route_target = "NBABossAgent" if domain == "nba" else "OnboardingAgent"
        reasoning = f"Matched intent '{matched_intent}' using deterministic keyword rules; domain={domain}."
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
