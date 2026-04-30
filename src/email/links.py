"""Invite link builders.

Two formats because the frontend has two distinct signup flows:
  - Existing-user invite → /register?invite={code}
    User joins an org that already exists. Inviter is an admin in that org.
  - New-customer invite → /signup/{code}
    User creates a fresh org. Inviter is a SUPERADMIN provisioning a new tenant.

Both helpers default to FRONTEND_BASE_URL so dev/staging/prod each get
their own absolute URL based on env.
"""
from __future__ import annotations

from typing import Optional


def build_user_invite_link(code: str, base_url: Optional[str] = None) -> str:
    """Link for the existing-org user invite flow."""
    from configs.settings import FRONTEND_BASE_URL
    base = (base_url or FRONTEND_BASE_URL).rstrip("/")
    return f"{base}/register?invite={code}"


def build_new_customer_invite_link(code: str, base_url: Optional[str] = None) -> str:
    """Link for the new-customer invite flow (creates a fresh org)."""
    from configs.settings import FRONTEND_BASE_URL
    base = (base_url or FRONTEND_BASE_URL).rstrip("/")
    return f"{base}/signup/{code}"
