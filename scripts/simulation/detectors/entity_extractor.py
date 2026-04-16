"""Entity extraction via spaCy NER + regex patterns for IPs, hostnames,
plugin IDs, CVEs, and control IDs."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
        except (ImportError, OSError) as e:
            import warnings
            warnings.warn(f"spaCy unavailable: {e}. NER disabled — only regex patterns active.")
            _nlp = "unavailable"
    return _nlp


@dataclass
class Entity:
    text: str
    label: str        # NER label or pattern type
    start: int
    end: int
    canonical: str    # lowered/stripped form


def extract_entities(text: str) -> List[Entity]:
    nlp = _get_nlp()
    if nlp == "unavailable" or not text:
        return []
    doc = nlp(text)
    return [
        Entity(
            text=ent.text,
            label=ent.label_,
            start=ent.start_char,
            end=ent.end_char,
            canonical=ent.text.strip().lower(),
        )
        for ent in doc.ents
        if ent.label_ in ("ORG", "PRODUCT", "PERSON", "GPE", "DATE", "CARDINAL")
    ]


_IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_PLUGIN_RE = re.compile(r"\b(?:plugin\s+(?:id\s+)?|Plugin\s+)(\d{4,6})\b", re.IGNORECASE)
_CVE_RE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b")
_CONTROL_RE = re.compile(r"\b[A-Z]{2}\.L[12]-\d+\.\d+\.\d+\b")
_HOSTNAME_RE = re.compile(r"\b([a-z][a-z0-9]*-(?:[a-z0-9]+-)*[a-z0-9]{2,})\b")
_CIS_ID_RE = re.compile(r"\b(\d{1,2}\.\d{1,2}(?:\.\d{1,2})?)\b")


def extract_ips(text: str) -> List[str]:
    return _IP_RE.findall(text)


def extract_plugin_ids(text: str) -> List[str]:
    return _PLUGIN_RE.findall(text)


def extract_cves(text: str) -> List[str]:
    return _CVE_RE.findall(text)


def extract_control_ids(text: str) -> List[str]:
    return _CONTROL_RE.findall(text)


_HOSTNAME_EXCLUDE = {
    "deny-by-default", "real-time", "role-based", "end-to-end", "day-to-day",
    "up-to-date", "on-premises", "multi-factor", "non-compliant", "two-factor",
    "least-privilege", "need-to-know", "out-of-date", "air-gapped", "off-site",
    "pass-through", "write-once", "read-only", "sign-in", "log-in", "third-party",
}


def extract_hostnames(text: str) -> List[str]:
    matches = _HOSTNAME_RE.findall(text.lower())
    return [m for m in matches if len(m) >= 6 and m not in _HOSTNAME_EXCLUDE]


def extract_cis_ids(text: str) -> List[str]:
    context_re = re.compile(r"(?:CIS|rule|benchmark|check)\s+(?:id\s+)?(\d{1,2}\.\d{1,2}(?:\.\d{1,2})?)", re.IGNORECASE)
    return context_re.findall(text)
