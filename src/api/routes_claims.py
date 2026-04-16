"""
src/api/routes_claims.py

REST API for SSP-narrative claim extraction (Phase 4.1).

Route ordering: static paths (``/extract-all``, ``/summary``,
``/by-section/{id}``) precede the dynamic ``/{claim_id}`` PATCH.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.auth import get_current_user, ADMIN_ROLES
from src.db.session import get_db
from src.truth.claim_extractor import (
    extract_claims_for_org,
    extract_claims_from_section,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/claims", tags=["claims"])


_VALID_TYPES    = {"POLICY", "TECHNICAL", "OPERATIONAL"}
_VALID_STATUSES = {"UNVERIFIED", "VERIFIED", "CONFLICT", "STALE"}


def _require_admin(user: dict) -> None:
    if user.get("role") not in ADMIN_ROLES:
        raise HTTPException(403, "Admin required")


def _audit(db: Session, *, actor: str, action: str, target_id: str, details: dict) -> None:
    try:
        from src.evidence.state_machine import create_audit_entry
        create_audit_entry(
            db=db, actor=actor, actor_type="user", action=action,
            target_type="claim", target_id=target_id, details=details,
        )
    except Exception:
        logger.exception("audit %s failed", action)


def _safe_user_fk(db: Session, user_id: Optional[str]) -> Optional[str]:
    if not user_id:
        return None
    row = db.execute(text("SELECT 1 FROM users WHERE id = :id"), {"id": user_id}).fetchone()
    return user_id if row else None


def _latest_section_for_control(db: Session, org_id: str, control_id: str) -> Optional[dict]:
    row = db.execute(text("""
        SELECT ss.id, ss.control_id, ss.narrative,
               COALESCE(c.title, ss.control_id) AS control_title
        FROM ssp_sections ss
        LEFT JOIN controls c ON c.id = ss.control_id
        WHERE ss.org_id = :org_id AND ss.control_id = :cid
        ORDER BY ss.version DESC
        LIMIT 1
    """), {"org_id": org_id, "cid": control_id}).fetchone()
    if not row:
        return None
    return {
        "id":            row.id,
        "control_id":    row.control_id,
        "narrative":     row.narrative or "",
        "control_title": row.control_title,
    }


# ───────────────────────────────────────────────────────────────────────────
# Static routes
# ───────────────────────────────────────────────────────────────────────────

@router.get("/summary")
def claims_summary(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Aggregate counts for the Overview widget."""
    org_id = user["org_id"]

    total = db.execute(
        text("SELECT COUNT(*) FROM claims WHERE org_id = :o"),
        {"o": org_id},
    ).scalar() or 0

    type_rows = db.execute(text("""
        SELECT claim_type, COUNT(*) FROM claims
        WHERE org_id = :o GROUP BY claim_type
    """), {"o": org_id}).fetchall()
    by_type = {r[0]: int(r[1]) for r in type_rows}

    status_rows = db.execute(text("""
        SELECT verification_status, COUNT(*) FROM claims
        WHERE org_id = :o GROUP BY verification_status
    """), {"o": org_id}).fetchall()
    by_status = {r[0]: int(r[1]) for r in status_rows}

    family_rows = db.execute(text("""
        SELECT SPLIT_PART(control_id, '.', 1) AS family, COUNT(*) AS cnt
        FROM claims
        WHERE org_id = :o
        GROUP BY family
        ORDER BY cnt DESC
    """), {"o": org_id}).fetchall()
    by_family = {r[0]: int(r[1]) for r in family_rows}

    return {
        "total":     int(total),
        "by_type":   by_type,
        "by_status": by_status,
        "by_family": by_family,
    }


@router.get("/by-section/{ssp_section_id}")
def claims_by_section(
    ssp_section_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """All claims for a section, ordered by source_span_start so the
    SSP page can render them inline with the narrative."""
    rows = db.execute(text("""
        SELECT id, org_id, control_id, ssp_section_id, claim_text, claim_type,
               verification_status, source_sentence, source_span_start,
               source_span_end, confidence, evidence_refs,
               extracted_at, extraction_model, verified_at, verified_by, notes
        FROM claims
        WHERE org_id = :o AND ssp_section_id = :sid
        ORDER BY COALESCE(source_span_start, 0) ASC, id ASC
    """), {"o": user["org_id"], "sid": ssp_section_id}).fetchall()
    return {"items": [dict(r._mapping) for r in rows], "count": len(rows)}


@router.post("/extract-all")
def extract_all(
    body: Optional[dict] = Body(default=None),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Run extraction over every SSP section in the org. Expensive — one
    LLM call per section. Optional ``control_ids`` limits the scope."""
    _require_admin(user)

    control_ids = None
    if body and isinstance(body.get("control_ids"), list):
        control_ids = [str(c) for c in body["control_ids"] if c]

    summary = extract_claims_for_org(
        org_id=user["org_id"],
        db=db,
        user_id=user["id"],
        control_ids=control_ids,
    )
    if summary["total_sections_processed"] > 50:
        summary["warning"] = (
            f"Processed {summary['total_sections_processed']} sections — "
            "this is a long-running and LLM-costly operation."
        )
    return summary


@router.post("/extract/{control_id}")
def extract_one(
    control_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Extract claims for the latest SSP section of ``control_id``."""
    _require_admin(user)

    section = _latest_section_for_control(db, user["org_id"], control_id)
    if not section:
        raise HTTPException(404, f"No SSP section found for {control_id}")

    if not section["narrative"].strip():
        return {"claims": [], "count": 0, "note": "Section has no narrative"}

    claims = extract_claims_from_section(
        narrative=section["narrative"],
        control_id=section["control_id"],
        control_title=section["control_title"],
        org_id=user["org_id"],
        ssp_section_id=section["id"],
        db=db,
        user_id=user["id"],
    )
    return {
        "claims":         claims,
        "count":          len(claims),
        "ssp_section_id": section["id"],
        "control_id":     section["control_id"],
    }


@router.get("")
def list_claims(
    control_id:          Optional[str] = Query(None),
    claim_type:          Optional[str] = Query(None),
    verification_status: Optional[str] = Query(None),
    page:                int           = Query(1,  ge=1),
    per_page:            int           = Query(50, ge=1, le=200),
    db:   Session = Depends(get_db),
    user: dict    = Depends(get_current_user),
):
    """Paginated, filterable list of claims for the caller's org."""
    where = ["org_id = :o"]
    params: dict = {
        "o":      user["org_id"],
        "limit":  per_page,
        "offset": (page - 1) * per_page,
    }
    if control_id:
        where.append("control_id = :cid")
        params["cid"] = control_id
    if claim_type:
        where.append("claim_type = :ctype")
        params["ctype"] = claim_type.upper()
    if verification_status:
        where.append("verification_status = :vs")
        params["vs"] = verification_status.upper()
    where_sql = " AND ".join(where)

    rows = db.execute(text(f"""
        SELECT id, org_id, control_id, ssp_section_id, claim_text, claim_type,
               verification_status, source_sentence, source_span_start,
               source_span_end, confidence, evidence_refs,
               extracted_at, extraction_model, verified_at, verified_by, notes
        FROM claims
        WHERE {where_sql}
        ORDER BY control_id ASC, COALESCE(source_span_start, 0) ASC, id ASC
        LIMIT :limit OFFSET :offset
    """), params).fetchall()
    total = db.execute(
        text(f"SELECT COUNT(*) FROM claims WHERE {where_sql}"), params
    ).scalar() or 0

    return {
        "items":    [dict(r._mapping) for r in rows],
        "total":    int(total),
        "page":     page,
        "per_page": per_page,
    }


# ───────────────────────────────────────────────────────────────────────────
# Dynamic route — PATCH by claim_id goes LAST
# ───────────────────────────────────────────────────────────────────────────

_ALLOWED_TRANSITIONS = {
    "UNVERIFIED": {"VERIFIED", "CONFLICT", "STALE"},
    "VERIFIED":   {"STALE"},
    "CONFLICT":   {"STALE", "VERIFIED"},
    "STALE":      {"UNVERIFIED"},
}


@router.patch("/{claim_id}")
def update_claim(
    claim_id: str,
    body: dict,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Update verification_status and/or notes. Admin-only."""
    _require_admin(user)

    current = db.execute(text("""
        SELECT verification_status FROM claims
        WHERE id = :id AND org_id = :o
    """), {"id": claim_id, "o": user["org_id"]}).fetchone()
    if not current:
        raise HTTPException(404, "Claim not found")

    updates: dict = {}
    changed_status = False

    new_status = body.get("verification_status") or body.get("status")
    if new_status is not None:
        ns = str(new_status).upper()
        if ns not in _VALID_STATUSES:
            raise HTTPException(400, f"Status must be one of {sorted(_VALID_STATUSES)}")
        allowed = _ALLOWED_TRANSITIONS.get(current.verification_status, set())
        if ns != current.verification_status and ns not in allowed:
            raise HTTPException(
                400,
                f"Cannot transition {current.verification_status} → {ns}",
            )
        updates["verification_status"] = ns
        changed_status = (ns != current.verification_status)

    if "notes" in body:
        updates["notes"] = body.get("notes")

    if not updates:
        raise HTTPException(400, "Nothing to update")

    now = datetime.now(timezone.utc)
    safe_user = _safe_user_fk(db, user["id"])

    if changed_status:
        if updates["verification_status"] == "UNVERIFIED":
            updates["verified_at"] = None
            updates["verified_by"] = None
        else:
            updates["verified_at"] = now
            updates["verified_by"] = safe_user

    set_sql = ", ".join(f"{k} = :{k}" for k in updates)
    params = {**updates, "id": claim_id, "o": user["org_id"]}

    db.execute(text(f"""
        UPDATE claims SET {set_sql}
        WHERE id = :id AND org_id = :o
    """), params)

    if changed_status:
        _audit(
            db,
            actor=safe_user or "system",
            action="CLAIM_STATUS_CHANGED",
            target_id=claim_id,
            details={
                "org_id":   user["org_id"],
                "from":     current.verification_status,
                "to":       updates["verification_status"],
            },
        )
    db.commit()

    return {"id": claim_id, **{k: updates[k] for k in updates if k in ("verification_status", "notes")}}
