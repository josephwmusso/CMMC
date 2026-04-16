"""
src/api/routes_affirmations.py

Annual affirmation API (Phase 6.4, 32 CFR 170.22).
"""
from __future__ import annotations

import base64
import hashlib
import io
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.auth import get_current_user, ADMIN_ROLES
from src.compliance.affirmation import (
    create_affirmation,
    generate_certificate_pdf,
    get_affirmation,
    get_affirmation_status,
    list_affirmations,
)
from src.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/affirmations", tags=["affirmations"])


def _require_admin(user: dict) -> None:
    if user.get("role") not in ADMIN_ROLES:
        raise HTTPException(403, "Admin required")


class AffirmRequest(BaseModel):
    affirmer_title: str
    attestation_text: Optional[str] = None
    material_changes: Optional[str] = None
    confirm: bool = False


# ── Static routes first ───────────────────────────────────────────────────

@router.get("/status")
def affirmation_status(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Current affirmation state for the caller's org. Any authenticated user."""
    return get_affirmation_status(user["org_id"], db)


@router.post("")
def create(
    body: AffirmRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Create a new affirmation. The logged-in user IS the affirmer."""
    _require_admin(user)

    if not body.confirm:
        raise HTTPException(
            400,
            "Set confirm=true to create an affirmation. "
            "This is a legally significant action per 32 CFR 170.22.",
        )

    ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or (request.client.host if request.client else None)
    )

    aff_dict, pdf_bytes = create_affirmation(
        org_id=user["org_id"],
        db=db,
        user_id=user["id"],
        user_email=user.get("email", ""),
        user_name=user.get("full_name") or user.get("email", ""),
        affirmer_title=body.affirmer_title,
        attestation_text=body.attestation_text,
        material_changes=body.material_changes,
        ip_address=ip,
    )
    aff_dict["certificate_pdf_base64"] = base64.b64encode(pdf_bytes).decode()
    return aff_dict


@router.get("")
def list_all(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Affirmation history for the org. Admin only."""
    _require_admin(user)
    return list_affirmations(user["org_id"], db)


# ── Dynamic routes ────────────────────────────────────────────────────────

@router.get("/{affirmation_id}")
def get_one(
    affirmation_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    _require_admin(user)
    aff = get_affirmation(affirmation_id, user["org_id"], db)
    if not aff:
        raise HTTPException(404, "Affirmation not found")
    return aff


@router.get("/{affirmation_id}/certificate")
def get_certificate(
    affirmation_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Regenerate and stream the PDF certificate."""
    _require_admin(user)
    aff = get_affirmation(affirmation_id, user["org_id"], db)
    if not aff:
        raise HTTPException(404, "Affirmation not found")

    from src.compliance.affirmation import _load_org_profile
    org_profile = _load_org_profile(user["org_id"], db)
    pdf_bytes = generate_certificate_pdf(aff, org_profile, db)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="affirmation_{affirmation_id}.pdf"'},
    )


@router.get("/{affirmation_id}/verify")
def verify_certificate(
    affirmation_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Regenerate the PDF and compare hash to stored certificate_hash."""
    _require_admin(user)
    aff = get_affirmation(affirmation_id, user["org_id"], db)
    if not aff:
        raise HTTPException(404, "Affirmation not found")

    from src.compliance.affirmation import _load_org_profile
    org_profile = _load_org_profile(user["org_id"], db)
    pdf_bytes = generate_certificate_pdf(aff, org_profile, db)
    computed = hashlib.sha256(pdf_bytes).hexdigest()
    expected = aff.get("certificate_hash") or ""

    return {
        "hash_matches":  computed == expected,
        "expected_hash": expected,
        "computed_hash": computed,
    }
