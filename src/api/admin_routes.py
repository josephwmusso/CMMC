"""
src/api/admin_routes.py

Admin endpoints for managing users, organizations, and invites (Phase 1.6B).

Permission model:
  - SUPERADMIN can do everything, across any org.
  - ADMIN can manage users and invites within their own org, but may only
    create/change roles MEMBER or VIEWER. Only a SUPERADMIN can promote
    someone to ADMIN or SUPERADMIN. Org CRUD is SUPERADMIN-only.
  - Nobody can modify or deactivate their own account via these routes
    (prevents self-lockout). Nobody can deactivate a SUPERADMIN.

Audit trail:
  - Org creation writes an audit_log entry via the canonical
    src.evidence.state_machine.create_audit_entry helper so the hash
    chain stays intact.
"""
from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.auth import (
    ADMIN_ROLES,
    ROLE_ADMIN,
    ROLE_MEMBER,
    ROLE_SUPERADMIN,
    ROLE_VIEWER,
    hash_password,
    is_admin_role,
    is_superadmin,
    require_admin_dep,
    require_superadmin_dep,
)
from src.db.session import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Roles an ADMIN is allowed to assign / manipulate.
ADMIN_ASSIGNABLE_ROLES = {ROLE_MEMBER, ROLE_VIEWER}
# Roles a SUPERADMIN is allowed to assign (anything below SUPERADMIN).
SUPERADMIN_ASSIGNABLE_ROLES = {ROLE_ADMIN, ROLE_MEMBER, ROLE_VIEWER}
# Full set.
ALL_ROLES = {ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_MEMBER, ROLE_VIEWER}

# Used to build invite URLs for the response payload.
BASE_URL = os.getenv("BASE_URL", "http://localhost:5173")


# ============================================================================
# Request / response models
# ============================================================================

class UserCreateReq(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = ""
    role: Optional[str] = ROLE_MEMBER


class UserUpdateReq(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_admin: bool
    org_id: str
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    deactivated_at: Optional[datetime] = None


class OrgCreateReq(BaseModel):
    name: str
    city: Optional[str] = None
    state: Optional[str] = None
    employee_count: Optional[int] = None
    cui_types: Optional[list[str]] = None


class OrgOut(BaseModel):
    id: str
    name: str
    city: Optional[str] = None
    state: Optional[str] = None
    employee_count: Optional[int] = None
    created_at: Optional[datetime] = None
    user_count: Optional[int] = None


class InviteCreateReq(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = ROLE_MEMBER
    full_name: Optional[str] = None  # used to personalize the invite email greeting


class InviteOut(BaseModel):
    id: str
    code: str
    email: Optional[str] = None
    role: str
    created_by: str
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    used_at: Optional[datetime] = None
    used_by: Optional[str] = None
    invite_url: Optional[str] = None
    email_sent: bool = False  # True if Resend accepted the invite send


# ============================================================================
# Helpers
# ============================================================================

def _derive_id(text_in: str) -> str:
    return hashlib.sha256(text_in.encode()).hexdigest()[:20]


def _user_row_to_out(row) -> UserOut:
    """Convert a SELECT row (positional) to a UserOut."""
    return UserOut(
        id=row[0],
        email=row[1],
        full_name=row[2] or "",
        role=(row[3] or ROLE_MEMBER).upper(),
        is_admin=(row[3] or ROLE_MEMBER).upper() in ADMIN_ROLES,
        org_id=row[4],
        created_at=row[5],
        last_login_at=row[6],
        deactivated_at=row[7],
    )


def _validate_role(role: str, requester_is_superadmin: bool) -> str:
    """Ensure ``role`` is assignable by the requester. Returns the upper-cased
    role string. Raises 400/403 on bad input."""
    role_u = (role or "").upper().strip()
    if role_u not in ALL_ROLES:
        raise HTTPException(400, f"Invalid role '{role}'")
    if role_u == ROLE_SUPERADMIN:
        # Never assignable via these endpoints — one superadmin is seeded.
        raise HTTPException(403, "Cannot assign SUPERADMIN role via admin API")
    if requester_is_superadmin:
        if role_u not in SUPERADMIN_ASSIGNABLE_ROLES:
            raise HTTPException(403, f"Superadmin cannot assign role '{role_u}'")
    else:
        if role_u not in ADMIN_ASSIGNABLE_ROLES:
            raise HTTPException(403, f"Admin can only assign {sorted(ADMIN_ASSIGNABLE_ROLES)}")
    return role_u


def _fetch_user(db: Session, user_id: str):
    row = db.execute(text("""
        SELECT id, email, full_name, role, org_id, created_at, last_login_at, deactivated_at
        FROM users WHERE id = :id
    """), {"id": user_id}).fetchone()
    return row


def _ensure_same_org_or_super(target_org: str, caller: dict):
    if is_superadmin(caller):
        return
    if target_org != caller["org_id"]:
        raise HTTPException(403, "Target user belongs to a different organization")


# ============================================================================
# User management — requires ADMIN or SUPERADMIN
# ============================================================================

@router.post("/users", response_model=UserOut, status_code=201)
def create_user(
    req: UserCreateReq,
    caller: dict = Depends(require_admin_dep),
    db: Session = Depends(get_db),
):
    """Create a new user inside the caller's org (or inside any org if SUPERADMIN)."""
    role = _validate_role(req.role or ROLE_MEMBER, is_superadmin(caller))
    # ADMIN cannot create in a foreign org; SUPERADMIN implicitly uses their own.
    org_id = caller["org_id"]

    existing = db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": req.email},
    ).fetchone()
    if existing:
        raise HTTPException(409, "Email already registered")

    user_id = _derive_id(req.email)
    hashed = hash_password(req.password)

    db.execute(text("""
        INSERT INTO users (id, email, org_id, full_name, hashed_password, is_admin, role, created_at)
        VALUES (:id, :email, :org_id, :full_name, :pw, :is_admin, :role, NOW())
    """), {
        "id": user_id,
        "email": req.email,
        "org_id": org_id,
        "full_name": req.full_name or "",
        "pw": hashed,
        "is_admin": role in ADMIN_ROLES,
        "role": role,
    })
    db.commit()

    row = _fetch_user(db, user_id)
    return _user_row_to_out(row)


@router.get("/users", response_model=list[UserOut])
def list_users(
    org_id: Optional[str] = Query(None, description="Superadmin-only filter"),
    caller: dict = Depends(require_admin_dep),
    db: Session = Depends(get_db),
):
    """List users in the caller's org. Superadmin may pass ?org_id=X to
    query any org."""
    if org_id and not is_superadmin(caller):
        raise HTTPException(403, "Only superadmin may list users across orgs")
    effective_org = org_id or caller["org_id"]

    rows = db.execute(text("""
        SELECT id, email, full_name, role, org_id, created_at, last_login_at, deactivated_at
        FROM users
        WHERE org_id = :org_id
        ORDER BY created_at DESC
    """), {"org_id": effective_org}).fetchall()
    return [_user_row_to_out(r) for r in rows]


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    req: UserUpdateReq,
    caller: dict = Depends(require_admin_dep),
    db: Session = Depends(get_db),
):
    row = _fetch_user(db, user_id)
    if not row:
        raise HTTPException(404, "User not found")
    target = _user_row_to_out(row)
    _ensure_same_org_or_super(target.org_id, caller)

    if user_id == caller["id"]:
        # Allow self-updates to full_name/email but NOT to role.
        if req.role is not None and req.role.upper() != target.role:
            raise HTTPException(403, "Cannot change your own role")

    updates = {}
    if req.full_name is not None:
        updates["full_name"] = req.full_name
    if req.email is not None and req.email != target.email:
        clash = db.execute(
            text("SELECT id FROM users WHERE email = :email AND id <> :id"),
            {"email": req.email, "id": user_id},
        ).fetchone()
        if clash:
            raise HTTPException(409, "Email already registered")
        updates["email"] = req.email
    if req.role is not None:
        new_role = _validate_role(req.role, is_superadmin(caller))
        # ADMIN cannot promote/demote a SUPERADMIN or ADMIN target.
        if not is_superadmin(caller) and target.role in ADMIN_ROLES:
            raise HTTPException(403, "Admin cannot modify an admin's role")
        updates["role"] = new_role
        updates["is_admin"] = new_role in ADMIN_ROLES

    if not updates:
        return target

    # SQLAlchemy's text() bindparam parser doesn't handle postgres '::cast'
    # syntax — use explicit CAST(:val AS type) instead.
    set_parts = []
    for k in updates:
        if k == "role":
            set_parts.append("role = CAST(:role AS user_role)")
        else:
            set_parts.append(f"{k} = :{k}")
    set_sql = ", ".join(set_parts)
    params = {"id": user_id, **updates}
    db.execute(text(f"UPDATE users SET {set_sql} WHERE id = :id"), params)
    db.commit()
    return _user_row_to_out(_fetch_user(db, user_id))


@router.delete("/users/{user_id}")
def deactivate_user(
    user_id: str,
    caller: dict = Depends(require_admin_dep),
    db: Session = Depends(get_db),
):
    row = _fetch_user(db, user_id)
    if not row:
        raise HTTPException(404, "User not found")
    target = _user_row_to_out(row)
    if user_id == caller["id"]:
        raise HTTPException(403, "Cannot deactivate your own account")
    if target.role == ROLE_SUPERADMIN:
        raise HTTPException(403, "Cannot deactivate a SUPERADMIN")
    _ensure_same_org_or_super(target.org_id, caller)

    db.execute(
        text("UPDATE users SET deactivated_at = NOW() WHERE id = :id"),
        {"id": user_id},
    )
    db.commit()
    return {"message": "User deactivated", "user_id": user_id}


@router.post("/users/{user_id}/reactivate")
def reactivate_user(
    user_id: str,
    caller: dict = Depends(require_admin_dep),
    db: Session = Depends(get_db),
):
    row = _fetch_user(db, user_id)
    if not row:
        raise HTTPException(404, "User not found")
    target = _user_row_to_out(row)
    _ensure_same_org_or_super(target.org_id, caller)

    db.execute(
        text("UPDATE users SET deactivated_at = NULL WHERE id = :id"),
        {"id": user_id},
    )
    db.commit()
    return {"message": "User reactivated", "user_id": user_id}


# ============================================================================
# Organization management — SUPERADMIN only
# ============================================================================

@router.post("/orgs", response_model=OrgOut, status_code=201)
def create_org(
    req: OrgCreateReq,
    caller: dict = Depends(require_superadmin_dep),
    db: Session = Depends(get_db),
):
    """Create a new organization and write a canonical audit entry."""
    name = req.name.strip()
    if not name:
        raise HTTPException(400, "Organization name is required")

    existing = db.execute(
        text("SELECT id FROM organizations WHERE name = :name"),
        {"name": name},
    ).fetchone()
    if existing:
        raise HTTPException(409, "Organization name already exists")

    org_id = _derive_id(name)
    db.execute(text("""
        INSERT INTO organizations
            (id, name, city, state, employee_count, created_at, updated_at)
        VALUES
            (:id, :name, :city, :state, :emp, NOW(), NOW())
    """), {
        "id": org_id,
        "name": name,
        "city": req.city,
        "state": req.state,
        "emp": req.employee_count,
    })

    # Canonical audit entry (uses the single append-only chain).
    try:
        from src.evidence.state_machine import create_audit_entry
        create_audit_entry(
            db=db,
            actor=caller["id"],
            actor_type="user",
            action="ORG_CREATED",
            target_type="ORGANIZATION",
            target_id=org_id,
            details={
                "name": name,
                "city": req.city,
                "state": req.state,
                "employee_count": req.employee_count,
                "cui_types": req.cui_types or [],
                "created_by_email": caller.get("email"),
            },
        )
    except Exception:
        # Never let an audit failure stop org creation — log + continue.
        import logging as _lg
        _lg.getLogger(__name__).exception("Audit entry for ORG_CREATED failed")

    db.commit()
    row = db.execute(text("""
        SELECT id, name, city, state, employee_count, created_at
        FROM organizations WHERE id = :id
    """), {"id": org_id}).fetchone()
    return OrgOut(
        id=row[0], name=row[1], city=row[2], state=row[3],
        employee_count=row[4], created_at=row[5], user_count=0,
    )


@router.get("/orgs", response_model=list[OrgOut])
def list_orgs(
    caller: dict = Depends(require_superadmin_dep),
    db: Session = Depends(get_db),
):
    rows = db.execute(text("""
        SELECT o.id, o.name, o.city, o.state, o.employee_count, o.created_at,
               (SELECT COUNT(*) FROM users u WHERE u.org_id = o.id) AS user_count
        FROM organizations o
        ORDER BY o.created_at DESC NULLS LAST, o.name
    """)).fetchall()
    return [
        OrgOut(
            id=r[0], name=r[1], city=r[2], state=r[3],
            employee_count=r[4], created_at=r[5], user_count=int(r[6] or 0),
        )
        for r in rows
    ]


# ============================================================================
# Invite management — ADMIN or SUPERADMIN (within their org)
# ============================================================================

def _invite_out(row, include_url: bool = True) -> dict:
    from src.email.links import build_user_invite_link, build_new_customer_invite_link
    code = row[2]
    invite_type = row[10] if len(row) > 10 else "USER_TO_ORG"
    target_org_name = row[11] if len(row) > 11 else None

    # URL format depends on invite type
    if not include_url:
        url = None
    elif invite_type == "NEW_CUSTOMER":
        url = build_new_customer_invite_link(code)
    else:
        url = build_user_invite_link(code)

    # Derive status
    now = datetime.now(timezone.utc)
    expires = row[7]
    used = row[8]
    if used:
        status = "REDEEMED"
    elif expires and expires <= now:
        status = "EXPIRED"
    else:
        status = "PENDING"

    return {
        "id": row[0],
        "code": code,
        "email": row[3],
        "role": row[4],
        "invite_type": invite_type or "USER_TO_ORG",
        "target_org_name": target_org_name,
        "status": status,
        "created_by": row[5],
        "created_at": row[6].isoformat() if row[6] else None,
        "expires_at": row[7].isoformat() if row[7] else None,
        "used_at": row[8].isoformat() if row[8] else None,
        "used_by": row[9],
        "invite_url": url,
    }


@router.post("/invites", response_model=InviteOut, status_code=201)
def create_invite(
    req: InviteCreateReq,
    caller: dict = Depends(require_admin_dep),
    db: Session = Depends(get_db),
):
    role = _validate_role(req.role or ROLE_MEMBER, is_superadmin(caller))
    org_id = caller["org_id"]
    code = secrets.token_urlsafe(32)
    invite_id = hashlib.sha256(code.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    db.execute(text("""
        INSERT INTO invites
            (id, org_id, code, email, role, created_by, created_at, expires_at)
        VALUES
            (:id, :org_id, :code, :email, :role, :created_by, NOW(), :expires_at)
    """), {
        "id": invite_id,
        "org_id": org_id,
        "code": code,
        "email": req.email,
        "role": role,
        "created_by": caller["id"],
        "expires_at": expires_at,
    })
    db.commit()

    row = db.execute(text("""
        SELECT id, org_id, code, email, role, created_by, created_at, expires_at,
               used_at, used_by, COALESCE(invite_type, 'USER_TO_ORG'), target_org_name
        FROM invites WHERE id = :id
    """), {"id": invite_id}).fetchone()
    payload = _invite_out(row)

    # Send the invite email. Failures don't break the API call — the invite
    # row is committed, and invite_url is in the response so the admin can
    # fall back to manual link sharing.
    payload["email_sent"] = _send_invite_email(
        db=db,
        invitee_email=req.email,
        invitee_name=req.full_name,
        inviter_org_id=org_id,
        invite_link=payload.get("invite_url"),
    )
    return payload


def _send_invite_email(
    *,
    db: Session,
    invitee_email: Optional[str],
    invitee_name: Optional[str],
    inviter_org_id: str,
    invite_link: Optional[str],
) -> bool:
    """Send an invite email via Resend. Returns True on success, False on
    any failure (missing email, Resend down, network error, etc.). Never
    raises — the caller has already committed the invite row to the DB."""
    import logging
    logger = logging.getLogger(__name__)

    if not invitee_email or not invite_link:
        return False

    # Resolve org_name for the subject. One-line lookup; falls back to a
    # bare subject if the lookup fails for any reason.
    org_name: Optional[str] = None
    try:
        org_row = db.execute(
            text("SELECT name FROM organizations WHERE id = :id"),
            {"id": inviter_org_id},
        ).fetchone()
        if org_row and org_row[0]:
            org_name = org_row[0]
    except Exception as e:
        logger.warning(f"Invite email: org_name lookup failed: {e}")

    try:
        from configs.settings import RESEND_API_KEY, EMAIL_FROM, INVITE_BCC
        from src.email.invite_template import build_invite_email_html, build_invite_email_subject
        if not RESEND_API_KEY:
            logger.warning("Invite email skipped: RESEND_API_KEY not configured")
            return False
        import resend
        resend.api_key = RESEND_API_KEY
        resend.Emails.send({
            "from": f"Intranest Notifications <{EMAIL_FROM}>",
            "to": [invitee_email],
            "bcc": INVITE_BCC,
            "subject": build_invite_email_subject(org_name),
            "html": build_invite_email_html(invitee_name, invite_link, org_name),
        })
        return True
    except Exception as e:
        logger.warning(f"Invite email send failed for {invitee_email}: {e}")
        return False


@router.get("/invites")
def list_invites(
    caller: dict = Depends(require_admin_dep),
    db: Session = Depends(get_db),
):
    if is_superadmin(caller):
        # SUPERADMIN sees their org's USER_TO_ORG invites + ALL NEW_CUSTOMER invites
        rows = db.execute(text("""
            SELECT id, org_id, code, email, role, created_by, created_at, expires_at,
                   used_at, used_by, COALESCE(invite_type, 'USER_TO_ORG'), target_org_name
            FROM invites
            WHERE org_id = :org_id
               OR (invite_type = 'NEW_CUSTOMER' AND created_by = :uid)
               OR invite_type = 'NEW_CUSTOMER'
            ORDER BY created_at DESC
        """), {"org_id": caller["org_id"], "uid": caller["id"]}).fetchall()
    else:
        rows = db.execute(text("""
            SELECT id, org_id, code, email, role, created_by, created_at, expires_at,
                   used_at, used_by, COALESCE(invite_type, 'USER_TO_ORG'), target_org_name
            FROM invites
            WHERE org_id = :org_id
            ORDER BY created_at DESC
        """), {"org_id": caller["org_id"]}).fetchall()
    return [_invite_out(r) for r in rows]


@router.delete("/invites/{invite_id}")
def revoke_invite(
    invite_id: str,
    caller: dict = Depends(require_admin_dep),
    db: Session = Depends(get_db),
):
    row = db.execute(text("""
        SELECT id, org_id FROM invites WHERE id = :id
    """), {"id": invite_id}).fetchone()
    if not row:
        raise HTTPException(404, "Invite not found")
    invite_org = row[1]
    if invite_org != caller["org_id"] and not is_superadmin(caller):
        raise HTTPException(403, "Invite belongs to a different organization")

    db.execute(
        text("UPDATE invites SET expires_at = NOW() WHERE id = :id"),
        {"id": invite_id},
    )
    db.commit()
    return {"message": "Invite revoked"}
