"""
src/api/routes_observations.py

REST API for observation rebuild + retrieval (Phase 4.2).

Static paths (``/build``, ``/build/{source_type}``, ``/summary``,
``/by-control/{control_id}``) are all distinct prefixes — no
``/{id}`` catch-all in this router, so ordering doesn't matter, but
we keep the builder routes first for readability.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.auth import get_current_user, ADMIN_ROLES
from src.db.session import get_db
from src.truth.observation_builder import (
    SOURCE_TYPES,
    build_all_observations,
    build_observations_for_source,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/observations", tags=["observations"])


def _require_admin(user: dict) -> None:
    if user.get("role") not in ADMIN_ROLES:
        raise HTTPException(403, "Admin required")


@router.post("/build")
def build_all(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Full rebuild — wipes and repopulates all observations for the caller's org."""
    _require_admin(user)
    return build_all_observations(org_id=user["org_id"], db=db, user_id=user["id"])


@router.post("/build/{source_type}")
def build_single(
    source_type: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Rebuild observations for one source_type only."""
    _require_admin(user)
    st = source_type.upper()
    if st not in SOURCE_TYPES:
        raise HTTPException(400, f"source_type must be one of {list(SOURCE_TYPES)}")
    return build_observations_for_source(
        org_id=user["org_id"], source_type=st, db=db, user_id=user["id"],
    )


@router.get("/summary")
def observations_summary(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Counts for the Overview widget."""
    org_id = user["org_id"]
    total = db.execute(
        text("SELECT COUNT(*) FROM observations WHERE org_id = :o"),
        {"o": org_id},
    ).scalar() or 0

    src_rows = db.execute(text("""
        SELECT source_type, COUNT(*) FROM observations
        WHERE org_id = :o GROUP BY source_type
    """), {"o": org_id}).fetchall()
    by_source = {r[0]: int(r[1]) for r in src_rows}

    type_rows = db.execute(text("""
        SELECT observation_type, COUNT(*) FROM observations
        WHERE org_id = :o GROUP BY observation_type
    """), {"o": org_id}).fetchall()
    by_type = {r[0]: int(r[1]) for r in type_rows}

    return {
        "total":              int(total),
        "by_source_type":     by_source,
        "by_observation_type": by_type,
    }


@router.get("/by-control/{control_id}")
def observations_by_control(
    control_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """All observations referencing this control, ordered highest
    confidence + most recent first. Used by the Resolution Engine."""
    rows = db.execute(text("""
        SELECT id, org_id, observation_text, source_type, source_id,
               control_ids, observation_type, confidence, observed_at,
               created_at, notes
        FROM observations
        WHERE org_id = :o AND :cid = ANY(control_ids)
        ORDER BY confidence DESC NULLS LAST,
                 observed_at DESC NULLS LAST,
                 created_at DESC
    """), {"o": user["org_id"], "cid": control_id}).fetchall()
    return {"items": [dict(r._mapping) for r in rows], "count": len(rows)}


@router.get("")
def list_observations(
    source_type:      Optional[str] = Query(None),
    observation_type: Optional[str] = Query(None),
    control_id:       Optional[str] = Query(None),
    page:     int = Query(1,  ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db:   Session = Depends(get_db),
    user: dict    = Depends(get_current_user),
):
    """Paginated, filterable list of observations for the caller's org."""
    where = ["org_id = :o"]
    params: dict = {
        "o":      user["org_id"],
        "limit":  per_page,
        "offset": (page - 1) * per_page,
    }
    if source_type:
        where.append("source_type = :st")
        params["st"] = source_type.upper()
    if observation_type:
        where.append("observation_type = :ot")
        params["ot"] = observation_type.upper()
    if control_id:
        where.append(":cid = ANY(control_ids)")
        params["cid"] = control_id
    where_sql = " AND ".join(where)

    rows = db.execute(text(f"""
        SELECT id, org_id, observation_text, source_type, source_id,
               control_ids, observation_type, confidence, observed_at,
               created_at, notes
        FROM observations
        WHERE {where_sql}
        ORDER BY confidence DESC NULLS LAST,
                 observed_at DESC NULLS LAST,
                 created_at DESC
        LIMIT :limit OFFSET :offset
    """), params).fetchall()
    total = db.execute(
        text(f"SELECT COUNT(*) FROM observations WHERE {where_sql}"), params,
    ).scalar() or 0

    return {
        "items":    [dict(r._mapping) for r in rows],
        "total":    int(total),
        "page":     page,
        "per_page": per_page,
    }
