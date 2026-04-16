"""
src/api/routes_resolutions.py

REST API for the resolution engine (Phase 4.3). All write endpoints
are admin-only because each resolve pass issues LLM calls.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.auth import get_current_user, ADMIN_ROLES
from src.db.session import get_db
from src.truth.resolver import (
    get_resolution_summary,
    resolve_all,
    resolve_control,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/resolutions", tags=["resolutions"])


def _require_admin(user: dict) -> None:
    if user.get("role") not in ADMIN_ROLES:
        raise HTTPException(403, "Admin required")


# ───────────────────────────────────────────────────────────────────────────
# Write endpoints (admin-only)
# ───────────────────────────────────────────────────────────────────────────

@router.post("/resolve-all")
def resolve_all_controls(
    body: Optional[dict] = Body(default=None),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Resolve every control (or a subset via body.control_ids) for the caller's org."""
    _require_admin(user)

    control_ids = None
    if body and isinstance(body.get("control_ids"), list):
        control_ids = [str(c) for c in body["control_ids"] if c]

    summary = resolve_all(
        org_id=user["org_id"], db=db, user_id=user["id"], control_ids=control_ids,
    )
    if summary["controls_processed"] > 50:
        summary["warning"] = (
            f"Processed {summary['controls_processed']} controls — each control "
            "runs claims × observations LLM calls."
        )
    return summary


@router.post("/resolve/{control_id}")
def resolve_single(
    control_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Resolve one control's claims against its observations."""
    _require_admin(user)
    return resolve_control(
        control_id=control_id, org_id=user["org_id"], db=db, user_id=user["id"],
    )


# ───────────────────────────────────────────────────────────────────────────
# Read endpoints
# ───────────────────────────────────────────────────────────────────────────

@router.get("/summary")
def resolution_summary(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Truth-model dashboard roll-up."""
    return get_resolution_summary(user["org_id"], db)


@router.get("/conflicts")
def resolution_conflicts(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """All CONFLICT claims with the CONTRADICTS resolutions that caused them."""
    rows = db.execute(text("""
        SELECT c.id            AS claim_id,
               c.control_id,
               c.claim_text,
               c.claim_type,
               r.id             AS resolution_id,
               r.observation_id,
               r.confidence,
               r.reasoning,
               o.observation_text,
               o.source_type
        FROM claims c
        JOIN resolutions  r ON r.claim_id       = c.id
        JOIN observations o ON o.id             = r.observation_id
        WHERE c.org_id = :o
          AND c.verification_status = 'CONFLICT'
          AND r.relationship = 'CONTRADICTS'
        ORDER BY r.confidence DESC, c.control_id ASC
    """), {"o": user["org_id"]}).fetchall()

    grouped: dict[str, dict] = {}
    for r in rows:
        entry = grouped.setdefault(r.claim_id, {
            "claim_id":    r.claim_id,
            "control_id":  r.control_id,
            "claim_text":  r.claim_text,
            "claim_type":  r.claim_type,
            "contradictions": [],
        })
        entry["contradictions"].append({
            "resolution_id":     r.resolution_id,
            "observation_id":    r.observation_id,
            "observation_text":  r.observation_text,
            "source_type":       r.source_type,
            "confidence":        r.confidence,
            "reasoning":         r.reasoning,
        })

    return {"items": list(grouped.values()), "count": len(grouped)}


@router.get("/by-control/{control_id}")
def resolutions_by_control(
    control_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Per-claim view for one control: each claim with its resolutions nested."""
    claims = db.execute(text("""
        SELECT id, claim_text, claim_type, verification_status,
               source_span_start, source_span_end, confidence
        FROM claims
        WHERE org_id = :o AND control_id = :c
        ORDER BY COALESCE(source_span_start, 0) ASC, id ASC
    """), {"o": user["org_id"], "c": control_id}).fetchall()

    if not claims:
        return {"control_id": control_id, "claims": []}

    claim_ids = [c.id for c in claims]
    res_rows = db.execute(text("""
        SELECT r.claim_id,
               r.id          AS resolution_id,
               r.relationship,
               r.confidence  AS resolution_confidence,
               r.reasoning,
               r.resolved_at,
               r.model_used,
               o.id            AS observation_id,
               o.observation_text,
               o.source_type,
               o.source_id
        FROM resolutions r
        JOIN observations o ON o.id = r.observation_id
        WHERE r.org_id = :o AND r.claim_id = ANY(:ids)
        ORDER BY r.confidence DESC, r.resolved_at DESC
    """), {"o": user["org_id"], "ids": claim_ids}).fetchall()

    by_claim: dict[str, list[dict]] = {cid: [] for cid in claim_ids}
    for r in res_rows:
        by_claim[r.claim_id].append({
            "resolution_id":    r.resolution_id,
            "observation_id":   r.observation_id,
            "observation_text": r.observation_text,
            "source_type":      r.source_type,
            "source_id":        r.source_id,
            "relationship":     r.relationship,
            "confidence":       r.resolution_confidence,
            "reasoning":        r.reasoning,
            "resolved_at":      r.resolved_at.isoformat() if r.resolved_at else None,
            "model_used":       r.model_used,
        })

    return {
        "control_id": control_id,
        "claims": [
            {
                "claim_id":            c.id,
                "claim_text":          c.claim_text,
                "claim_type":          c.claim_type,
                "verification_status": c.verification_status,
                "source_span_start":   c.source_span_start,
                "source_span_end":     c.source_span_end,
                "extraction_confidence": c.confidence,
                "resolutions":         by_claim.get(c.id, []),
            }
            for c in claims
        ],
    }


@router.get("")
def list_resolutions(
    claim_id:       Optional[str] = Query(None),
    observation_id: Optional[str] = Query(None),
    relationship:   Optional[str] = Query(None),
    control_id:     Optional[str] = Query(None),
    page:     int = Query(1,  ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db:   Session = Depends(get_db),
    user: dict    = Depends(get_current_user),
):
    """Paginated, filterable list joined with claim + observation text."""
    where = ["r.org_id = :o"]
    params: dict = {
        "o":      user["org_id"],
        "limit":  per_page,
        "offset": (page - 1) * per_page,
    }
    if claim_id:
        where.append("r.claim_id = :claim_id")
        params["claim_id"] = claim_id
    if observation_id:
        where.append("r.observation_id = :obs_id")
        params["obs_id"] = observation_id
    if relationship:
        where.append("r.relationship = :rel")
        params["rel"] = relationship.upper()
    if control_id:
        where.append("c.control_id = :cid")
        params["cid"] = control_id
    where_sql = " AND ".join(where)

    rows = db.execute(text(f"""
        SELECT r.id, r.org_id, r.claim_id, r.observation_id,
               r.relationship, r.confidence, r.reasoning,
               r.resolved_at, r.resolved_by, r.model_used,
               c.control_id, c.claim_text, c.claim_type, c.verification_status,
               o.observation_text, o.source_type, o.observation_type
        FROM resolutions r
        JOIN claims       c ON c.id = r.claim_id
        JOIN observations o ON o.id = r.observation_id
        WHERE {where_sql}
        ORDER BY r.confidence DESC, r.resolved_at DESC
        LIMIT :limit OFFSET :offset
    """), params).fetchall()

    total = db.execute(text(f"""
        SELECT COUNT(*)
        FROM resolutions r
        JOIN claims       c ON c.id = r.claim_id
        JOIN observations o ON o.id = r.observation_id
        WHERE {where_sql}
    """), params).scalar() or 0

    return {
        "items":    [dict(r._mapping) for r in rows],
        "total":    int(total),
        "page":     page,
        "per_page": per_page,
    }
