"""
src/api/routes_freshness.py

Evidence freshness API (Phase 4.4). Freshness is computed on read for
individual items; the POST /refresh-claims endpoint is the only write
path (flips VERIFIED ↔ STALE on claims).
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.auth import get_current_user, ADMIN_ROLES
from src.db.session import get_db
from src.truth.freshness import (
    calculate_evidence_freshness,
    calculate_observation_freshness,
    get_freshness_summary,
    list_stale_items,
    refresh_claim_staleness,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/freshness", tags=["freshness"])


def _require_admin(user: dict) -> None:
    if user.get("role") not in ADMIN_ROLES:
        raise HTTPException(403, "Admin required")


@router.get("/summary")
def freshness_summary(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Aggregate freshness for the Overview widget."""
    return get_freshness_summary(user["org_id"], db)


@router.get("/stale")
def stale_items(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List of stale evidence + observations, sorted by age DESC."""
    return list_stale_items(user["org_id"], db)


@router.post("/refresh-claims")
def refresh_claims(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Walk VERIFIED/STALE claims and flip status based on supporting
    observation freshness. Admin-only."""
    _require_admin(user)
    return refresh_claim_staleness(user["org_id"], db, user["id"])


@router.get("/evidence/{evidence_id}")
def evidence_freshness(
    evidence_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Freshness detail for one evidence artifact."""
    result = calculate_evidence_freshness(evidence_id, db, user["org_id"])
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


@router.get("/observation/{observation_id}")
def obs_freshness(
    observation_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Freshness detail for one observation."""
    result = calculate_observation_freshness(observation_id, db, user["org_id"])
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result
