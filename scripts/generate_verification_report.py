"""Generate a self-contained HTML verification report from layer JSON results."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.verification.result_schema import (
    AssertionResult,
    LayerResult,
    VerificationReport,
    load_layer_result,
)


def parse_audit_file(path: Path) -> dict:
    """Extract finding counts from DATA_INTEGRITY_AUDIT.md."""
    summary = {
        "critical": {"total": 0, "resolved": 0},
        "high": {"total": 0, "resolved": 0},
        "medium": {"total": 0, "resolved": 0},
        "low": {"total": 0, "resolved": 0},
    }
    if not path.exists():
        return summary
    text = path.read_text(encoding="utf-8")
    for sev in ["critical", "high", "medium", "low"]:
        m = re.search(rf"(?i){sev}:\s*(\d+)", text[:500])
        if m:
            summary[sev]["total"] = int(m.group(1))
    # Count resolved
    resolved_section = text[text.find("## Resolution Status"):] if "## Resolution Status" in text else ""
    for sev in ["critical", "high"]:
        matches = re.findall(rf"(?i){sev}.*?all\s+(\d+)\s+resolved", resolved_section)
        if matches:
            summary[sev]["resolved"] = int(matches[0])
        else:
            count = resolved_section.lower().count(f"resolved") if sev in resolved_section.lower()[:200] else 0
            summary[sev]["resolved"] = min(count, summary[sev]["total"])
    return summary


def get_git_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=str(ROOT), stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


def build_report(results_dir: Path, audit_path: Path,
                 playwright_status: str = "SKIP") -> VerificationReport:
    layers = []
    for json_path in sorted(results_dir.glob("*.json")):
        try:
            layers.append(load_layer_result(json_path))
        except Exception as e:
            print(f"Warning: could not load {json_path}: {e}")

    if playwright_status != "SKIP":
        layers.append(LayerResult(
            layer_name="Browser E2E", layer_id="e2e",
            total=1, passed=1 if playwright_status == "PASS" else 0,
            failed=0 if playwright_status == "PASS" else 1,
            warned=0, skipped=0, duration_seconds=0,
            assertions=[AssertionResult(name="playwright_onboarding",
                                        status=playwright_status, message="Manual input")],
            environment="local",
            timestamp=datetime.now(timezone.utc).isoformat(),
        ))

    audit = parse_audit_file(audit_path)
    overall = "PASS" if all(l.failed == 0 for l in layers) else "FAIL"
    now = datetime.now(timezone.utc).isoformat()
    rid = hashlib.sha256(f"{now}{json.dumps([l.to_dict() for l in layers])}".encode()).hexdigest()[:16]

    return VerificationReport(
        report_id=rid,
        generated_at=now,
        environment=layers[0].environment if layers else "local",
        platform_version=get_git_hash(),
        layers=layers,
        audit_summary=audit,
        overall_status=overall,
    )


def render_html(report: VerificationReport) -> str:
    total_pass = sum(l.passed for l in report.layers)
    total_fail = sum(l.failed for l in report.layers)
    total_warn = sum(l.warned for l in report.layers)
    total_all = sum(l.total for l in report.layers)

    status_color = "#22c55e" if report.overall_status == "PASS" else "#ef4444"
    status_text = "ALL PASS" if report.overall_status == "PASS" else "FAILURES DETECTED"

    def badge(status):
        colors = {"PASS": "#22c55e", "FAIL": "#ef4444", "WARN": "#eab308", "SKIP": "#71717a"}
        c = colors.get(status, "#71717a")
        return f'<span style="background:{c};color:#fff;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600">{status}</span>'

    def audit_card(sev, data):
        total = data["total"]
        resolved = data["resolved"]
        color = "#22c55e" if resolved >= total and total > 0 else "#eab308" if resolved > 0 else "#71717a"
        return f'''<div style="text-align:center;padding:16px">
            <div style="font-size:11px;color:#a1a1aa;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px">{sev}</div>
            <div style="font-size:24px;font-weight:600;color:{color}">{resolved}/{total}</div>
            <div style="font-size:11px;color:#71717a">resolved</div>
        </div>'''

    layer_cards = ""
    for l in report.layers:
        lcolor = "#22c55e" if l.failed == 0 else "#ef4444"
        layer_cards += f'''<div style="background:#18181b;border:1px solid #27272a;border-radius:8px;padding:16px;text-align:center;min-width:140px">
            <div style="width:12px;height:12px;border-radius:50%;background:{lcolor};margin:0 auto 8px"></div>
            <div style="font-size:13px;color:#fafafa;font-weight:500">{l.layer_name}</div>
            <div style="font-size:12px;color:#a1a1aa;margin-top:4px">{l.passed}/{l.total} pass</div>
        </div>'''

    layer_details = ""
    for idx, l in enumerate(report.layers):
        rows = ""
        failed_first = sorted(l.assertions, key=lambda a: (0 if a.status == "FAIL" else 1 if a.status == "WARN" else 2))
        for a in failed_first:
            border = "border-left:3px solid #ef4444;" if a.status == "FAIL" else ""
            rows += f'''<tr style="{border}">
                <td style="padding:6px 12px">{badge(a.status)}</td>
                <td style="padding:6px 12px;color:#fafafa;font-size:12px;font-family:monospace">{a.name}</td>
                <td style="padding:6px 12px;color:#a1a1aa;font-size:12px">{a.message[:120]}</td>
            </tr>'''

        lcolor = "#22c55e" if l.failed == 0 else "#ef4444"
        dur = f"{l.duration_seconds:.0f}s" if l.duration_seconds else ""
        layer_details += f'''
        <div style="background:#18181b;border:1px solid #27272a;border-radius:8px;margin-bottom:16px;overflow:hidden">
            <div onclick="this.nextElementSibling.style.display=this.nextElementSibling.style.display==='none'?'block':'none'"
                 style="padding:16px 20px;cursor:pointer;display:flex;justify-content:space-between;align-items:center">
                <div style="display:flex;align-items:center;gap:12px">
                    <div style="width:10px;height:10px;border-radius:50%;background:{lcolor}"></div>
                    <span style="font-size:14px;font-weight:500;color:#fafafa">{l.layer_name}</span>
                    <span style="font-size:12px;color:#a1a1aa">{l.passed}/{l.total} pass {dur}</span>
                </div>
                <span style="color:#71717a;font-size:18px">▾</span>
            </div>
            <div style="display:none;border-top:1px solid #27272a">
                <table style="width:100%;border-collapse:collapse">
                    {rows}
                </table>
            </div>
        </div>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Intranest Verification Report</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#09090b; color:#fafafa; font-family:system-ui,-apple-system,sans-serif; }}
  @media print {{
    body {{ background:#fff; color:#000; }}
    [style*="display:none"] {{ display:block !important; }}
  }}
</style>
</head>
<body>
<div style="max-width:1200px;margin:0 auto;padding:24px">

  <!-- Header -->
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:32px;padding-bottom:20px;border-bottom:1px solid #27272a">
    <div>
      <div style="font-size:16px;font-weight:600;letter-spacing:-0.02em;color:#fafafa">INTRANEST</div>
      <div style="font-size:13px;color:#a1a1aa;margin-top:2px">Verification Report</div>
    </div>
    <div style="text-align:right">
      <div style="background:{status_color};color:#fff;padding:8px 20px;border-radius:8px;font-size:14px;font-weight:600;display:inline-block;margin-bottom:6px">{status_text}</div>
      <div style="font-size:11px;color:#71717a">{report.generated_at[:19]}Z &middot; {report.platform_version} &middot; {report.environment}</div>
    </div>
  </div>

  <!-- Summary strip -->
  <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:24px">
    {layer_cards}
    <div style="background:#18181b;border:1px solid #3b82f6;border-radius:8px;padding:16px;text-align:center;min-width:160px">
      <div style="font-size:24px;font-weight:700;color:#3b82f6">{total_pass}/{total_all}</div>
      <div style="font-size:12px;color:#a1a1aa;margin-top:4px">total assertions passed</div>
    </div>
  </div>

  <!-- Audit findings -->
  <div style="background:#18181b;border:1px solid #27272a;border-radius:8px;margin-bottom:24px;padding:20px">
    <div style="font-size:13px;font-weight:500;color:#fafafa;margin-bottom:12px">Data Integrity Audit Findings</div>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:#27272a;border-radius:6px;overflow:hidden">
      {audit_card("CRITICAL", report.audit_summary.get("critical") or dict(total=0, resolved=0))}
      {audit_card("HIGH", report.audit_summary.get("high") or dict(total=0, resolved=0))}
      {audit_card("MEDIUM", report.audit_summary.get("medium") or dict(total=0, resolved=0))}
      {audit_card("LOW", report.audit_summary.get("low") or dict(total=0, resolved=0))}
    </div>
  </div>

  <!-- Layer details -->
  {layer_details}

  <!-- Footer -->
  <div style="text-align:center;padding:20px;color:#52525b;font-size:11px">
    Generated by Intranest Verification Harness &middot; Report ID: {report.report_id}
  </div>

</div>
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description="Generate HTML verification report")
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--audit-file", default="docs/DATA_INTEGRITY_AUDIT.md")
    parser.add_argument("--playwright-status", default="SKIP", choices=["PASS", "FAIL", "SKIP"])
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    audit_path = Path(args.audit_file)
    output_path = Path(args.output)

    report = build_report(results_dir, audit_path, args.playwright_status)
    html = render_html(report)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Report generated: {output_path}")
    print(f"Overall: {report.overall_status} ({sum(l.passed for l in report.layers)}/{sum(l.total for l in report.layers)})")


if __name__ == "__main__":
    main()
