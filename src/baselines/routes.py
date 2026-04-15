"""
src/baselines/routes.py

HTTP API for the baseline engine.

Route ordering note: static-path routes (``/summary``, ``/org/adopted``,
``/org/{ob_id}/deviations``, ``/match/{scan_id}``,
``/deviations/{dev_id}``) are declared BEFORE the catch-all
``/{baseline_id}`` routes so FastAPI matches them first.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.auth import get_current_user, ADMIN_ROLES
from src.baselines.matcher import (
    get_baseline_summary,
    match_scan_to_baselines,
)
from src.db.session import get_db
from src.evidence.state_machine import create_audit_entry

router = APIRouter(prefix="/api/baselines", tags=["baselines"])


def _generate_id(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()[:20]


def _require_admin(user: dict) -> None:
    if user.get("role") not in ADMIN_ROLES:
        raise HTTPException(403, "Admin required")


# ───────────────────────────────────────────────────────────────────────────
# Static-path routes — must come before /{baseline_id}
# ───────────────────────────────────────────────────────────────────────────

@router.get("/summary")
def baseline_summary(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Overview-page compliance summary for the caller's org."""
    return get_baseline_summary(db, user["org_id"])


@router.get("/org/adopted")
def list_org_baselines(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List the caller org's ACTIVE adoptions with deviation counts."""
    rows = db.execute(text("""
        SELECT ob.id          AS org_baseline_id,
               ob.adopted_at,
               ob.status,
               b.id            AS baseline_id,
               b.name,
               b.version,
               b.platform,
               b.source,
               b.item_count,
               COALESCE(open_ct.cnt,  0) AS open_deviations,
               COALESCE(total_ct.cnt, 0) AS total_deviations
        FROM org_baselines ob
        JOIN baselines b ON ob.baseline_id = b.id
        LEFT JOIN (
            SELECT org_baseline_id, COUNT(*) AS cnt
            FROM baseline_deviations WHERE status = 'OPEN'
            GROUP BY org_baseline_id
        ) open_ct ON open_ct.org_baseline_id = ob.id
        LEFT JOIN (
            SELECT org_baseline_id, COUNT(*) AS cnt
            FROM baseline_deviations
            GROUP BY org_baseline_id
        ) total_ct ON total_ct.org_baseline_id = ob.id
        WHERE ob.org_id = :org_id AND ob.status = 'ACTIVE'
        ORDER BY ob.adopted_at DESC
    """), {"org_id": user["org_id"]}).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/org/{org_baseline_id}/deviations")
def list_deviations(
    org_baseline_id: str,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Paginated list of deviations under one adoption, filterable by
    deviation status and item severity."""
    ob = db.execute(text("""
        SELECT id FROM org_baselines
        WHERE id = :id AND org_id = :org_id
    """), {"id": org_baseline_id, "org_id": user["org_id"]}).fetchone()
    if not ob:
        raise HTTPException(404, "Baseline adoption not found")

    where = ["bd.org_baseline_id = :ob_id"]
    params: dict = {
        "ob_id":  org_baseline_id,
        "limit":  page_size,
        "offset": max(0, (page - 1) * page_size),
    }
    if status:
        where.append("bd.status = :status")
        params["status"] = status.upper()
    if severity:
        where.append("bi.severity = :severity")
        params["severity"] = severity.upper()
    where_sql = " AND ".join(where)

    rows = db.execute(text(f"""
        SELECT bd.id,
               bd.status,
               bd.actual_value,
               bd.notes,
               bd.detected_at,
               bd.resolved_at,
               bi.cis_id,
               bi.title           AS item_title,
               bi.section,
               bi.expected_value,
               bi.severity        AS item_severity,
               bi.control_ids,
               sf.host_ip,
               sf.plugin_name     AS finding_name
        FROM baseline_deviations bd
        JOIN baseline_items bi ON bd.baseline_item_id = bi.id
        LEFT JOIN scan_findings sf ON bd.scan_finding_id = sf.id
        WHERE {where_sql}
        ORDER BY
            CASE bi.severity
                WHEN 'CRITICAL' THEN 0
                WHEN 'HIGH'     THEN 1
                WHEN 'MEDIUM'   THEN 2
                ELSE 3
            END,
            bd.detected_at DESC
        LIMIT :limit OFFSET :offset
    """), params).fetchall()

    total = db.execute(text(f"""
        SELECT COUNT(*)
        FROM baseline_deviations bd
        JOIN baseline_items bi ON bd.baseline_item_id = bi.id
        WHERE {where_sql}
    """), params).scalar() or 0

    return {
        "items":     [dict(r._mapping) for r in rows],
        "total":     total,
        "page":      page,
        "page_size": page_size,
    }


@router.post("/match/{scan_import_id}")
def run_baseline_match(
    scan_import_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Run the baseline matcher against one scan for the caller's org."""
    _require_admin(user)

    scan = db.execute(text("""
        SELECT id FROM scan_imports
        WHERE id = :id AND org_id = :org_id
    """), {"id": scan_import_id, "org_id": user["org_id"]}).fetchone()
    if not scan:
        raise HTTPException(404, "Scan not found")

    result = match_scan_to_baselines(db, user["org_id"], scan_import_id)

    create_audit_entry(
        db,
        actor=user["id"],
        actor_type="user",
        action="baseline.match_run",
        target_type="scan_import",
        target_id=scan_import_id,
        details={
            "org_id":              user["org_id"],
            "deviations_created":  result["deviations_created"],
            "deviations_skipped":  result["deviations_skipped"],
            "baselines_checked":   result["baselines_checked"],
        },
    )
    db.commit()

    return result


@router.patch("/deviations/{deviation_id}")
def update_deviation(
    deviation_id: str,
    body: dict,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Transition a deviation's status (REMEDIATED / ACCEPTED / FALSE_POSITIVE / OPEN)."""
    _require_admin(user)

    dev = db.execute(text("""
        SELECT id FROM baseline_deviations
        WHERE id = :id AND org_id = :org_id
    """), {"id": deviation_id, "org_id": user["org_id"]}).fetchone()
    if not dev:
        raise HTTPException(404, "Deviation not found")

    new_status = (body.get("status") or "").upper()
    valid = ("OPEN", "REMEDIATED", "ACCEPTED", "FALSE_POSITIVE")
    if new_status not in valid:
        raise HTTPException(400, f"Status must be one of: {valid}")

    notes = body.get("notes")
    now = datetime.now(timezone.utc)
    resolved_at = now if new_status != "OPEN" else None
    resolved_by = user["id"] if new_status != "OPEN" else None
    # resolved_by FKs into users; ALLOW_ANONYMOUS paths yield a fake id
    # that isn't a real row. Drop the reference rather than fail the patch.
    if resolved_by:
        exists = db.execute(
            text("SELECT 1 FROM users WHERE id = :id"),
            {"id": resolved_by},
        ).fetchone()
        if not exists:
            resolved_by = None

    db.execute(text("""
        UPDATE baseline_deviations
        SET status      = :status,
            notes       = :notes,
            resolved_at = :resolved_at,
            resolved_by = :resolved_by
        WHERE id = :id
    """), {
        "id":          deviation_id,
        "status":      new_status,
        "notes":       notes,
        "resolved_at": resolved_at,
        "resolved_by": resolved_by,
    })

    create_audit_entry(
        db,
        actor=user["id"],
        actor_type="user",
        action="baseline.deviation_updated",
        target_type="baseline_deviation",
        target_id=deviation_id,
        details={"org_id": user["org_id"], "status": new_status},
    )
    db.commit()

    return {"message": "Updated", "status": new_status}


# ───────────────────────────────────────────────────────────────────────────
# Catalog + adoption — /{baseline_id} comes last
# ───────────────────────────────────────────────────────────────────────────

@router.get("")
def list_baselines(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List all catalog baselines, annotated with whether the caller's
    org has adopted each (ACTIVE only)."""
    rows = db.execute(text("""
        SELECT b.*,
               EXISTS (
                   SELECT 1 FROM org_baselines ob
                   WHERE ob.baseline_id = b.id
                     AND ob.org_id      = :org_id
                     AND ob.status      = 'ACTIVE'
               ) AS adopted
        FROM baselines b
        ORDER BY b.platform, b.name
    """), {"org_id": user["org_id"]}).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/{baseline_id}")
def get_baseline(
    baseline_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Catalog baseline detail + all items."""
    baseline = db.execute(text(
        "SELECT * FROM baselines WHERE id = :id"
    ), {"id": baseline_id}).fetchone()
    if not baseline:
        raise HTTPException(404, "Baseline not found")

    items = db.execute(text("""
        SELECT * FROM baseline_items
        WHERE baseline_id = :id
        ORDER BY cis_id
    """), {"id": baseline_id}).fetchall()

    result = dict(baseline._mapping)
    result["items"] = [dict(r._mapping) for r in items]
    return result


@router.post("/{baseline_id}/adopt")
def adopt_baseline(
    baseline_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Adopt a baseline for the caller's org (or re-activate an archived one)."""
    _require_admin(user)

    baseline = db.execute(text(
        "SELECT id, name FROM baselines WHERE id = :id"
    ), {"id": baseline_id}).fetchone()
    if not baseline:
        raise HTTPException(404, "Baseline not found")

    existing = db.execute(text("""
        SELECT id, status FROM org_baselines
        WHERE org_id = :org_id AND baseline_id = :baseline_id
    """), {"org_id": user["org_id"], "baseline_id": baseline_id}).fetchone()

    now = datetime.now(timezone.utc)

    if existing:
        if existing.status == "ACTIVE":
            return {"message": "Already adopted", "org_baseline_id": existing.id}
        db.execute(text("""
            UPDATE org_baselines
            SET status = 'ACTIVE', adopted_at = :now
            WHERE id = :id
        """), {"id": existing.id, "now": now})
        create_audit_entry(
            db,
            actor=user["id"],
            actor_type="user",
            action="baseline.readopted",
            target_type="baseline",
            target_id=baseline_id,
            details={"org_id": user["org_id"], "name": baseline.name},
        )
        db.commit()
        return {"message": "Re-adopted", "org_baseline_id": existing.id}

    ob_id = _generate_id(f"ob:{user['org_id']}:{baseline_id}")
    db.execute(text("""
        INSERT INTO org_baselines (id, org_id, baseline_id, adopted_at, status)
        VALUES (:id, :org_id, :baseline_id, :now, 'ACTIVE')
    """), {
        "id":          ob_id,
        "org_id":      user["org_id"],
        "baseline_id": baseline_id,
        "now":         now,
    })

    create_audit_entry(
        db,
        actor=user["id"],
        actor_type="user",
        action="baseline.adopted",
        target_type="baseline",
        target_id=baseline_id,
        details={"org_id": user["org_id"], "name": baseline.name},
    )
    db.commit()

    return {"message": "Adopted", "org_baseline_id": ob_id}


@router.delete("/{baseline_id}/adopt")
def archive_baseline(
    baseline_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Archive (not delete) the caller org's adoption. Preserves deviation history."""
    _require_admin(user)

    row = db.execute(text("""
        UPDATE org_baselines
        SET status = 'ARCHIVED'
        WHERE org_id = :org_id
          AND baseline_id = :baseline_id
          AND status = 'ACTIVE'
        RETURNING id
    """), {"org_id": user["org_id"], "baseline_id": baseline_id}).fetchone()

    if not row:
        raise HTTPException(404, "Adoption not found")

    create_audit_entry(
        db,
        actor=user["id"],
        actor_type="user",
        action="baseline.archived",
        target_type="baseline",
        target_id=baseline_id,
        details={"org_id": user["org_id"]},
    )
    db.commit()
    return {"message": "Archived"}
