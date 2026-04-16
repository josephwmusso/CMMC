"""
src/scanners/ciscat_importer.py

Persist a parsed CIS-CAT result into the platform:
  - match rules to baseline_items by cis_id (scoped to the benchmark
    whose title best matches the CIS-CAT report's benchmark.title)
  - auto-adopt the baseline for the org if not already ACTIVE
  - create a DRAFT SCAN_REPORT evidence artifact
  - insert a scan_imports row (scan_type='CISCAT')
  - insert baseline_deviations for fail/error/unknown rules
    (scan_finding_id is NULL — CIS-CAT deviations don't come from Nessus
    findings; the rule-to-deviation link goes via cis_id)
  - write one SCAN_IMPORTED audit entry on the canonical hash chain

Mirrors the flow in src/api/routes_scans.py::upload_scan so the two
importers share one transactional pattern.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.scanners.ciscat_parser import (
    CiscatResult,
    generate_ciscat_summary,
    parse_ciscat_json,
)

logger = logging.getLogger(__name__)


def _gen_id(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()[:20]


def _safe_user_fk(db: Session, user_id: Optional[str]) -> Optional[str]:
    """scan_imports.imported_by / baseline_deviations.resolved_by FK into
    users. The ALLOW_ANONYMOUS dev bypass hands us 'dev-user' which isn't
    a real row. Return None rather than fail the whole import."""
    if not user_id:
        return None
    row = db.execute(
        text("SELECT 1 FROM users WHERE id = :id"),
        {"id": user_id},
    ).fetchone()
    return user_id if row else None


def _audit(db: Session, *, actor: str, action: str, target_id: str, details: dict) -> None:
    try:
        from src.evidence.state_machine import create_audit_entry
        create_audit_entry(
            db=db,
            actor=actor,
            actor_type="user",
            action=action,
            target_type="SCAN_IMPORT",
            target_id=target_id,
            details=details,
        )
    except Exception:
        logger.exception("audit entry %s failed", action)


def _match_baseline(db: Session, report: CiscatResult) -> Optional[dict]:
    """Find a catalog baseline whose title overlaps with the CIS-CAT
    benchmark.title. Prefers longest-substring match to keep Win11 vs
    M365 disambiguation unambiguous.

    Returns a dict with {baseline_id, name, platform} or None.
    """
    rows = db.execute(text("""
        SELECT id, name, platform FROM baselines
    """)).fetchall()
    if not rows:
        return None

    rpt_title_lower = report.benchmark_title.lower()
    best: Optional[tuple[int, dict]] = None
    for row in rows:
        name_lower = (row.name or "").lower()
        platform_lower = (row.platform or "").lower()
        # Score: platform hit + count of name tokens present in report title.
        score = 0
        if platform_lower and platform_lower in rpt_title_lower:
            score += 50
        if name_lower and name_lower in rpt_title_lower:
            score += 100
        # Token overlap fallback.
        for tok in set(name_lower.split()) | set(platform_lower.split()):
            if len(tok) >= 4 and tok in rpt_title_lower:
                score += 1
        if score > 0 and (best is None or score > best[0]):
            best = (score, {"baseline_id": row.id, "name": row.name, "platform": row.platform})
    return best[1] if best else None


def _ensure_adoption(db: Session, org_id: str, baseline_id: str) -> tuple[str, bool]:
    """Return (org_baseline_id, auto_adopted). Creates an ACTIVE
    org_baseline if none exists or re-activates an ARCHIVED one."""
    now = datetime.now(timezone.utc)
    row = db.execute(text("""
        SELECT id, status FROM org_baselines
        WHERE org_id = :org_id AND baseline_id = :baseline_id
    """), {"org_id": org_id, "baseline_id": baseline_id}).fetchone()

    if row is None:
        ob_id = _gen_id(f"ob:{org_id}:{baseline_id}")
        db.execute(text("""
            INSERT INTO org_baselines (id, org_id, baseline_id, adopted_at, status)
            VALUES (:id, :org_id, :baseline_id, :now, 'ACTIVE')
        """), {"id": ob_id, "org_id": org_id, "baseline_id": baseline_id, "now": now})
        return ob_id, True

    if row.status != "ACTIVE":
        db.execute(text("""
            UPDATE org_baselines
            SET status = 'ACTIVE', adopted_at = :now
            WHERE id = :id
        """), {"id": row.id, "now": now})
        return row.id, True

    return row.id, False


def _build_deviation_note(rule, baseline_severity: Optional[str]) -> str:
    parts = [f"CIS-CAT result: {rule.result.upper()}"]
    if rule.title:
        parts.append(rule.title)
    if rule.expected_value or rule.actual_value:
        parts.append(f"expected={rule.expected_value or '?'} actual={rule.actual_value or '?'}")
    sev = rule.severity or baseline_severity
    if sev:
        parts.append(f"severity={sev}")
    return " | ".join(parts)[:1000]


def _build_actual_value(rule) -> str:
    if rule.actual_value and rule.expected_value:
        return f"{rule.actual_value} (expected {rule.expected_value})"
    if rule.actual_value:
        return rule.actual_value[:500]
    return rule.title[:500]


def import_ciscat_report(
    file_content: bytes,
    *,
    filename: str,
    org_id: str,
    user_id: str,
    user_email: Optional[str],
    db: Session,
) -> dict:
    """Parse + persist one CIS-CAT JSON report. Owns its db.commit()s.

    Raises ValueError for malformed input (route maps to 400).
    """
    report: CiscatResult = parse_ciscat_json(file_content)
    safe_user_id = _safe_user_fk(db, user_id)

    # ── 1. Match to a catalog baseline ────────────────────────────────────
    matched = _match_baseline(db, report)
    if matched is None:
        # Log a FAILED scan_import so the list endpoint shows the attempt.
        scan_id = _gen_id(f"ciscat:{org_id}:{filename}:{datetime.now(timezone.utc).isoformat()}")
        db.execute(text("""
            INSERT INTO scan_imports
                (id, org_id, filename, scan_type, status, error_message, imported_by)
            VALUES
                (:id, :org_id, :filename, 'CISCAT', 'FAILED', :err, :imported_by)
        """), {
            "id":          scan_id,
            "org_id":      org_id,
            "filename":    filename,
            "err":         f"No catalog baseline matches '{report.benchmark_title}'",
            "imported_by": safe_user_id,
        })
        db.commit()
        raise ValueError(
            f"No seeded baseline matches '{report.benchmark_title}'. "
            "Seed the catalog with this benchmark first."
        )

    baseline_id   = matched["baseline_id"]
    baseline_name = matched["name"]

    # ── 2. Ensure the org has adopted the baseline ───────────────────────
    org_baseline_id, auto_adopted = _ensure_adoption(db, org_id, baseline_id)

    # ── 3. Load baseline_items indexed by cis_id ─────────────────────────
    item_rows = db.execute(text("""
        SELECT id, cis_id, control_ids, severity
        FROM baseline_items
        WHERE baseline_id = :bid
    """), {"bid": baseline_id}).fetchall()
    items_by_cis_id = {r.cis_id: r for r in item_rows if r.cis_id}

    # ── 4. Generate IDs + evidence artifact ──────────────────────────────
    now = datetime.now(timezone.utc)
    scan_id = _gen_id(f"ciscat:{org_id}:{filename}:{now.isoformat()}")
    evidence_id = _gen_id(f"evidence:ciscat:{scan_id}")

    summary_text = generate_ciscat_summary(report)
    artifact_name = f"CIS-CAT Report - {report.benchmark_title} ({now.strftime('%Y-%m-%d')})"[:500]

    db.execute(text("""
        INSERT INTO evidence_artifacts
            (id, org_id, filename, file_path, mime_type,
             state, evidence_type, source_system, description, owner, created_at)
        VALUES
            (:id, :org_id, :filename, '', 'application/json',
             'DRAFT', 'SCAN_REPORT', 'CIS-CAT', :description, :owner, NOW())
    """), {
        "id":          evidence_id,
        "org_id":      org_id,
        "filename":    artifact_name,
        "description": summary_text[:4000],
        "owner":       user_email or user_id,
    })

    # ── 5. Link evidence to every control covered by matched items ───────
    # Collect control_ids from all items whose cis_id appears in the
    # report (pass or fail — the artifact attests the scan happened
    # against those controls).
    reported_cis_ids = {r.cis_id for r in report.rules if r.cis_id}
    covered_controls: set[str] = set()
    for cid, item in items_by_cis_id.items():
        if cid in reported_cis_ids:
            for ctrl in (item.control_ids or []):
                covered_controls.add(ctrl)

    if covered_controls:
        valid_rows = db.execute(
            text("SELECT id FROM controls WHERE id = ANY(:ids)"),
            {"ids": list(covered_controls)},
        ).fetchall()
        valid_ids = {r[0] for r in valid_rows}
        for ctrl in sorted(covered_controls & valid_ids):
            link_id = _gen_id(f"evcm:{evidence_id}:{ctrl}")
            db.execute(text("""
                INSERT INTO evidence_control_map (id, evidence_id, control_id, mapped_by)
                VALUES (:id, :eid, :cid, 'ciscat_importer')
                ON CONFLICT (evidence_id, control_id, objective_id) DO NOTHING
            """), {"id": link_id, "eid": evidence_id, "cid": ctrl})

    # ── 6. scan_imports row ──────────────────────────────────────────────
    # scan_findings are NOT populated for CIS-CAT — deviations carry the
    # per-rule detail. finding_count therefore reflects deviation count.
    deviation_rules = [r for r in report.rules if r.is_deviation]

    db.execute(text("""
        INSERT INTO scan_imports
            (id, org_id, filename, scan_type, scanner_version, scan_date,
             imported_by, host_count, finding_count,
             critical_count, high_count, medium_count, low_count, info_count,
             status, evidence_artifact_id, summary_text)
        VALUES
            (:id, :org_id, :filename, 'CISCAT', :version, :scan_date,
             :imported_by, :host_count, :finding_count,
             :c, :h, :m, :l, :i,
             'COMPLETE', :evidence_id, :summary)
    """), {
        "id":            scan_id,
        "org_id":        org_id,
        "filename":      filename,
        "version":       f"{report.benchmark_title} {report.benchmark_version}".strip()[:100],
        "scan_date":     report.scan_timestamp,
        "imported_by":   safe_user_id,
        "host_count":    1 if report.target_host else 0,
        "finding_count": len(deviation_rules),
        "c": 0, "h": 0, "m": 0, "l": 0, "i": 0,
        "evidence_id":   evidence_id,
        "summary":       summary_text[:5000],
    })

    # ── 7. baseline_deviations per failing rule ──────────────────────────
    deviations_created = 0
    deviations_skipped = 0
    unmatched_cis_ids:  list[str] = []

    for rule in deviation_rules:
        if not rule.cis_id:
            unmatched_cis_ids.append(rule.rule_id)
            continue
        item = items_by_cis_id.get(rule.cis_id)
        if item is None:
            unmatched_cis_ids.append(rule.cis_id)
            continue

        # One deviation per (org_baseline, item, scan_import).
        dev_id = _gen_id(f"dev:ciscat:{org_baseline_id}:{item.id}:{scan_id}")

        existing = db.execute(text("""
            SELECT 1 FROM baseline_deviations WHERE id = :id
        """), {"id": dev_id}).fetchone()
        if existing:
            deviations_skipped += 1
            continue

        db.execute(text("""
            INSERT INTO baseline_deviations
                (id, org_id, org_baseline_id, baseline_item_id,
                 scan_finding_id, actual_value, status, notes, detected_at)
            VALUES
                (:id, :org_id, :ob_id, :item_id,
                 NULL, :actual, 'OPEN', :notes, :now)
        """), {
            "id":      dev_id,
            "org_id":  org_id,
            "ob_id":   org_baseline_id,
            "item_id": item.id,
            "actual":  _build_actual_value(rule),
            "notes":   _build_deviation_note(rule, item.severity),
            "now":     now,
        })
        deviations_created += 1

    db.commit()

    # ── 8. Audit entry ───────────────────────────────────────────────────
    _audit(db, actor=user_id, action="SCAN_IMPORTED", target_id=scan_id, details={
        "source_type":         "CISCAT",
        "filename":            filename,
        "org_id":              org_id,
        "baseline_id":         baseline_id,
        "baseline_name":       baseline_name,
        "org_baseline_id":     org_baseline_id,
        "auto_adopted":        auto_adopted,
        "total_rules":         report.total_count,
        "pass":                report.pass_count,
        "fail":                report.fail_count,
        "error":               report.error_count,
        "unknown":             report.unknown_count,
        "deviations_created":  deviations_created,
        "evidence_artifact_id": evidence_id,
    })
    db.commit()

    return {
        "scan_id":              scan_id,
        "source_type":          "CISCAT",
        "filename":             filename,
        "status":               "COMPLETE",
        "benchmark_title":      report.benchmark_title,
        "benchmark_version":    report.benchmark_version,
        "baseline_id":          baseline_id,
        "baseline_name":        baseline_name,
        "org_baseline_id":      org_baseline_id,
        "auto_adopted":         auto_adopted,
        "total_rules":          report.total_count,
        "pass_count":           report.pass_count,
        "fail_count":           report.fail_count,
        "error_count":          report.error_count,
        "unknown_count":        report.unknown_count,
        "deviations_created":   deviations_created,
        "deviations_skipped":   deviations_skipped,
        "unmatched_cis_ids":    unmatched_cis_ids,
        "controls_mapped":      len(covered_controls),
        "evidence_artifact_id": evidence_id,
    }
