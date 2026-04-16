"""
src/api/routes_assessments.py

Assessment simulation API (Phase 4.5). ``/simulate`` makes LLM calls
(assessor findings); ``/at-risk`` and ``/method-coverage`` are
LLM-free for fast widget use.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.auth import get_current_user, ADMIN_ROLES
from src.db.session import get_db
from src.truth.assessment_sim import (
    compute_method_coverage,
    identify_likely_failures,
    run_simulation,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/assessments", tags=["assessments"])


def _require_admin(user: dict) -> None:
    if user.get("role") not in ADMIN_ROLES:
        raise HTTPException(403, "Admin required")


# ── Write endpoints ───────────────────────────────────────────────────────

@router.post("/simulate")
def simulate(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Full simulation run — stores snapshot, returns scorecard."""
    _require_admin(user)

    total_claims = db.execute(
        text("SELECT COUNT(*) FROM claims WHERE org_id = :o"),
        {"o": user["org_id"]},
    ).scalar() or 0
    result = run_simulation(user["org_id"], db, user["id"])
    if total_claims == 0:
        result["warning"] = (
            "No claims extracted yet — extract claims first for meaningful results."
        )
    return result


# ── Read endpoints (static paths first) ───────────────────────────────────

@router.get("/latest")
def latest_snapshot(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Most recent simulation snapshot for the org."""
    row = db.execute(text("""
        SELECT * FROM assessment_snapshots
        WHERE org_id = :o
        ORDER BY created_at DESC
        LIMIT 1
    """), {"o": user["org_id"]}).fetchone()
    if not row:
        return None
    return dict(row._mapping)


@router.get("/history")
def snapshot_history(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Snapshot list for trend visualization."""
    rows = db.execute(text("""
        SELECT id, created_at, readiness_pct, sprs_actual,
               sprs_truth_adjusted, sprs_delta,
               total_claims, controls_at_risk
        FROM assessment_snapshots
        WHERE org_id = :o
        ORDER BY created_at DESC
    """), {"o": user["org_id"]}).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/method-coverage")
def method_coverage_all(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Live method coverage per control that has claims."""
    controls = db.execute(text("""
        SELECT DISTINCT control_id FROM claims WHERE org_id = :o
        ORDER BY control_id
    """), {"o": user["org_id"]}).fetchall()

    items = []
    for r in controls:
        mc = compute_method_coverage(r.control_id, user["org_id"], db)
        items.append(mc)

    total = len(items)
    avg_pct = (sum(i["coverage_pct"] for i in items) / total) if total else 0.0
    return {"items": items, "total": total, "avg_coverage_pct": round(avg_pct, 1)}


@router.get("/at-risk")
def at_risk_controls(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Top-10 at-risk controls — no LLM calls, no snapshot."""
    return identify_likely_failures(user["org_id"], db, top_n=10)


# ── Dynamic path last ─────────────────────────────────────────────────────

@router.get("/{snapshot_id}")
def get_snapshot(
    snapshot_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Retrieve a specific historical snapshot."""
    row = db.execute(text("""
        SELECT * FROM assessment_snapshots
        WHERE id = :id AND org_id = :o
    """), {"id": snapshot_id, "o": user["org_id"]}).fetchone()
    if not row:
        raise HTTPException(404, "Snapshot not found")
    return dict(row._mapping)
