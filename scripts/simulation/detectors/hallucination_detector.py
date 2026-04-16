"""Hallucination detector — scans AI-generated text against grounding
universe + forbidden list. Model-agnostic, deterministic."""
from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from scripts.simulation.detectors.entity_extractor import (
    extract_control_ids,
    extract_cves,
    extract_entities,
    extract_hostnames,
    extract_ips,
    extract_plugin_ids,
)
from scripts.simulation.detectors.categorizer import categorize


@dataclass
class Hit:
    category: str       # FORBIDDEN_TOOL, UNGROUNDED_TOOL, BAD_IP, etc.
    severity: str       # violation | warning | info
    entity: str
    span: Tuple[int, int]
    context: str
    reason: str


@dataclass
class DetectorReport:
    artifact_id: str
    artifact_type: str
    control_ids: List[str]
    text_scanned: str
    hits: List[Hit] = field(default_factory=list)
    severity: str = "clean"
    summary: Dict[str, int] = field(default_factory=dict)


def _context(text: str, start: int, end: int, window: int = 40) -> str:
    s = max(0, start - window)
    e = min(len(text), end + window)
    return text[s:e].replace("\n", " ")


def _word_boundary_match(text_lower: str, term_lower: str) -> Optional[Tuple[int, int]]:
    pattern = r"\b" + re.escape(term_lower) + r"\b"
    m = re.search(pattern, text_lower, re.IGNORECASE)
    if m:
        return (m.start(), m.end())
    return None


def detect(
    text: str,
    *,
    artifact_id: str = "unknown",
    artifact_type: str = "ssp_narrative",
    control_ids: Optional[List[str]] = None,
    grounding_universe: Optional[Dict[str, Any]] = None,
    forbidden: Optional[Dict[str, Any]] = None,
) -> DetectorReport:
    """Run the full detection pipeline on one artifact."""
    report = DetectorReport(
        artifact_id=artifact_id,
        artifact_type=artifact_type,
        control_ids=control_ids or [],
        text_scanned=text,
    )
    if not text or not text.strip():
        return report

    text_lower = text.lower()
    grounding = grounding_universe or {}
    forbid = forbidden or {}

    # ── 1. Forbidden list check ──────────────────────────────────────────
    for tool in forbid.get("forbidden_tools", []):
        match = _word_boundary_match(text_lower, tool.lower())
        if match:
            report.hits.append(Hit(
                category="FORBIDDEN_TOOL",
                severity="violation",
                entity=tool,
                span=match,
                context=_context(text, *match),
                reason=f"Forbidden tool '{tool}' found in output",
            ))

    # IP check
    allowed_cidr = forbid.get("forbidden_ip_ranges", {}).get("allowed_cidr")
    allowed_net = None
    if allowed_cidr:
        try:
            allowed_net = ipaddress.ip_network(allowed_cidr, strict=False)
        except ValueError:
            pass

    for ip_str in extract_ips(text):
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if allowed_net and ip in allowed_net:
            continue
        idx = text.find(ip_str)
        span = (idx, idx + len(ip_str)) if idx >= 0 else (0, 0)
        report.hits.append(Hit(
            category="BAD_IP",
            severity="violation",
            entity=ip_str,
            span=span,
            context=_context(text, *span),
            reason=f"IP {ip_str} not in allowed range {allowed_cidr}",
        ))

    # Hostname check
    allowed_hosts = {h.lower() for h in forbid.get("allowed_hostnames", [])}
    for hostname in extract_hostnames(text):
        if hostname in allowed_hosts:
            continue
        idx = text_lower.find(hostname)
        span = (idx, idx + len(hostname)) if idx >= 0 else (0, 0)
        report.hits.append(Hit(
            category="BAD_HOSTNAME",
            severity="warning",
            entity=hostname,
            span=span,
            context=_context(text, *span),
            reason=f"Hostname '{hostname}' not in allowed list",
        ))

    # ── 2. Fabricated citation check ─────────────────────────────────────
    known_plugins = set(str(p) for p in forbid.get("_known_plugin_ids", []))
    for pid in extract_plugin_ids(text):
        if pid in known_plugins:
            continue
        idx = text.find(pid)
        span = (idx, idx + len(pid)) if idx >= 0 else (0, 0)
        report.hits.append(Hit(
            category="FABRICATED_CITATION",
            severity="violation",
            entity=f"plugin {pid}",
            span=span,
            context=_context(text, *span),
            reason=f"Plugin ID {pid} not in known scan findings",
        ))

    known_cves = set(forbid.get("_known_cves", []))
    for cve in extract_cves(text):
        if cve in known_cves:
            continue
        idx = text.find(cve)
        span = (idx, idx + len(cve)) if idx >= 0 else (0, 0)
        report.hits.append(Hit(
            category="FABRICATED_CITATION",
            severity="warning",
            entity=cve,
            span=span,
            context=_context(text, *span),
            reason=f"CVE {cve} not in known scan findings",
        ))

    # Evidence title fuzzy match
    allowed_titles = forbid.get("allowed_evidence_titles", [])
    ev_ref_re = re.compile(r'(?:per the |as documented in the |per our )[""]?([^""\n,;]{5,60})[""]?', re.IGNORECASE)
    for m in ev_ref_re.finditer(text):
        ref = m.group(1).strip()
        best_ratio = max(
            (SequenceMatcher(None, ref.lower(), t.lower()).ratio() for t in allowed_titles),
            default=0.0,
        )
        if best_ratio < 0.85:
            report.hits.append(Hit(
                category="FABRICATED_CITATION",
                severity="warning",
                entity=ref,
                span=(m.start(1), m.end(1)),
                context=_context(text, m.start(), m.end()),
                reason=f"Evidence reference '{ref}' doesn't match any known title (best ratio: {best_ratio:.2f})",
            ))

    # ── 3. Entity extraction + grounding ─────────────────────────────────
    grounding_tools_lower = {t.lower() for t in grounding.get("tools", [])}
    grounding_terms_lower = {t.lower() for t in grounding.get("company_terms", [])}
    evidence_text = grounding.get("evidence_free_text", "")

    forbidden_facts = forbid.get("forbidden_facts", {}) or {}
    date_constraints = forbid.get("date_constraints", {}) or {}

    for ent in extract_entities(text):
        cat = categorize(ent)
        if cat == "SAFE_VOCAB":
            continue

        if cat == "POTENTIAL_HALLUCINATION":
            # Check tools grounding
            if ent.label in ("ORG", "PRODUCT"):
                grounded = (
                    ent.canonical in grounding_tools_lower
                    or ent.canonical in grounding_terms_lower
                    or ent.canonical in evidence_text
                    or any(SequenceMatcher(None, ent.canonical, t).ratio() >= 0.85
                           for t in grounding_tools_lower)
                    or any(SequenceMatcher(None, ent.canonical, t).ratio() >= 0.80
                           for t in grounding_terms_lower)
                    or any(ent.canonical in t for t in grounding_terms_lower)
                    or any(t in ent.canonical for t in grounding_terms_lower if len(t) >= 4)
                )
                if not grounded:
                    report.hits.append(Hit(
                        category="UNGROUNDED_TOOL",
                        severity="warning",
                        entity=ent.text,
                        span=(ent.start, ent.end),
                        context=_context(text, ent.start, ent.end),
                        reason=f"Entity '{ent.text}' ({ent.label}) not in grounding universe",
                    ))

            # Check employee count
            if ent.label == "CARDINAL":
                expected_count = forbidden_facts.get("employee_count_other_than")
                if expected_count is not None:
                    try:
                        num = int(ent.text.replace(",", ""))
                        count_context = text[max(0, ent.start - 30):ent.end + 30].lower()
                        if "employee" in count_context and num != expected_count:
                            report.hits.append(Hit(
                                category="EMPLOYEE_COUNT_WRONG",
                                severity="violation",
                                entity=ent.text,
                                span=(ent.start, ent.end),
                                context=_context(text, ent.start, ent.end),
                                reason=f"Employee count {num} != expected {expected_count}",
                            ))
                    except ValueError:
                        pass

            # Check dates
            if ent.label == "DATE":
                earliest = date_constraints.get("earliest_allowed")
                latest = date_constraints.get("latest_allowed")
                date_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", ent.text)
                if date_match and earliest and latest:
                    ds = date_match.group(0)
                    if ds < earliest or ds > latest:
                        report.hits.append(Hit(
                            category="DATE_OUT_OF_RANGE",
                            severity="violation",
                            entity=ds,
                            span=(ent.start, ent.end),
                            context=_context(text, ent.start, ent.end),
                            reason=f"Date {ds} outside range [{earliest}, {latest}]",
                        ))

    # ── 3b. Regex fallback: employee count (spaCy may miss CARDINAL) ────
    expected_count = (forbid.get("forbidden_facts") or {}).get("employee_count_other_than")
    if expected_count is not None:
        emp_re = re.compile(r"\b(\d{1,5})\s*(?:employees?|staff|personnel|workers)\b", re.IGNORECASE)
        for m in emp_re.finditer(text):
            num = int(m.group(1))
            if num != expected_count and num > 1:
                report.hits.append(Hit(
                    category="EMPLOYEE_COUNT_WRONG",
                    severity="violation",
                    entity=m.group(0),
                    span=(m.start(), m.end()),
                    context=_context(text, m.start(), m.end()),
                    reason=f"Employee count {num} != expected {expected_count}",
                ))

    # ── 4. Severity rollup ───────────────────────────────────────────────
    summary: Dict[str, int] = {}
    has_violation = False
    has_warning = False
    for h in report.hits:
        summary[h.category] = summary.get(h.category, 0) + 1
        if h.severity == "violation":
            has_violation = True
        elif h.severity == "warning":
            has_warning = True

    report.summary = summary
    if has_violation:
        report.severity = "violations"
    elif has_warning:
        report.severity = "warnings"
    else:
        report.severity = "clean"

    return report
