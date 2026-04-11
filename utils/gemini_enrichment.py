"""Optional Gemini post-processing for agent summaries (tool-grounded only).

Uses the supported ``google-genai`` SDK (``from google import genai``), not the
deprecated ``google.generativeai`` package.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from utils.env import gemini_api_key

logger = logging.getLogger("fandragen.gemini")

# Prefer small, fast models; fall back if a name is unavailable in the account/region.
_MODEL_CANDIDATES = ("gemini-2.0-flash", "gemini-1.5-flash")


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
    prompt = (
        "You are FanDraGen, an NBA fantasy assistant. Rewrite the summary and rationale to be clear and concise. "
        "Do NOT invent statistics, injuries, or trades. Only use facts implied by the evidence block.\n\n"
        f"Evidence (authoritative):\n{evidence_block}\n\n"
        f"Draft summary:\n{summary}\n\n"
        f"Draft rationale bullets:\n" + "\n".join(f"- {r}" for r in rationale[:12])
        + "\n\nRespond as JSON with keys \"summary\" (string) and \"rationale\" (array of strings)."
    )

    client = genai.Client(api_key=key)
    config = types.GenerateContentConfig(
        temperature=0.35,
        max_output_tokens=1024,
        response_mime_type="application/json",
    )

    last_error: Exception | None = None
    for model_id in _MODEL_CANDIDATES:
        try:
            response = client.models.generate_content(model=model_id, contents=prompt, config=config)
            text = (getattr(response, "text", None) or "").strip()
            if not text:
                logger.warning("Gemini returned empty text (model=%s).", model_id)
                continue
            parsed = _parse_json_loose(text)
            if not parsed:
                logger.warning(
                    "Gemini JSON parse failed (model=%s). First 200 chars: %r",
                    model_id,
                    text[:200],
                )
                continue
            new_summary = parsed.get("summary")
            new_rationale = parsed.get("rationale")
            if not isinstance(new_summary, str) or not isinstance(new_rationale, list):
                logger.warning("Gemini JSON missing summary/rationale types (model=%s).", model_id)
                continue
            cleaned = [str(x) for x in new_rationale if str(x).strip()]
            if len(new_summary.strip()) < 20 or not cleaned:
                logger.warning("Gemini JSON too short after validation (model=%s).", model_id)
                continue
            logger.info("Gemini enrichment succeeded with model=%s", model_id)
            return new_summary.strip(), cleaned
        except Exception as exc:
            last_error = exc
            logger.warning("Gemini generate_content failed (model=%s): %s", model_id, exc)

    if last_error:
        logger.error("All Gemini model candidates failed; last error: %s", last_error)
    return None


def _parse_json_loose(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
