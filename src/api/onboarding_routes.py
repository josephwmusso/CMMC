"""
src/api/onboarding_routes.py

Phase 1.6F — onboarding wizard endpoints.

Saves organization + tech-stack info in a single transaction across three
tables (organizations, company_profiles, intake_responses) and flips
users.onboarding_complete so the frontend wizard stops firing.

Design choices (per the 1.6F audit conversation):
  * Only canonical Module 0 question IDs are used (no invented IDs).
  * Identity provider + MFA are folded into the canonical Module 0 option
    string (e.g. "Microsoft Entra ID (Azure AD) with MFA"); the raw
    pieces are preserved in answer_details JSON.
  * Gap computation is intentionally skipped during onboarding — the
    mapped values are all "good" canonical answers, so flags would
    always be false. Normal gap eval still fires when the user walks the
    real intake questionnaire.
  * backup_tool + training_tool have no Module 0 question; they persist
    only to company_profiles (backup_solution + training_solution).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.auth import get_current_user
from src.db.session import get_db

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


# ============================================================================
# Request / response models
# ============================================================================

class OrganizationInfo(BaseModel):
    name: str
    city: str = ""
    state: str = ""
    employee_count: int = 0
    system_name: str = ""


class TechStack(BaseModel):
    identity_provider: str = ""
    mfa_enabled: bool = False
    email_platform: str = ""
    edr_tool: str = ""
    firewall: str = ""
    siem: str = ""
    backup_tool: str = ""
    training_tool: str = ""


class OnboardingRequest(BaseModel):
    organization: OrganizationInfo
    tech_stack: TechStack
    cui_types: list[str] = []


class OnboardingComplete(BaseModel):
    success: bool
    session_id: Optional[str] = None
    responses_saved: int
    onboarding_complete: bool


class OnboardingStatus(BaseModel):
    onboarding_complete: bool
    has_company_profile: bool
    has_intake_session: bool


# ============================================================================
# Helpers
# ============================================================================

def _canonical_idp(identity_provider: str, mfa_enabled: bool) -> str:
    """Fold identity_provider + mfa_enabled into a canonical Module 0 option.

    Options defined in module0_foundation.py:
      - "Microsoft Entra ID (Azure AD) with MFA"
      - "Microsoft Entra ID (Azure AD) without MFA"
      - "On-premises Active Directory with MFA"
      - "On-premises Active Directory without MFA"
      - "Okta"
      - "Google Identity"
      - "No centralized login system"
      - "I'm not sure"
    """
    if not identity_provider:
        return ""
    low = identity_provider.lower().strip()
    mfa_suffix = " with MFA" if mfa_enabled else " without MFA"
    if "entra" in low or "azure ad" in low or ("microsoft" in low and "ad" in low):
        return f"Microsoft Entra ID (Azure AD){mfa_suffix}"
    if "active directory" in low or low.startswith("ad "):
        return f"On-premises Active Directory{mfa_suffix}"
    if "okta" in low:
        return "Okta"
    if "google" in low:
        return "Google Identity"
    if low in ("none", "no centralized login system", "no idp"):
        return "No centralized login system"
    # Unknown values pass through untouched.
    return identity_provider


def _active_session_id(db: Session, org_id: str) -> Optional[str]:
    row = db.execute(text("""
        SELECT id FROM intake_sessions
        WHERE org_id = :org_id
        ORDER BY started_at DESC
        LIMIT 1
    """), {"org_id": org_id}).fetchone()
    return row[0] if row else None


def _create_intake_session(db: Session, org_id: str) -> str:
    now = datetime.now(timezone.utc)
    session_id = hashlib.sha256(f"{org_id}:{now.isoformat()}".encode()).hexdigest()[:20]
    db.execute(text("""
        INSERT INTO intake_sessions (id, org_id, started_at, updated_at, current_module, status)
        VALUES (:id, :org_id, :now, :now, 0, 'in_progress')
        ON CONFLICT (id) DO NOTHING
    """), {"id": session_id, "org_id": org_id, "now": now.isoformat()})
    return session_id


def _upsert_intake_response(
    db: Session,
    *,
    session_id: str,
    org_id: str,
    question_id: str,
    answer_value: str,
    answer_details: Optional[dict] = None,
    control_ids: Optional[list[str]] = None,
    answer_type: str = "text",
    module_id: int = 0,
    question_tier: str = "SCREENING",
) -> None:
    """Upsert a single intake_responses row — no gap evaluation (canonical
    values only; gaps get re-computed when the user walks the real intake).
    """
    now = datetime.now(timezone.utc).isoformat()
    row_id = hashlib.sha256(f"{session_id}:{question_id}".encode()).hexdigest()[:20]
    db.execute(text("""
        INSERT INTO intake_responses
            (id, session_id, org_id, module_id, question_id, control_ids,
             answer_type, answer_value, answer_details,
             creates_gap, gap_severity, question_tier, answered_at)
        VALUES
            (:id, :sid, :oid, :mid, :qid, CAST(:cids AS json),
             :atype, :aval, CAST(:adetails AS json),
             FALSE, NULL, :tier, :now)
        ON CONFLICT (session_id, question_id) DO UPDATE SET
            answer_value    = :aval,
            answer_details  = CAST(:adetails AS json),
            answer_type     = :atype,
            module_id       = :mid,
            control_ids     = CAST(:cids AS json),
            question_tier   = :tier,
            creates_gap     = FALSE,
            gap_severity    = NULL,
            answered_at     = :now
    """), {
        "id":       row_id,
        "sid":      session_id,
        "oid":      org_id,
        "mid":      module_id,
        "qid":      question_id,
        "cids":     json.dumps(control_ids or []),
        "atype":    answer_type,
        "aval":     answer_value,
        "adetails": json.dumps(answer_details) if answer_details else "{}",
        "tier":     question_tier,
        "now":      now,
    })


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/complete", response_model=OnboardingComplete)
def complete_onboarding(
    req: OnboardingRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Persist org info + tech stack to organizations + company_profiles +
    intake_responses, create/reuse an intake session, flip the user's
    onboarding flag. Single DB transaction."""
    org_id = current_user["org_id"]
    user_id = current_user["id"]

    # Verify the org exists (the caller's JWT might point at a missing org
    # right after a user→org migration gone wrong; fail loudly).
    org_row = db.execute(
        text("SELECT id FROM organizations WHERE id = :id"),
        {"id": org_id},
    ).fetchone()
    if not org_row:
        raise HTTPException(404, "Organization not found for current user")

    now_iso = datetime.now(timezone.utc).isoformat()
    canonical_idp = _canonical_idp(req.tech_stack.identity_provider, req.tech_stack.mfa_enabled)
    location_combined = ", ".join([p for p in (req.organization.city, req.organization.state) if p])
    cui_joined = ", ".join(req.cui_types) if req.cui_types else ""

    try:
        # ── A. Update organizations ───────────────────────────────────────
        db.execute(text("""
            UPDATE organizations SET
                name           = :name,
                city           = :city,
                state          = :state,
                employee_count = :emp,
                system_name    = COALESCE(NULLIF(:sys, ''), system_name),
                updated_at     = :now
            WHERE id = :id
        """), {
            "name": req.organization.name,
            "city": req.organization.city or None,
            "state": req.organization.state or None,
            "emp":  req.organization.employee_count or None,
            "sys":  req.organization.system_name,
            "now":  now_iso,
            "id":   org_id,
        })

        # ── B. Upsert company_profiles ────────────────────────────────────
        profile_id = hashlib.sha256(f"profile:{org_id}".encode()).hexdigest()[:20]
        db.execute(text("""
            INSERT INTO company_profiles
                (id, org_id, company_name, employee_count, primary_location,
                 cui_types, identity_provider, email_platform,
                 edr_product, firewall_product, siem_product,
                 backup_solution, training_solution,
                 created_at, updated_at)
            VALUES
                (:id, :oid, :name, :emp, :loc,
                 CAST(:cui AS json), :idp, :email,
                 :edr, :fw, :siem,
                 :backup, :training,
                 :now, :now)
            ON CONFLICT (org_id) DO UPDATE SET
                company_name       = :name,
                employee_count     = :emp,
                primary_location   = :loc,
                cui_types          = CAST(:cui AS json),
                identity_provider  = :idp,
                email_platform     = :email,
                edr_product        = :edr,
                firewall_product   = :fw,
                siem_product       = :siem,
                backup_solution    = :backup,
                training_solution  = :training,
                updated_at         = :now
        """), {
            "id":       profile_id,
            "oid":      org_id,
            "name":     req.organization.name,
            "emp":      req.organization.employee_count or None,
            "loc":      location_combined or None,
            "cui":      json.dumps(req.cui_types or []),
            "idp":      canonical_idp or None,
            "email":    req.tech_stack.email_platform or None,
            "edr":      req.tech_stack.edr_tool or None,
            "fw":       req.tech_stack.firewall or None,
            "siem":     req.tech_stack.siem or None,
            "backup":   req.tech_stack.backup_tool or None,
            "training": req.tech_stack.training_tool or None,
            "now":      now_iso,
        })

        # ── C. Intake session + Module 0 responses ───────────────────────
        session_id = _active_session_id(db, org_id) or _create_intake_session(db, org_id)

        responses_saved = 0

        def save(qid: str, value: str, *, atype: str = "text",
                 details: Optional[dict] = None) -> None:
            nonlocal responses_saved
            if value is None or value == "":
                return
            _upsert_intake_response(
                db,
                session_id=session_id,
                org_id=org_id,
                question_id=qid,
                answer_value=value,
                answer_type=atype,
                answer_details=details,
            )
            responses_saved += 1

        # Organization-info → Module 0
        save("m0_company_name", req.organization.name)
        if req.organization.employee_count:
            save("m0_employee_count", str(req.organization.employee_count), atype="number")
        if location_combined:
            save(
                "m0_primary_location",
                location_combined,
                details={"city": req.organization.city, "state": req.organization.state},
            )

        # Tech stack → Module 0
        if canonical_idp:
            save(
                "m0_identity_provider",
                canonical_idp,
                atype="multiple_choice",
                details={
                    "provider_raw":  req.tech_stack.identity_provider,
                    "mfa_enabled":   req.tech_stack.mfa_enabled,
                    "canonicalized": canonical_idp,
                },
            )
        save("m0_email_platform", req.tech_stack.email_platform, atype="multiple_choice")
        save("m0_edr", req.tech_stack.edr_tool, atype="multiple_choice")
        save("m0_firewall", req.tech_stack.firewall, atype="multiple_choice")
        save("m0_siem", req.tech_stack.siem, atype="multiple_choice")
        save("m0_training_tool", req.tech_stack.training_tool, atype="multiple_choice")

        # CUI types: multi-choice stored as comma-joined string + raw list in details
        if req.cui_types:
            save(
                "m0_cui_types",
                cui_joined,
                atype="multiple_choice",
                details={"selected": req.cui_types},
            )

        # ── D. Flip the onboarding flag ──────────────────────────────────
        db.execute(
            text("UPDATE users SET onboarding_complete = TRUE WHERE id = :id"),
            {"id": user_id},
        )

        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, f"Onboarding failed: {exc}")

    return OnboardingComplete(
        success=True,
        session_id=session_id,
        responses_saved=responses_saved,
        onboarding_complete=True,
    )


@router.get("/status", response_model=OnboardingStatus)
def onboarding_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = current_user["org_id"]
    user_id = current_user["id"]

    user_row = db.execute(
        text("SELECT onboarding_complete FROM users WHERE id = :id"),
        {"id": user_id},
    ).fetchone()
    # DEV_USER isn't in the DB — fall back to the dict's value.
    user_complete = bool(
        user_row[0] if user_row else current_user.get("onboarding_complete", False)
    )

    profile_row = db.execute(
        text("SELECT 1 FROM company_profiles WHERE org_id = :oid"),
        {"oid": org_id},
    ).fetchone()
    session_row = db.execute(
        text("SELECT 1 FROM intake_sessions WHERE org_id = :oid LIMIT 1"),
        {"oid": org_id},
    ).fetchone()

    return OnboardingStatus(
        onboarding_complete=user_complete,
        has_company_profile=bool(profile_row),
        has_intake_session=bool(session_row),
    )


@router.post("/skip")
def skip_onboarding(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Flip onboarding_complete without saving any data. Used when the user
    chooses to fill the wizard later."""
    db.execute(
        text("UPDATE users SET onboarding_complete = TRUE WHERE id = :id"),
        {"id": current_user["id"]},
    )
    db.commit()
    return {"success": True}
