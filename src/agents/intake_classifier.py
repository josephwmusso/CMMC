"""
src/agents/intake_classifier.py

LLM-backed classification of free-text intake answers into one of the
predefined options for a given question. Used by
POST /api/intake/interpret.

Returns a structured dict with the best-match option value, extracted
tool names, compliance notes, and a short SSP narrative fragment that
the document generator can lift verbatim.

Uses the existing ComplianceLLM wrapper so the same provider/model
config governs classification as SSP generation (Claude Sonnet in dev,
vLLM in prod).
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from src.agents.llm_client import get_llm

logger = logging.getLogger(__name__)


_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def _normalize_options(raw_options: Any) -> list[dict]:
    """Options may be list[str] (Module 0) or list[dict] (Module 1).
    Normalize both into [{'value': ..., 'label': ...}, ...]."""
    out: list[dict] = []
    if not raw_options:
        return out
    for opt in raw_options:
        if isinstance(opt, str):
            out.append({"value": opt, "label": opt})
        elif isinstance(opt, dict):
            value = opt.get("value", opt.get("label", ""))
            label = opt.get("label", value)
            out.append({"value": value, "label": label})
    return out


def build_classification_prompt(question: dict, free_text: str) -> str:
    """Build the LLM prompt for classifying a free-text intake response."""
    options = _normalize_options(question.get("options"))
    options_text = "\n".join(
        f'  - value: "{opt["value"]}" | label: "{opt["label"]}"'
        for opt in options
    )
    control_ids = ", ".join(question.get("control_ids") or [])

    return f"""You are a CMMC Level 2 compliance analyst classifying an organization's
free-text description of their IT environment into structured intake data for
a compliance assessment platform.

QUESTION: {question.get("text", "")}
QUESTION_ID: {question.get("id", "")}
NIST 800-171 CONTROLS AFFECTED: {control_ids}

AVAILABLE OPTIONS (the user should be classified into one of these):
{options_text}

USER'S FREE-TEXT DESCRIPTION:
"{free_text}"

INSTRUCTIONS:
1. Determine which option BEST matches the user's description. Consider the primary tool/approach described, not secondary or ancillary tools.
2. If the description clearly matches one option, set best_match_value to that option's value.
3. If the description doesn't match ANY option well (e.g., they describe a tool not listed), set best_match_value to null.
4. Extract all specific product names, tools, and vendors mentioned.
5. Extract specific configurations mentioned (MFA, encryption, federation, etc.).
6. Assess compliance implications for the affected NIST controls.
7. Note any compliance gaps revealed by the description that the predefined options wouldn't catch.
8. Write 2-3 sentences suitable for an SSP implementation narrative — specific to what they described, not generic.

Respond with ONLY a JSON object (no markdown, no explanation):
{{
  "best_match_value": "<option value or null>",
  "extracted_tools": ["<product/tool names>"],
  "extracted_configurations": ["<specific configs mentioned>"],
  "compliance_notes": "<1-2 sentences on compliance implications for the affected controls>",
  "gap_indicators": ["<any compliance gaps revealed>"],
  "creates_gap": <true if description reveals a gap the options wouldn't catch>,
  "gap_severity": "<CRITICAL|HIGH|MEDIUM|null>",
  "ssp_narrative_context": "<2-3 sentences for an SSP implementation narrative>"
}}"""


def _strip_markdown_fences(raw: str) -> str:
    """LLMs sometimes wrap JSON in ```json ... ``` fences. Strip them."""
    s = raw.strip()
    s = _JSON_FENCE_RE.sub("", s).strip()
    return s


def _parse_classification(raw: str) -> Optional[dict]:
    """Parse the LLM's JSON response. Returns None on malformed output."""
    cleaned = _strip_markdown_fences(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find a {...} block inside the response as a last resort.
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                return None
        return None


def _label_for_value(question: dict, value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    for opt in _normalize_options(question.get("options")):
        if opt["value"] == value:
            return opt["label"]
    return None


def classify_free_text(question: dict, free_text: str) -> dict:
    """Run the LLM classification for a single free-text answer.

    Returns a dict shaped for the /interpret endpoint response:
      {
        "best_match_value": ...,
        "best_match_label": ...,
        "extracted_tools": [...],
        "extracted_configurations": [...],
        "compliance_notes": "...",
        "gap_indicators": [...],
        "creates_gap": bool,
        "gap_severity": ...,
        "ssp_narrative_context": "...",
      }

    Raises RuntimeError on LLM/parse failure; the caller maps that to 503.
    """
    llm = get_llm()
    system_prompt = (
        "You are a precise CMMC compliance analyst. "
        "Return only valid JSON — no preamble, no trailing commentary."
    )
    user_prompt = build_classification_prompt(question, free_text)

    raw = llm.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=1024,
        temperature=0.1,
    )

    parsed = _parse_classification(raw)
    if parsed is None:
        logger.warning("Classification JSON parse failed. Raw: %s", raw[:500])
        raise RuntimeError("classification parse failed")

    best_match_value = parsed.get("best_match_value")
    # LLM may return the string "null" rather than JSON null.
    if isinstance(best_match_value, str) and best_match_value.strip().lower() in ("null", "none", ""):
        best_match_value = None

    return {
        "best_match_value":         best_match_value,
        "best_match_label":         _label_for_value(question, best_match_value),
        "extracted_tools":          parsed.get("extracted_tools") or [],
        "extracted_configurations": parsed.get("extracted_configurations") or [],
        "compliance_notes":         parsed.get("compliance_notes") or "",
        "gap_indicators":           parsed.get("gap_indicators") or [],
        "creates_gap":              bool(parsed.get("creates_gap")),
        "gap_severity":             parsed.get("gap_severity"),
        "ssp_narrative_context":    parsed.get("ssp_narrative_context") or "",
    }
