"""
src/scanners/ciscat_parser.py

Parse CIS-CAT Pro Assessor JSON output into structured rule results.
Pure parser — no DB access. Mirrors the shape of nessus_parser.py so the
importer can follow the same flow.

Expected input shape (relaxed; extra fields ignored):
  {
    "benchmark": {"title": str, "version": str, "profile": str},
    "rules": [
      {
        "rule_id": "xccdf_org.cisecurity.benchmarks_rule_X.Y.Z",
        "title": str,
        "result": "pass" | "fail" | "error" | "unknown" | "notchecked" | "informational",
        "actual_value": str (optional),
        "expected_value": str (optional),
        "severity": "critical" | "high" | "medium" | "low" | "info" (optional),
        "description": str (optional)
      },
      ...
    ],
    "summary": {"total": int, "pass": int, "fail": int, "error": int, "unknown": int},
    "timestamp": ISO8601 str (optional),
    "target_host": str (optional)
  }
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Union

logger = logging.getLogger(__name__)


_XCCDF_RULE_RE = re.compile(
    r"^xccdf_org\.cisecurity\.benchmarks_rule_(.+)$"
)

# CIS-CAT result states that become deviations. "pass" is compliant;
# "notchecked"/"informational" are treated as informational (no deviation).
_DEVIATION_RESULTS = {"fail", "error", "unknown"}

_SEVERITY_CANON = {
    "critical": "CRITICAL",
    "high":     "HIGH",
    "medium":   "MEDIUM",
    "low":      "LOW",
    "info":     "LOW",
    "informational": "LOW",
}


@dataclass
class CiscatRule:
    rule_id:        str
    cis_id:         Optional[str]
    title:          str
    result:         str           # normalized lowercase: pass/fail/error/unknown/...
    actual_value:   Optional[str]
    expected_value: Optional[str]
    severity:       Optional[str] # UPPERCASE when present
    description:    Optional[str]

    @property
    def is_deviation(self) -> bool:
        return self.result in _DEVIATION_RESULTS


@dataclass
class CiscatResult:
    benchmark_title:   str
    benchmark_version: str
    benchmark_profile: Optional[str]
    target_host:       Optional[str]
    scan_timestamp:    Optional[datetime]
    rules:             list[CiscatRule]
    pass_count:        int = 0
    fail_count:        int = 0
    error_count:       int = 0
    unknown_count:     int = 0
    total_count:       int = 0


# ── Public helpers ────────────────────────────────────────────────────────

def extract_cis_id(rule_id: Optional[str]) -> Optional[str]:
    """Strip the XCCDF prefix to get the bare CIS rule number (e.g. "1.1.1").

    Returns None if ``rule_id`` is empty or doesn't match the canonical
    XCCDF naming used by CIS-CAT. Malformed rule_ids are logged at debug
    level and otherwise ignored so a single stray rule can't break the
    whole import.
    """
    if not rule_id:
        return None
    m = _XCCDF_RULE_RE.match(rule_id.strip())
    if not m:
        # Some older CIS-CAT profiles emit bare numbers. Accept those too.
        bare = rule_id.strip()
        if re.match(r"^\d+(\.\d+)*$", bare):
            return bare
        logger.debug("Unrecognised rule_id format: %s", rule_id)
        return None
    return m.group(1).strip()


def _parse_timestamp(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    s = raw.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def parse_ciscat_json(file_content: Union[bytes, str]) -> CiscatResult:
    """Parse a CIS-CAT Pro Assessor JSON export.

    Raises ``ValueError`` for malformed JSON or a missing ``rules`` list —
    the importer maps those to a 400 so the client gets a clear message.
    """
    if isinstance(file_content, bytes):
        file_content = file_content.decode("utf-8", errors="replace")

    try:
        data = json.loads(file_content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Root JSON element must be an object")

    benchmark = data.get("benchmark") or {}
    if not isinstance(benchmark, dict) or not benchmark.get("title"):
        raise ValueError("Missing or invalid 'benchmark' object — not a CIS-CAT export")

    rules_raw = data.get("rules")
    if not isinstance(rules_raw, list):
        raise ValueError("Missing or invalid 'rules' array")

    rules: list[CiscatRule] = []
    pass_ct = fail_ct = error_ct = unknown_ct = 0

    for raw in rules_raw:
        if not isinstance(raw, dict):
            continue
        rule_id = str(raw.get("rule_id") or "").strip()
        cis_id  = extract_cis_id(rule_id)
        result  = str(raw.get("result") or "unknown").strip().lower()

        sev_raw = raw.get("severity")
        sev = _SEVERITY_CANON.get(str(sev_raw).lower()) if sev_raw else None

        rules.append(CiscatRule(
            rule_id=        rule_id,
            cis_id=         cis_id,
            title=          str(raw.get("title") or "").strip(),
            result=         result,
            actual_value=   (str(raw["actual_value"])   if raw.get("actual_value")   is not None else None),
            expected_value= (str(raw["expected_value"]) if raw.get("expected_value") is not None else None),
            severity=       sev,
            description=    (str(raw["description"]).strip() if raw.get("description") else None),
        ))

        if   result == "pass":    pass_ct    += 1
        elif result == "fail":    fail_ct    += 1
        elif result == "error":   error_ct   += 1
        elif result == "unknown": unknown_ct += 1

    # Prefer the explicit summary when present; otherwise fall back to
    # what we counted from the rules list.
    summary = data.get("summary") or {}
    if isinstance(summary, dict):
        pass_ct    = int(summary.get("pass",    pass_ct))
        fail_ct    = int(summary.get("fail",    fail_ct))
        error_ct   = int(summary.get("error",   error_ct))
        unknown_ct = int(summary.get("unknown", unknown_ct))
        total_ct   = int(summary.get("total",   len(rules)))
    else:
        total_ct   = len(rules)

    return CiscatResult(
        benchmark_title=   str(benchmark.get("title", "")).strip(),
        benchmark_version= str(benchmark.get("version", "")).strip(),
        benchmark_profile= (str(benchmark["profile"]).strip() if benchmark.get("profile") else None),
        target_host=       (str(data["target_host"]).strip() if data.get("target_host") else None),
        scan_timestamp=    _parse_timestamp(data.get("timestamp")),
        rules=             rules,
        pass_count=        pass_ct,
        fail_count=        fail_ct,
        error_count=       error_ct,
        unknown_count=     unknown_ct,
        total_count=       total_ct,
    )


def generate_ciscat_summary(result: CiscatResult) -> str:
    """Human-readable summary used as the evidence artifact description."""
    deviations = [r for r in result.rules if r.is_deviation]
    lines = [
        f"CIS-CAT Benchmark Report: {result.benchmark_title} {result.benchmark_version}",
    ]
    if result.benchmark_profile:
        lines.append(f"Profile: {result.benchmark_profile}")
    if result.target_host:
        lines.append(f"Target Host: {result.target_host}")
    if result.scan_timestamp:
        lines.append(f"Scan Date: {result.scan_timestamp.strftime('%Y-%m-%d %H:%M')}")
    lines += [
        "",
        "Result Summary:",
        f"  Total Rules: {result.total_count}",
        f"  Pass:        {result.pass_count}",
        f"  Fail:        {result.fail_count}",
        f"  Error:       {result.error_count}",
        f"  Unknown:     {result.unknown_count}",
        "",
    ]
    if deviations:
        lines.append("Top Deviations:")
        for r in deviations[:10]:
            sev = r.severity or "MEDIUM"
            cid = r.cis_id or "?"
            lines.append(f"  [{r.result.upper()}][{sev}] {cid}: {r.title[:120]}")
            if r.expected_value or r.actual_value:
                lines.append(
                    f"    expected={r.expected_value or '?'}  actual={r.actual_value or '?'}"
                )
    else:
        lines.append("No deviations detected.")

    return "\n".join(lines)
