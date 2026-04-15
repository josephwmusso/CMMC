"""
src/api/routes_scans.py

Phase 3.1A — Nessus scan upload + findings API.

Key design choices (audit notes):
  * Evidence table has no 'name' column — we write to `filename` and use
    `evidence_type='SCAN_REPORT'`, `state='draft'`.
  * Evidence ↔ control mapping uses the human control string directly
    (controls.id IS the NIST id, no PK translation needed). mapped_by
    column is mandatory on evidence_control_map.
  * Audit entries go through state_machine.create_audit_entry — hand-
    rolling prev_hash / entry_hash breaks the global chain verifier.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.auth import get_current_user
from src.db.session import get_db
from src.scanners.nessus_parser import (
    UNIVERSAL_SCAN_CONTROLS,
    generate_scan_summary,
    parse_nessus_xml,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scans", tags=["scans"])

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB cap


def _gen_id(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()[:20]


def _audit(db: Session, *, actor: str, action: str, target_id: str, details: dict) -> None:
    """Best-effort canonical audit entry. Never raises — an audit failure
    must not prevent the user-visible action from completing."""
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


# ---------------------------------------------------------------------------
# POST /api/scans/upload
# ---------------------------------------------------------------------------

@router.post("/upload")
async def upload_scan(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Upload + parse a .nessus file. Creates:
      - scan_imports row
      - one scan_findings row per severity≥1 finding
      - a DRAFT evidence_artifacts row (SCAN_REPORT)
      - evidence_control_map rows for every mapped control
      - one audit_log entry (SCAN_IMPORTED)
    """
    org_id = current_user["org_id"]
    user_id = current_user["id"]

    if not file.filename or not file.filename.lower().endswith(".nessus"):
        raise HTTPException(status_code=400, detail="Only .nessus files are supported")

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

    scan_id = _gen_id(
        f"scan:{org_id}:{file.filename}:{datetime.now(timezone.utc).isoformat()}"
    )

    # ── Parse ─────────────────────────────────────────────────────────────
    try:
        result = parse_nessus_xml(content)
    except Exception as exc:
        logger.error("parse failure on %s: %s", file.filename, exc)
        # Persist a FAILED row so the list endpoint shows the attempt.
        db.execute(text("""
            INSERT INTO scan_imports (id, org_id, filename, status, error_message, imported_by)
            VALUES (:id, :org_id, :filename, 'FAILED', :err, :imported_by)
        """), {
            "id": scan_id, "org_id": org_id, "filename": file.filename,
            "err": str(exc)[:500], "imported_by": user_id,
        })
        db.commit()
        raise HTTPException(status_code=400, detail=f"Failed to parse scan file: {str(exc)[:200]}")

    summary = generate_scan_summary(result)

    # ── Evidence artifact (DRAFT SCAN_REPORT) ─────────────────────────────
    evidence_id = _gen_id(f"evidence:scan:{scan_id}")
    artifact_name = (
        f"Nessus Scan - {result.scan_name} "
        f"({datetime.now(timezone.utc).strftime('%Y-%m-%d')})"
    )[:500]

    db.execute(text("""
        INSERT INTO evidence_artifacts
            (id, org_id, filename, file_path, mime_type,
             state, evidence_type, source_system, description, owner, created_at)
        VALUES
            (:id, :org_id, :filename, '', 'application/xml',
             'DRAFT', 'SCAN_REPORT', 'Nessus', :description, :owner, NOW())
    """), {
        "id": evidence_id,
        "org_id": org_id,
        "filename": artifact_name,
        "description": summary[:4000],
        "owner": current_user.get("email") or user_id,
    })

    # ── Control mappings ──────────────────────────────────────────────────
    mapped_controls: set[str] = set(UNIVERSAL_SCAN_CONTROLS)
    for finding in result.findings:
        mapped_controls.update(finding.mapped_control_ids)

    if mapped_controls:
        valid_rows = db.execute(
            text("SELECT id FROM controls WHERE id = ANY(:ids)"),
            {"ids": list(mapped_controls)},
        ).fetchall()
        valid_ids = {r[0] for r in valid_rows}
        for cid in sorted(mapped_controls & valid_ids):
            link_id = _gen_id(f"evcm:{evidence_id}:{cid}")
            db.execute(text("""
                INSERT INTO evidence_control_map (id, evidence_id, control_id, mapped_by)
                VALUES (:id, :eid, :cid, 'nessus_parser')
                ON CONFLICT (evidence_id, control_id, objective_id) DO NOTHING
            """), {"id": link_id, "eid": evidence_id, "cid": cid})

    # ── scan_imports row ─────────────────────────────────────────────────
    db.execute(text("""
        INSERT INTO scan_imports
            (id, org_id, filename, scan_type, scanner_version, scan_date,
             imported_by, host_count, finding_count,
             critical_count, high_count, medium_count, low_count, info_count,
             status, evidence_artifact_id, summary_text)
        VALUES
            (:id, :org_id, :filename, 'NESSUS', :version, :scan_date,
             :imported_by, :host_count, :finding_count,
             :c, :h, :m, :l, :i,
             'COMPLETE', :evidence_id, :summary)
    """), {
        "id": scan_id,
        "org_id": org_id,
        "filename": file.filename,
        "version": result.scanner_version,
        "scan_date": result.scan_date,
        "imported_by": user_id,
        "host_count": len(result.hosts),
        "finding_count": len(result.findings),
        "c": result.critical_count,
        "h": result.high_count,
        "m": result.medium_count,
        "l": result.low_count,
        "i": result.info_count,
        "evidence_id": evidence_id,
        "summary": summary[:5000],
    })

    # ── scan_findings batch insert ───────────────────────────────────────
    for finding in result.findings:
        fid = _gen_id(
            f"finding:{scan_id}:{finding.host_ip}:{finding.plugin_id}:{finding.port}"
        )
        db.execute(text("""
            INSERT INTO scan_findings
                (id, scan_import_id, org_id, host_ip, hostname, port, protocol,
                 plugin_id, plugin_name, plugin_family, severity, severity_label,
                 cvss_base_score, cvss3_base_score, cve_ids, synopsis, description,
                 solution, risk_factor, mapped_control_ids, status)
            VALUES
                (:id, :scan_id, :org_id, :host_ip, :hostname, :port, :protocol,
                 :plugin_id, :plugin_name, :plugin_family, :severity, :severity_label,
                 :cvss_base, :cvss3_base, CAST(:cves AS json), :synopsis, :description,
                 :solution, :risk_factor, CAST(:controls AS json), 'OPEN')
        """), {
            "id": fid,
            "scan_id": scan_id,
            "org_id": org_id,
            "host_ip": finding.host_ip,
            "hostname": finding.hostname,
            "port": finding.port,
            "protocol": finding.protocol,
            "plugin_id": finding.plugin_id,
            "plugin_name": finding.plugin_name[:500],
            "plugin_family": finding.plugin_family,
            "severity": finding.severity,
            "severity_label": finding.severity_label,
            "cvss_base": finding.cvss_base_score,
            "cvss3_base": finding.cvss3_base_score,
            "cves": json.dumps(finding.cve_ids),
            "synopsis": finding.synopsis[:2000] if finding.synopsis else None,
            "description": finding.description[:5000] if finding.description else None,
            "solution": finding.solution[:2000] if finding.solution else None,
            "risk_factor": finding.risk_factor,
            "controls": json.dumps(finding.mapped_control_ids),
        })

    db.commit()

    # Audit — canonical hash chain. Separate commit since the helper
    # updates audit_log with its own INSERT.
    _audit(db, actor=user_id, action="SCAN_IMPORTED", target_id=scan_id, details={
        "filename": file.filename,
        "org_id": org_id,
        "host_count": len(result.hosts),
        "finding_count": len(result.findings),
        "critical": result.critical_count,
        "high": result.high_count,
        "evidence_artifact_id": evidence_id,
    })
    db.commit()

    return {
        "scan_id": scan_id,
        "filename": file.filename,
        "status": "COMPLETE",
        "host_count": len(result.hosts),
        "finding_count": len(result.findings),
        "critical_count": result.critical_count,
        "high_count": result.high_count,
        "medium_count": result.medium_count,
        "low_count": result.low_count,
        "info_count": result.info_count,
        "evidence_artifact_id": evidence_id,
        "controls_mapped": len(mapped_controls),
    }


# ---------------------------------------------------------------------------
# GET /api/scans/  +  /api/scans/summary  +  /api/scans/{id}
# ---------------------------------------------------------------------------

@router.get("/")
async def list_scans(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    rows = db.execute(text("""
        SELECT id, filename, scan_type, scan_date, imported_at,
               host_count, finding_count, critical_count, high_count,
               medium_count, low_count, info_count, status,
               evidence_artifact_id, error_message
        FROM scan_imports
        WHERE org_id = :org_id
        ORDER BY imported_at DESC
    """), {"org_id": org_id}).fetchall()
    return [dict(row._mapping) for row in rows]


@router.get("/summary")
async def scan_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Org-wide vulnerability rollup for the Overview dashboard."""
    org_id = current_user["org_id"]

    severity_rows = db.execute(text("""
        SELECT severity_label, COUNT(*) AS count
        FROM scan_findings
        WHERE org_id = :org_id AND status = 'OPEN'
        GROUP BY severity_label
    """), {"org_id": org_id}).fetchall()
    severity_breakdown = {r[0]: int(r[1]) for r in severity_rows}

    scan_stats = db.execute(text("""
        SELECT COUNT(*)             AS total_scans,
               MAX(scan_date)       AS latest_scan_date,
               COALESCE(SUM(host_count), 0) AS total_hosts_scanned
        FROM scan_imports
        WHERE org_id = :org_id AND status = 'COMPLETE'
    """), {"org_id": org_id}).fetchone()

    control_rows = db.execute(text("""
        SELECT elem::text AS control_id, COUNT(*) AS finding_count
        FROM scan_findings,
             json_array_elements_text(mapped_control_ids) AS elem
        WHERE org_id = :org_id AND status = 'OPEN'
        GROUP BY elem
        ORDER BY finding_count DESC
        LIMIT 10
    """), {"org_id": org_id}).fetchall()
    top_affected_controls = [
        {"control_id": r[0], "finding_count": int(r[1])} for r in control_rows
    ]

    at_risk = db.execute(text("""
        SELECT COUNT(DISTINCT host_ip) AS hosts_at_risk
        FROM scan_findings
        WHERE org_id = :org_id AND status = 'OPEN' AND severity >= 3
    """), {"org_id": org_id}).fetchone()

    return {
        "total_open_findings": sum(severity_breakdown.values()),
        "severity_breakdown": severity_breakdown,
        "total_scans": int(scan_stats[0]) if scan_stats else 0,
        "latest_scan_date": scan_stats[1].isoformat() if scan_stats and scan_stats[1] else None,
        "total_hosts_scanned": int(scan_stats[2]) if scan_stats else 0,
        "hosts_at_risk": int(at_risk[0]) if at_risk else 0,
        "top_affected_controls": top_affected_controls,
    }


@router.get("/{scan_id}")
async def get_scan(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    row = db.execute(text("""
        SELECT * FROM scan_imports
        WHERE id = :id AND org_id = :org_id
    """), {"id": scan_id, "org_id": org_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Scan not found")
    return dict(row._mapping)


@router.get("/{scan_id}/findings")
async def get_scan_findings(
    scan_id: str,
    severity: Optional[str] = Query(None, description="CRITICAL / HIGH / MEDIUM / LOW"),
    status_filter: Optional[str] = Query(None, alias="status",
                                         description="OPEN / MITIGATED / ACCEPTED / FALSE_POSITIVE"),
    control_id: Optional[str] = Query(None, description="Filter by mapped NIST control"),
    host: Optional[str] = Query(None, description="Filter by host IP"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    conditions = ["scan_import_id = :scan_id", "org_id = :org_id"]
    params: dict = {"scan_id": scan_id, "org_id": org_id, "limit": limit, "offset": offset}

    if severity:
        conditions.append("severity_label = :severity")
        params["severity"] = severity.upper()
    if status_filter:
        conditions.append("status = :status_val")
        params["status_val"] = status_filter.upper()
    if host:
        conditions.append("host_ip = :host")
        params["host"] = host
    if control_id:
        conditions.append("mapped_control_ids::text LIKE :control_pattern")
        params["control_pattern"] = f'%"{control_id}"%'

    where = " AND ".join(conditions)

    rows = db.execute(text(f"""
        SELECT id, host_ip, hostname, port, protocol, plugin_id, plugin_name,
               plugin_family, severity, severity_label, cvss_base_score,
               cvss3_base_score, cve_ids, synopsis, solution, risk_factor,
               mapped_control_ids, status, notes, created_at
        FROM scan_findings
        WHERE {where}
        ORDER BY severity DESC, cvss3_base_score DESC NULLS LAST
        LIMIT :limit OFFSET :offset
    """), params).fetchall()

    total = db.execute(
        text(f"SELECT COUNT(*) FROM scan_findings WHERE {where}"), params
    ).scalar() or 0

    return {
        "findings": [dict(row._mapping) for row in rows],
        "total": int(total),
        "limit": limit,
        "offset": offset,
    }


# ---------------------------------------------------------------------------
# PATCH /api/scans/findings/{id}/status
# ---------------------------------------------------------------------------

VALID_FINDING_STATUSES = {"OPEN", "MITIGATED", "ACCEPTED", "FALSE_POSITIVE"}


@router.patch("/findings/{finding_id}/status")
async def update_finding_status(
    finding_id: str,
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    new_status = str(body.get("status", "")).upper()
    notes = body.get("notes")

    if new_status not in VALID_FINDING_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Status must be one of: {sorted(VALID_FINDING_STATUSES)}",
        )

    result = db.execute(text("""
        UPDATE scan_findings
        SET status = :status, notes = COALESCE(:notes, notes)
        WHERE id = :id AND org_id = :org_id
        RETURNING id
    """), {"id": finding_id, "org_id": org_id, "status": new_status, "notes": notes})

    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Finding not found")
    db.commit()
    return {"id": finding_id, "status": new_status}


# ---------------------------------------------------------------------------
# POST /api/scans/{scan_id}/generate-poam  (3.1C)
# ---------------------------------------------------------------------------

POAM_INELIGIBLE_CONTROLS = {"CA.L2-3.12.4"}  # SSP control — CMMC hard rule


def _severity_to_risk(sev: int) -> str:
    # Align with existing risk_level values already on assessment-driven items.
    if sev >= 4: return "CRITICAL"
    if sev >= 3: return "HIGH"
    if sev >= 2: return "MEDIUM"
    return "LOW"


def _build_weakness_text(control_id: str, findings: list) -> str:
    """Human-readable weakness summary, capped at 2000 chars."""
    lines = [f"Vulnerability scan identified {len(findings)} finding(s) affecting {control_id}:"]
    # Top 5 by severity, then by plugin_id for determinism.
    ordered = sorted(findings, key=lambda f: (-int(f[5]), f[7]))[:5]
    for f in ordered:
        # Row layout below: (id, scan_id, host_ip, plugin_id, plugin_name, severity, severity_label, solution, cve_ids)
        sev_label = f[6]
        plugin_name = (f[4] or "").strip()
        host_ip = f[2] or "?"
        cves = f[8] if isinstance(f[8], list) else []
        cve_str = f" ({', '.join(cves[:2])})" if cves else ""
        lines.append(f"- [{sev_label}] {plugin_name} on {host_ip}{cve_str}")
    if len(findings) > 5:
        lines.append(f"(+ {len(findings) - 5} additional finding(s) suppressed)")
    return "\n".join(lines)[:2000]


def _build_remediation_text(findings: list) -> str:
    """Dedup solutions across findings, cap at 2000 chars."""
    seen: set = set()
    ordered_unique: list[str] = []
    for f in findings:
        sol = (f[7] or "").strip()
        if not sol:
            continue
        key = sol.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered_unique.append(sol)
    if not ordered_unique:
        return "Review finding details and apply vendor guidance."
    numbered = [f"{i+1}. {s}" for i, s in enumerate(ordered_unique[:5])]
    body = "Recommended remediation actions:\n" + "\n".join(numbered)
    return body[:2000]


@router.post("/{scan_id}/generate-poam")
async def generate_poam_from_scan(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create POA&M items for each NIST control covered by OPEN Critical/High
    findings in this scan. Skips CA.L2-3.12.4 (CMMC hard rule) and dedupes
    against existing items for the same control.
    """
    org_id = current_user["org_id"]
    user_id = current_user["id"]

    # Verify the scan belongs to this org.
    owner = db.execute(text("""
        SELECT id FROM scan_imports WHERE id = :sid AND org_id = :oid
    """), {"sid": scan_id, "oid": org_id}).fetchone()
    if not owner:
        raise HTTPException(status_code=404, detail="Scan not found")

    # Pull all OPEN severity >= 3 findings with the columns weakness + remediation need.
    finding_rows = db.execute(text("""
        SELECT id, scan_import_id, host_ip, plugin_id, plugin_name,
               severity, severity_label, solution, cve_ids, mapped_control_ids
        FROM scan_findings
        WHERE scan_import_id = :sid AND org_id = :oid
          AND status = 'OPEN' AND severity >= 3
        ORDER BY severity DESC
    """), {"sid": scan_id, "oid": org_id}).fetchall()

    # Group findings by the controls they map to.
    by_control: dict[str, list] = {}
    import json as _json
    for r in finding_rows:
        ctrls = r[9]
        if isinstance(ctrls, str):
            try:
                ctrls = _json.loads(ctrls)
            except Exception:
                ctrls = []
        if not isinstance(ctrls, list):
            ctrls = []
        for cid in ctrls:
            by_control.setdefault(cid, []).append(r)

    now = datetime.now(timezone.utc)
    from datetime import timedelta as _td
    deadline = now + _td(days=180)

    created: list[str] = []
    skipped_existing = 0
    skipped_ca = 0
    skipped_covered_elsewhere = 0
    total_findings = sum(len(v) for v in by_control.values())

    for control_id, findings in by_control.items():
        if control_id in POAM_INELIGIBLE_CONTROLS:
            skipped_ca += 1
            logger.info("POA&M skip: %s is POA&M-ineligible under CMMC", control_id)
            continue

        # Dedup #1: same scan already produced a POA&M item for this control.
        already_same = db.execute(text("""
            SELECT 1 FROM poam_items
            WHERE org_id = :oid AND control_id = :cid
              AND source_type = 'SCAN' AND source_id = :sid
            LIMIT 1
        """), {"oid": org_id, "cid": control_id, "sid": scan_id}).fetchone()
        if already_same:
            skipped_existing += 1
            continue

        # Dedup #2: any OPEN POA&M item from any source already tracks this
        # control — the user can close that one, re-generate, and we'll fill
        # in gaps next time.
        already_open_any = db.execute(text("""
            SELECT 1 FROM poam_items
            WHERE org_id = :oid AND control_id = :cid AND status = 'OPEN'
            LIMIT 1
        """), {"oid": org_id, "cid": control_id}).fetchone()
        if already_open_any:
            skipped_covered_elsewhere += 1
            continue

        poam_id = hashlib.sha256(
            f"poam:scan:{scan_id}:{control_id}".encode()
        ).hexdigest()[:20]

        worst_sev = max(int(f[5]) for f in findings)
        risk = _severity_to_risk(worst_sev)

        db.execute(text("""
            INSERT INTO poam_items
                (id, org_id, control_id, weakness_description, remediation_plan,
                 status, risk_level, scheduled_completion,
                 source_type, source_id, created_at)
            VALUES
                (:id, :oid, :cid, :weak, :rem,
                 'OPEN', :risk, :deadline,
                 'SCAN', :source_id, :now)
        """), {
            "id":        poam_id,
            "oid":       org_id,
            "cid":       control_id,
            "weak":      _build_weakness_text(control_id, findings),
            "rem":       _build_remediation_text(findings),
            "risk":      risk,
            "deadline":  deadline,
            "source_id": scan_id,
            "now":       now,
        })
        created.append(control_id)

    db.commit()

    # Audit via the canonical helper (keeps the global hash chain intact).
    _audit(
        db,
        actor=user_id,
        action="POAM_GENERATED_FROM_SCAN",
        target_id=scan_id,
        details={
            "scan_id": scan_id,
            "poam_items_created": len(created),
            "controls_covered": created,
            "skipped_existing_same_scan": skipped_existing,
            "skipped_covered_elsewhere": skipped_covered_elsewhere,
            "skipped_ca_3_12_4": skipped_ca,
            "total_findings_processed": total_findings,
        },
    )
    db.commit()

    return {
        "scan_id": scan_id,
        "poam_items_created": len(created),
        "controls_covered": created,
        "skipped_existing": skipped_existing + skipped_covered_elsewhere,
        "skipped_ca_3_12_4": skipped_ca,
        "total_findings_processed": total_findings,
    }


# ---------------------------------------------------------------------------
# DELETE /api/scans/{id}
# ---------------------------------------------------------------------------

@router.delete("/{scan_id}")
async def delete_scan(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]

    row = db.execute(text("""
        SELECT id, evidence_artifact_id FROM scan_imports
        WHERE id = :id AND org_id = :org_id
    """), {"id": scan_id, "org_id": org_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Scan not found")

    evidence_id = row[1]

    # Findings CASCADE when scan_imports is deleted, but be explicit so a
    # FK repoint later doesn't silently leak rows.
    db.execute(text("DELETE FROM scan_findings WHERE scan_import_id = :id"),
               {"id": scan_id})
    db.execute(text("DELETE FROM scan_imports   WHERE id = :id"),
               {"id": scan_id})

    if evidence_id:
        db.execute(text("DELETE FROM evidence_control_map WHERE evidence_id = :eid"),
                   {"eid": evidence_id})
        db.execute(
            text("DELETE FROM evidence_artifacts WHERE id = :eid AND org_id = :org_id"),
            {"eid": evidence_id, "org_id": org_id},
        )

    db.commit()
    _audit(db, actor=current_user["id"], action="SCAN_DELETED",
           target_id=scan_id, details={"evidence_artifact_id": evidence_id})
    db.commit()

    return {"deleted": scan_id}
