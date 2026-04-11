"""Optional Gemini post-processing for agent summaries (tool-grounded only).

Uses the supported ``google-genai`` SDK (``from google import genai``), not the
deprecated ``google.generativeai`` package.

Uses structured output (``response_schema``) so the API returns validated JSON
and avoids truncated / malformed JSON from free-form generation.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from pydantic import BaseModel, Field

from utils.env import gemini_api_key, gemini_model_override

logger = logging.getLogger("fandragen.gemini")

# Prefer models that work on current Gemini API; put gemini-2.5-flash first — it often
# succeeds when 2.0 hits free-tier 429s. Override with GEMINI_MODEL=...
_MODEL_CANDIDATES = (
    "gemini-2.5-flash",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash",
)

# Avoid huge prompts (token limits + cost); keep enough for grounding.
_MAX_EVIDENCE_CHARS = 28000


class GeminiEnrichmentPayload(BaseModel):
    """Schema for Gemini polish: must match keys the boss expects."""

    summary: str = Field(description="Clear, concise summary; no invented stats.")
    rationale: list[str] = Field(description="Short bullets grounded in evidence only.")


def enrich_summary_with_gemini(
    summary: str,
    rationale: list[str],
    tool_evidence_snippets: list[str],
) -> tuple[str, list[str]] | None:
    """Return improved summary and rationale, or None if Gemini is unavailable or fails."""

    key = gemini_api_key()
    if not key:
        logger.debug("GEMINI_API_KEY not set; skipping enrichment.")
        return None

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        logger.warning("google-genai is not installed (%s). pip install google-genai", exc)
        return None

    evidence_block = "\n".join(tool_evidence_snippets[:24])
    if len(evidence_block) > _MAX_EVIDENCE_CHARS:
        evidence_block = evidence_block[:_MAX_EVIDENCE_CHARS] + "\n…[evidence truncated]"

    prompt = (
        "You are FanDraGen, an NBA fantasy assistant. Rewrite the summary and rationale to be clear and concise. "
        "Do NOT invent statistics, injuries, or trades. Only use facts implied by the evidence block.\n\n"
        f"Evidence (authoritative):\n{evidence_block}\n\n"
        f"Draft summary:\n{summary}\n\n"
        f"Draft rationale bullets:\n" + "\n".join(f"- {r}" for r in rationale[:12])
        + "\n\nFill the JSON schema: one summary string and a rationale array of strings."
    )

    client = genai.Client(api_key=key)
    config = types.GenerateContentConfig(
        temperature=0.35,
        max_output_tokens=8192,
        response_mime_type="application/json",
        response_schema=GeminiEnrichmentPayload,
    )

    override = gemini_model_override()
    seen: set[str] = set()
    model_order: list[str] = []
    for mid in ([override] if override else []) + list(_MODEL_CANDIDATES):
        if mid and mid not in seen:
            seen.add(mid)
            model_order.append(mid)

    last_error: Exception | None = None
    for model_id in model_order:
        for attempt in range(3):
            try:
                response = client.models.generate_content(model=model_id, contents=prompt, config=config)
                parsed_obj = getattr(response, "parsed", None)
                if isinstance(parsed_obj, GeminiEnrichmentPayload):
                    new_summary = parsed_obj.summary.strip()
                    cleaned = [str(x).strip() for x in parsed_obj.rationale if str(x).strip()]
                    if len(new_summary) >= 20 and cleaned:
                        logger.info("Gemini enrichment succeeded with model=%s", model_id)
                        return new_summary, cleaned
                    logger.warning("Gemini structured output too short (model=%s).", model_id)
                    break

                text = (getattr(response, "text", None) or "").strip()
                parsed = _parse_json_loose(text) if text else None
                if parsed:
                    new_summary = parsed.get("summary")
                    new_rationale = parsed.get("rationale")
                    if isinstance(new_summary, str) and isinstance(new_rationale, list):
                        cleaned = [str(x) for x in new_rationale if str(x).strip()]
                        if len(new_summary.strip()) >= 20 and cleaned:
                            logger.info("Gemini enrichment succeeded (text fallback) model=%s", model_id)
                            return new_summary.strip(), cleaned
                logger.warning(
                    "Gemini returned unusable structured output (model=%s). text_len=%s parsed=%s",
                    model_id,
                    len(text),
                    bool(parsed),
                )
                break
            except Exception as exc:
                last_error = exc
                err_s = str(exc)
                if (
                    "429" in err_s
                    or "RESOURCE_EXHAUSTED" in err_s
                    or "quota" in err_s.lower()
                    or "Too Many Requests" in err_s
                ) and attempt < 2:
                    wait = 2.0 * (2**attempt)
                    logger.warning(
                        "Gemini rate limited (model=%s), retry %s/%s in %.1fs",
                        model_id,
                        attempt + 1,
                        3,
                        wait,
                    )
                    time.sleep(wait)
                    continue
                if "429" in err_s or "RESOURCE_EXHAUSTED" in err_s:
                    logger.warning(
                        "Gemini rate limit or quota (model=%s). Try GEMINI_MODEL=gemini-2.5-flash. %s",
                        model_id,
                        err_s[:400],
                    )
                else:
                    logger.warning("Gemini generate_content failed (model=%s): %s", model_id, exc)
                break

    if last_error:
        logger.warning(
            "Gemini enrichment skipped; last error: %s. "
            "Try GEMINI_MODEL=gemini-2.5-flash, wait if quota 429, or check billing.",
            last_error,
        )
    return None


def _parse_json_loose(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    extracted = _extract_balanced_json_object(text)
    if extracted:
        try:
            return json.loads(extracted)
        except json.JSONDecodeError:
            return None
    return None


def _extract_balanced_json_object(text: str) -> str | None:
    """Best-effort extract a single JSON object when the model truncates or adds noise."""

    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None
