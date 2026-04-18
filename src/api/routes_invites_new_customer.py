"""
src/api/routes_invites_new_customer.py

New-customer invite flow: SUPERADMIN creates invite → recipient sets
password → backend creates org + user + JWT → frontend's existing
ProtectedRoute gate pushes user into Onboarding.tsx.

Public endpoints (no auth): GET /{code}, POST /{code}/redeem.
Protected endpoint (SUPERADMIN): POST / (create invite).
"""
from __future__ import annotations

import hashlib
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.auth import (
    ROLE_ADMIN,
    ROLE_SUPERADMIN,
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
)
from src.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/invites/new-customer", tags=["invites"])


def _gen_id(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()[:20]


def _audit(db: Session, *, actor: str, action: str, target_id: str, details: dict) -> None:
    try:
        from src.evidence.state_machine import create_audit_entry
        create_audit_entry(
            db=db, actor=actor, actor_type="user", action=action,
            target_type="invite", target_id=target_id, details=details,
        )
    except Exception:
        logger.exception("audit %s failed", action)


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _safe_user_fk(db: Session, uid: Optional[str]) -> str:
    """Resolve a user ID that satisfies the users FK. In ALLOW_ANONYMOUS
    dev mode 'dev-user' isn't a real row — fall back to the seeded admin."""
    if uid:
        r = db.execute(text("SELECT 1 FROM users WHERE id = :id"), {"id": uid}).fetchone()
        if r:
            return uid
    fallback = db.execute(text("SELECT id FROM users ORDER BY created_at LIMIT 1")).fetchone()
    return fallback[0] if fallback else uid or "unknown"


# ── Models ────────────────────────────────────────────────────────────────

class NewCustomerInviteRequest(BaseModel):
    email: str
    full_name: str
    org_name: str


class RedeemRequest(BaseModel):
    password: str
    full_name: str


# ── Create invite (SUPERADMIN only) ──────────────────────────────────────

@router.post("")
def create_new_customer_invite(
    body: NewCustomerInviteRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    if user.get("role") != ROLE_SUPERADMIN:
        raise HTTPException(403, "SUPERADMIN required")

    email = body.email.strip().lower()
    org_name = body.org_name.strip()
    full_name = body.full_name.strip()

    if not _EMAIL_RE.match(email):
        raise HTTPException(400, "Invalid email format")
    if not (2 <= len(org_name) <= 200):
        raise HTTPException(400, "org_name must be 2-200 characters")
    if not (2 <= len(full_name) <= 100):
        raise HTTPException(400, "full_name must be 2-100 characters")

    existing_user = db.execute(
        text("SELECT 1 FROM users WHERE LOWER(email) = :e"),
        {"e": email},
    ).fetchone()
    if existing_user:
        raise HTTPException(
            409,
            "A user with this email already exists. "
            "Use the standard user invite flow to add them to an existing org instead.",
        )

    pending = db.execute(text("""
        SELECT code FROM invites
        WHERE LOWER(email) = :e
          AND invite_type = 'NEW_CUSTOMER'
          AND used_at IS NULL
          AND expires_at > NOW()
    """), {"e": email}).fetchone()
    if pending:
        from configs.settings import FRONTEND_BASE_URL
        existing_url = f"{FRONTEND_BASE_URL}/signup/{pending[0]}"
        raise HTTPException(
            409,
            detail={
                "message": "A pending new-customer invite already exists for this email.",
                "existing_invite_url": existing_url,
            },
        )

    invite_code = secrets.token_urlsafe(32)
    invite_id = hashlib.sha256(invite_code.encode()).hexdigest()[:20]
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=7)

    db.execute(text("""
        INSERT INTO invites
            (id, org_id, code, email, role, created_by, created_at, expires_at,
             invite_type, target_org_name)
        VALUES
            (:id, NULL, :code, :email, :role, :created_by, :now, :expires,
             'NEW_CUSTOMER', :org_name)
    """), {
        "id":         invite_id,
        "code":       invite_code,
        "email":      email,
        "role":       ROLE_ADMIN,
        "created_by": _safe_user_fk(db, user["id"]),
        "now":        now,
        "expires":    expires,
        "org_name":   org_name,
    })

    _audit(
        db, actor=user["id"], action="NEW_CUSTOMER_INVITED",
        target_id=invite_id,
        details={"email": email, "org_name": org_name, "full_name": full_name},
    )
    db.commit()

    from configs.settings import FRONTEND_BASE_URL
    invite_url = f"{FRONTEND_BASE_URL}/signup/{invite_code}"

    return {
        "invite_id":   invite_id,
        "invite_code": invite_code,
        "invite_url":  invite_url,
        "email":       email,
        "org_name":    org_name,
        "expires_at":  expires.isoformat(),
    }


# ── Lookup invite (public) ──────────────────────────────────────────────

@router.get("/{invite_code}")
def get_invite(invite_code: str, db: Session = Depends(get_db)):
    row = db.execute(text("""
        SELECT id, email, target_org_name, expires_at, used_at
        FROM invites
        WHERE code = :code AND invite_type = 'NEW_CUSTOMER'
    """), {"code": invite_code}).fetchone()
    if not row:
        raise HTTPException(404, "Invite not found")

    now = datetime.now(timezone.utc)
    expired = row.expires_at <= now if row.expires_at else False
    redeemed = row.used_at is not None

    return {
        "org_name":         row.target_org_name,
        "email":            row.email,
        "expires_at":       row.expires_at.isoformat() if row.expires_at else None,
        "already_redeemed": redeemed,
        "expired":          expired,
    }


# ── Redeem invite (public — issues JWT) ─────────────────────────────────

@router.post("/{invite_code}/redeem")
def redeem_invite(
    invite_code: str,
    body: RedeemRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    inv = db.execute(text("""
        SELECT id, email, target_org_name, expires_at, used_at, role
        FROM invites
        WHERE code = :code AND invite_type = 'NEW_CUSTOMER'
    """), {"code": invite_code}).fetchone()

    if not inv:
        raise HTTPException(404, "Invite not found")
    if inv.used_at is not None:
        raise HTTPException(400, "This invite has already been used")
    now = datetime.now(timezone.utc)
    if inv.expires_at and inv.expires_at <= now:
        raise HTTPException(400, "This invite has expired")

    password = body.password
    full_name = body.full_name.strip()
    if len(password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    if len(full_name) < 2:
        raise HTTPException(400, "Name must be at least 2 characters")

    existing = db.execute(
        text("SELECT 1 FROM users WHERE LOWER(email) = :e"),
        {"e": inv.email.lower()},
    ).fetchone()
    if existing:
        raise HTTPException(409, "A user with this email already exists")

    # ── Create org ────────────────────────────────────────────────────────
    org_id = hashlib.sha256(
        f"{inv.target_org_name}:{secrets.token_hex(8)}".encode()
    ).hexdigest()[:20]

    db.execute(text("""
        INSERT INTO organizations (id, name, created_at)
        VALUES (:id, :name, :now)
    """), {"id": org_id, "name": inv.target_org_name, "now": now})

    # ── Create user ───────────────────────────────────────────────────────
    import uuid
    user_id = f"USR-{uuid.uuid4().hex[:12].upper()}"
    hashed = hash_password(password)
    role = (inv.role or ROLE_ADMIN).upper()

    db.execute(text("""
        INSERT INTO users
            (id, email, org_id, full_name, hashed_password,
             is_admin, role, onboarding_complete, created_at)
        VALUES
            (:id, :email, :org_id, :name, :pw,
             :is_admin, :role, FALSE, :now)
    """), {
        "id":       user_id,
        "email":    inv.email,
        "org_id":   org_id,
        "name":     full_name,
        "pw":       hashed,
        "is_admin": role in (ROLE_ADMIN, ROLE_SUPERADMIN),
        "role":     role,
        "now":      now,
    })

    # ── Mark invite redeemed ──────────────────────────────────────────────
    db.execute(text("""
        UPDATE invites
        SET used_at = :now, used_by = :uid, org_id = :oid
        WHERE id = :id
    """), {"now": now, "uid": user_id, "id": inv.id, "oid": org_id})

    _audit(
        db, actor=user_id, action="NEW_CUSTOMER_ONBOARDED",
        target_id=inv.id,
        details={"org_id": org_id, "user_id": user_id, "org_name": inv.target_org_name},
    )
    db.commit()

    # ── Issue JWT (same shape as login) ──────────────────────────────────
    token_data = {"sub": user_id, "org_id": org_id, "role": role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(user_id)

    return {
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "token_type":    "bearer",
        "user": {
            "id":                  user_id,
            "email":               inv.email,
            "full_name":           full_name,
            "org_id":              org_id,
            "role":                role,
            "is_admin":            True,
            "onboarding_complete": False,
        },
        "org": {
            "id":   org_id,
            "name": inv.target_org_name,
        },
    }
