"""Optional Gemini post-processing for agent summaries (tool-grounded only)."""

from __future__ import annotations

from typing import Any

from utils.env import gemini_api_key


def enrich_summary_with_gemini(
    summary: str,
    rationale: list[str],
    tool_evidence_snippets: list[str],
) -> tuple[str, list[str]] | None:
    """Return improved summary and rationale, or None if Gemini is unavailable or fails."""

    key = gemini_api_key()
    if not key:
        return None
    try:
        import google.generativeai as genai
    except ImportError:
        return None

    genai.configure(api_key=key)
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
    except Exception:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash-8b")
        except Exception:
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
    try:
        resp = model.generate_content(
            prompt,
            generation_config={"temperature": 0.35, "max_output_tokens": 1024},
        )
        text = (resp.text or "").strip()
    except Exception:
        return None

    parsed = _parse_json_loose(text)
    if not parsed:
        return None
    new_summary = parsed.get("summary")
    new_rationale = parsed.get("rationale")
    if not isinstance(new_summary, str) or not isinstance(new_rationale, list):
        return None
    cleaned = [str(x) for x in new_rationale if str(x).strip()]
    if len(new_summary.strip()) < 20 or not cleaned:
        return None
    return new_summary.strip(), cleaned


def _parse_json_loose(text: str) -> dict[str, Any] | None:
    import json
    import re

    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
