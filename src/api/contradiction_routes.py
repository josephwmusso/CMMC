"""
src/api/contradiction_routes.py

Phase 2.9A — HTTP surface for the contradiction engine.

  POST /api/contradictions/detect            (any authed user, org-scoped)
  GET  /api/contradictions                   (any authed user)
  PUT  /api/contradictions/{id}/resolve      (admin / superadmin)
  GET  /api/contradictions/summary           (any authed user)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.auth import get_current_user, require_admin_dep
from src.api.contradiction_engine import run_and_sync
from src.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/contradictions", tags=["contradictions"])


# ---------------------------------------------------------------------------
# Response models (kept permissive — raw SQL result shapes flow through)
# ---------------------------------------------------------------------------

class DetectResponse(BaseModel):
    detected: int
    resolved: int
    total_open: int


class ResolveRequest(BaseModel):
    status: str  # RESOLVED / DISMISSED / OVERRIDDEN
    resolution_notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Severity ordering — used by GET / sorting
# ---------------------------------------------------------------------------
SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
VALID_STATUSES = {"OPEN", "RESOLVED", "DISMISSED", "OVERRIDDEN"}


def _row_to_dict(row) -> dict:
    return {
        "id": row[0],
        "org_id": row[1],
        "session_id": row[2],
        "rule_id": row[3],
        "family": row[4],
        "severity": row[5],
        "status": row[6],
        "description": row[7],
        "source_question_id": row[8],
        "source_answer": row[9],
        "conflicting_question_id": row[10],
        "conflicting_answer": row[11],
        "affected_control_ids": row[12],
        "resolution_notes": row[13],
        "resolved_by": row[14],
        "resolved_at": row[15].isoformat() if row[15] else None,
        "detected_at": row[16].isoformat() if row[16] else None,
        "updated_at": row[17].isoformat() if row[17] else None,
    }


SELECT_COLUMNS = """
    id, org_id, session_id, rule_id, family, severity, status,
    description, source_question_id, source_answer,
    conflicting_question_id, conflicting_answer,
    affected_control_ids, resolution_notes, resolved_by,
    resolved_at, detected_at, updated_at
"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/detect", response_model=DetectResponse)
def detect(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run all 14 contradiction rules against the caller's org."""
    org_id = current_user["org_id"]
    try:
        counters = run_and_sync(db, org_id)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("Contradiction detect failed for %s: %s", org_id, exc)
        raise HTTPException(500, f"Contradiction scan failed: {exc}")

    # Audit entry — best-effort, never fail the scan because of audit.
    try:
        from src.evidence.state_machine import create_audit_entry
        create_audit_entry(
            db=db,
            actor=current_user.get("id", "unknown"),
            actor_type="user",
            action="CONTRADICTION_SCAN",
            target_type="ORGANIZATION",
            target_id=org_id,
            details={
                "detected": counters["detected"],
                "resolved": counters["resolved"],
                "total_open": counters["total_open"],
            },
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Audit entry for CONTRADICTION_SCAN failed")

    return DetectResponse(**counters)


@router.get("", response_model=list[dict])
def list_contradictions(
    status_filter: Optional[str] = Query(None, alias="status"),
    family: Optional[str] = None,
    severity: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List contradictions for the caller's org. Supports filters on status,
    family, and severity. Ordered by severity (CRITICAL first) then family."""
    org_id = current_user["org_id"]
    where = ["org_id = :oid"]
    params: dict = {"oid": org_id}
    if status_filter:
        where.append("status = :status_val")
        params["status_val"] = status_filter.upper()
    if family:
        where.append("family = :family")
        params["family"] = family.upper()
    if severity:
        where.append("severity = :severity")
        params["severity"] = severity.upper()

    rows = db.execute(
        text(f"""
            SELECT {SELECT_COLUMNS}
            FROM intake_contradictions
            WHERE {' AND '.join(where)}
        """),
        params,
    ).fetchall()

    dicts = [_row_to_dict(r) for r in rows]
    # Sort by severity, then family, then newest.
    dicts.sort(key=lambda d: (
        SEVERITY_ORDER.get(d["severity"], 99),
        d["family"],
        -(int(datetime.fromisoformat(d["updated_at"]).timestamp()) if d["updated_at"] else 0),
    ))
    return dicts


@router.put("/{contradiction_id}/resolve", response_model=dict)
def resolve_contradiction(
    contradiction_id: str,
    req: ResolveRequest,
    current_user: dict = Depends(require_admin_dep),
    db: Session = Depends(get_db),
):
    """ADMIN+ only. Flip status to RESOLVED / DISMISSED / OVERRIDDEN."""
    status = (req.status or "").upper()
    if status not in {"RESOLVED", "DISMISSED", "OVERRIDDEN"}:
        raise HTTPException(400, f"Invalid status: {req.status}")

    org_id = current_user["org_id"]
    now = datetime.now(timezone.utc).isoformat()

    existing = db.execute(text("""
        SELECT id, org_id FROM intake_contradictions WHERE id = :id
    """), {"id": contradiction_id}).fetchone()
    if not existing:
        raise HTTPException(404, "Contradiction not found")
    if existing[1] != org_id and current_user.get("role") != "SUPERADMIN":
        raise HTTPException(404, "Contradiction not found")

    db.execute(text("""
        UPDATE intake_contradictions
        SET status           = :status,
            resolution_notes = :notes,
            resolved_by      = :by,
            resolved_at      = :now,
            updated_at       = :now
        WHERE id = :id
    """), {
        "status": status,
        "notes": req.resolution_notes,
        "by": current_user["id"],
        "now": now,
        "id": contradiction_id,
    })
    db.commit()

    try:
        from src.evidence.state_machine import create_audit_entry
        create_audit_entry(
            db=db,
            actor=current_user["id"],
            actor_type="user",
            action="CONTRADICTION_RESOLVED",
            target_type="CONTRADICTION",
            target_id=contradiction_id,
            details={
                "new_status": status,
                "notes": req.resolution_notes or "",
            },
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Audit entry for CONTRADICTION_RESOLVED failed")

    row = db.execute(
        text(f"SELECT {SELECT_COLUMNS} FROM intake_contradictions WHERE id = :id"),
        {"id": contradiction_id},
    ).fetchone()
    return _row_to_dict(row)


@router.get("/summary", response_model=dict)
def summary(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = current_user["org_id"]
    rows = db.execute(text("""
        SELECT status, severity, family, COUNT(*)
        FROM intake_contradictions
        WHERE org_id = :oid
        GROUP BY status, severity, family
    """), {"oid": org_id}).fetchall()

    out = {
        "total": 0,
        "by_status": {"OPEN": 0, "RESOLVED": 0, "DISMISSED": 0, "OVERRIDDEN": 0},
        "by_severity": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
        "by_family": {},
    }
    for status_val, sev, fam, n in rows:
        n = int(n or 0)
        out["total"] += n
        out["by_status"][status_val] = out["by_status"].get(status_val, 0) + n
        out["by_severity"][sev] = out["by_severity"].get(sev, 0) + n
        out["by_family"][fam] = out["by_family"].get(fam, 0) + n

    # 2.9B — assessment readiness gate.
    # Any OPEN CRITICAL → not assessment-ready (hard block).
    # OPEN HIGH → ready with warnings.
    # MEDIUM / LOW OPEN or anything not OPEN → informational.
    blocker_rows = db.execute(text("""
        SELECT id, rule_id, family, description
        FROM intake_contradictions
        WHERE org_id = :oid AND status = 'OPEN' AND severity = 'CRITICAL'
        ORDER BY family, rule_id
    """), {"oid": org_id}).fetchall()
    warning_rows = db.execute(text("""
        SELECT id, rule_id, family, description
        FROM intake_contradictions
        WHERE org_id = :oid AND status = 'OPEN' AND severity = 'HIGH'
        ORDER BY family, rule_id
    """), {"oid": org_id}).fetchall()

    def _short(row) -> dict:
        return {
            "id": row[0],
            "rule_id": row[1],
            "family": row[2],
            "description": row[3],
        }

    out["assessment_impact"] = {
        "ready":    len(blocker_rows) == 0,
        "blockers": [_short(r) for r in blocker_rows],
        "warnings": [_short(r) for r in warning_rows],
    }
    return out
