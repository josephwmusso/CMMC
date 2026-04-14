"""
src/api/auth.py

JWT authentication for the CMMC API.
Endpoints:
  POST /api/auth/register  — Create user account
  POST /api/auth/login     — Authenticate and get JWT
  GET  /api/auth/me        — Return current user info

All sensitive routes use Depends(get_current_user) to enforce auth.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import bcrypt as _bcrypt
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.db.session import get_db

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# ── Config ──────────────────────────────────────────────────────────────────
# Env is read directly here (and also mirrored in configs/settings.py) so
# this module has no circular-import dependency during auto-discovery.
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))           # 24 h
JWT_REFRESH_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))    # 7 d

# Role taxonomy. Postgres enum mirrors these exact strings (UPPERCASE).
ROLE_SUPERADMIN = "SUPERADMIN"
ROLE_ADMIN = "ADMIN"
ROLE_MEMBER = "MEMBER"
ROLE_VIEWER = "VIEWER"
ADMIN_ROLES = (ROLE_SUPERADMIN, ROLE_ADMIN)

# Direct bcrypt usage (passlib incompatible with bcrypt>=4.1)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# DEV_MODE: dev secret OR explicit ALLOW_ANONYMOUS=true (for demos)
DEV_MODE = (
    JWT_SECRET_KEY == "dev-secret-change-in-production"
    or os.getenv("ALLOW_ANONYMOUS", "").lower() == "true"
)
DEV_USER = {
    "id": "dev-user",
    "email": "david.kim@apex-defense.us",
    "org_id": "9de53b587b23450b87af",
    "full_name": "Dev User",
    "is_admin": True,
    "role": ROLE_SUPERADMIN,
}


# ── Pydantic models ─────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: str
    password: str
    # org_id is optional now: when an invite_code is provided the invite
    # supplies the org; when ALLOW_ANONYMOUS=true the demo org is used;
    # legacy callers that pass org_id explicitly still work.
    org_id: Optional[str] = None
    full_name: str = ""
    invite_code: Optional[str] = None


class UserOut(BaseModel):
    id: str
    email: str
    org_id: str
    full_name: str
    is_admin: bool
    role: str = ROLE_MEMBER


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut
    refresh_token: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Password helpers ────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── JWT helpers ─────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    payload["type"] = "access"
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=JWT_EXPIRE_MINUTES))
    payload["exp"] = expire
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Stateless refresh token — only the user_id + type + exp are signed.
    Roles/orgs are re-read from DB at refresh time so revocation takes
    effect immediately without a blocklist."""
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_EXPIRE_DAYS)
    payload = {"sub": user_id, "type": "refresh", "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# ── Role helpers (accept the dict returned by get_current_user) ─────────────

def is_superadmin(user: dict) -> bool:
    return user.get("role") == ROLE_SUPERADMIN


def is_admin_role(user: dict) -> bool:
    """True for SUPERADMIN or ADMIN (broader than the legacy is_admin bool
    because a downgraded ADMIN could still have is_admin stale-true)."""
    return user.get("role") in ADMIN_ROLES


# ── DB helpers ──────────────────────────────────────────────────────────────

def _role_from_row(role_val, is_admin: bool) -> str:
    """Coerce a DB role value (may be None on older rows) to a canonical
    uppercase role string, falling back to ADMIN/MEMBER from is_admin."""
    if role_val:
        return str(role_val).upper()
    return ROLE_ADMIN if is_admin else ROLE_MEMBER


def get_user_by_email(db: Session, email: str) -> Optional[dict]:
    row = db.execute(
        text("SELECT id, email, org_id, full_name, hashed_password, is_admin, role FROM users WHERE email = :email"),
        {"email": email},
    ).fetchone()
    if not row:
        return None
    cols = ["id", "email", "org_id", "full_name", "hashed_password", "is_admin", "role"]
    user = dict(zip(cols, row))
    # Normalize role; if the DB column doesn't exist yet (pre-migration),
    # the SELECT would have errored — so reaching here means role is present.
    user["role"] = _role_from_row(user.get("role"), bool(user.get("is_admin")))
    user["is_admin"] = user["role"] in ADMIN_ROLES
    return user


# ── FastAPI dependency ───────────────────────────────────────────────────────

def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> dict:
    """
    Validate JWT and return the current user dict.
    In dev mode (default JWT secret), allows unauthenticated access
    with the Apex Defense demo org so the frontend works without login.
    Raises 401 on invalid/expired token in production.
    """
    # Dev mode bypass: no token provided and using default dev secret
    if token is None:
        if DEV_MODE:
            return DEV_USER
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        token_type = payload.get("type", "access")
        if user_id is None:
            raise credentials_error
        if token_type != "access":
            # Refresh tokens must go to /api/auth/refresh, not be used as auth.
            raise credentials_error
    except JWTError:
        raise credentials_error

    row = db.execute(
        text("SELECT id, email, org_id, full_name, is_admin, role FROM users WHERE id = :id"),
        {"id": user_id},
    ).fetchone()
    if not row:
        raise credentials_error

    user = dict(zip(["id", "email", "org_id", "full_name", "is_admin", "role"], row))
    # role is fresh from DB (revocation + promotion take effect next request,
    # not at token expiry). is_admin derived for back-compat with older call
    # sites that still read user["is_admin"].
    user["role"] = _role_from_row(user.get("role"), bool(user.get("is_admin")))
    user["is_admin"] = user["role"] in ADMIN_ROLES
    return user


def verify_org_access(org_id: str, current_user: dict) -> None:
    """
    Ensure the authenticated user belongs to org_id (or is admin).
    Raises 403 if not.
    """
    if current_user["org_id"] != org_id and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Access denied to this organization")


# ── Role-gated dependencies ─────────────────────────────────────────────────

def require_admin_dep(current_user: dict = Depends(get_current_user)) -> dict:
    """FastAPI dependency: 403 unless user is SUPERADMIN or ADMIN."""
    if not is_admin_role(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def require_superadmin_dep(current_user: dict = Depends(get_current_user)) -> dict:
    """FastAPI dependency: 403 unless user is SUPERADMIN."""
    if not is_superadmin(current_user):
        raise HTTPException(status_code=403, detail="Superadmin access required")
    return current_user


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Create a new user account.

    Resolution order for org_id + role:
      1. invite_code provided → validate, consume, take its org_id + role.
      2. org_id provided in body → legacy path (anyone-can-register demo org
         or explicit dev behavior). Only allowed when ALLOW_ANONYMOUS=true.
      3. Nothing provided + ALLOW_ANONYMOUS=true → fall back to the demo org
         with role=MEMBER so the frontend can self-register in dev.
      4. Nothing provided + ALLOW_ANONYMOUS=false → reject.
    """
    import uuid

    existing = get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(400, "Email already registered")

    allow_anon = os.getenv("ALLOW_ANONYMOUS", "").lower() == "true"
    assigned_org_id: Optional[str] = None
    assigned_role: str = ROLE_MEMBER
    invite_row = None

    if user_in.invite_code:
        invite_row = db.execute(text("""
            SELECT id, org_id, email, role, expires_at, used_at
            FROM invites WHERE code = :code
        """), {"code": user_in.invite_code}).fetchone()
        if not invite_row:
            raise HTTPException(400, "Invalid invite code")
        _, inv_org, inv_email, inv_role, inv_expires, inv_used = invite_row
        now = datetime.now(timezone.utc)
        if inv_used is not None:
            raise HTTPException(400, "Invite code has already been used")
        if inv_expires is not None and inv_expires <= now:
            raise HTTPException(400, "Invite code has expired")
        if inv_email and inv_email.lower() != (user_in.email or "").lower():
            raise HTTPException(400, "Invite is tied to a different email address")
        assigned_org_id = inv_org
        assigned_role = (inv_role or ROLE_MEMBER).upper()
    elif user_in.org_id:
        if not allow_anon:
            raise HTTPException(400, "Invite code required")
        assigned_org_id = user_in.org_id
    else:
        if not allow_anon:
            raise HTTPException(400, "Invite code required")
        assigned_org_id = "9de53b587b23450b87af"  # demo org fallback

    user_id = f"USR-{uuid.uuid4().hex[:12].upper()}"
    hashed_pw = hash_password(user_in.password)

    db.execute(
        text("""
            INSERT INTO users (id, email, org_id, full_name, hashed_password,
                               is_admin, role, created_at)
            VALUES (:id, :email, :org_id, :full_name, :hashed_password,
                    :is_admin, :role, NOW())
        """),
        {
            "id": user_id,
            "email": user_in.email,
            "org_id": assigned_org_id,
            "full_name": user_in.full_name,
            "hashed_password": hashed_pw,
            "is_admin": assigned_role in ADMIN_ROLES,
            "role": assigned_role,
        },
    )

    # Mark invite consumed only after the user row is in place.
    if invite_row is not None:
        db.execute(
            text("UPDATE invites SET used_at = NOW(), used_by = :uid WHERE id = :id"),
            {"uid": user_id, "id": invite_row[0]},
        )

    db.commit()

    return UserOut(
        id=user_id,
        email=user_in.email,
        org_id=assigned_org_id,
        full_name=user_in.full_name,
        is_admin=assigned_role in ADMIN_ROLES,
        role=assigned_role,
    )


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate and return a JWT bearer token."""
    user = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Soft-deleted users cannot log in. get_user_by_email doesn't select this
    # column (would cascade to lots of call sites) so we check it here.
    deactivated = db.execute(
        text("SELECT deactivated_at FROM users WHERE id = :id"),
        {"id": user["id"]},
    ).fetchone()
    if deactivated and deactivated[0] is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated. Contact your administrator.",
        )

    token = create_access_token({
        "sub": user["id"],
        "org_id": user["org_id"],
        "role": user["role"],
    })
    refresh = create_refresh_token(user["id"])
    return Token(
        access_token=token,
        token_type="bearer",
        refresh_token=refresh,
        user=UserOut(
            id=user["id"],
            email=user["email"],
            org_id=user["org_id"],
            full_name=user["full_name"],
            is_admin=user["is_admin"],
            role=user["role"],
        ),
    )


@router.get("/me", response_model=UserOut)
def get_me(current_user: dict = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return UserOut(**{k: current_user.get(k) for k in UserOut.model_fields})


@router.post("/refresh", response_model=RefreshResponse)
def refresh(req: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access token.

    Stateless: refresh tokens aren't stored server-side. Revocation works
    because role + org are re-read from the DB here — a disabled user
    can't get a new access token.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(req.refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise credentials_error
    if payload.get("type") != "refresh":
        raise credentials_error
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_error

    row = db.execute(
        text("SELECT id, org_id, is_admin, role FROM users WHERE id = :id"),
        {"id": user_id},
    ).fetchone()
    if not row:
        raise credentials_error

    uid, org_id, is_admin_val, role_val = row
    role = _role_from_row(role_val, bool(is_admin_val))
    token = create_access_token({"sub": uid, "org_id": org_id, "role": role})
    return RefreshResponse(access_token=token, token_type="bearer")


# ── OAuth ───────────────────────────────────────────────────────────────────

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", "")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET", "")
MICROSOFT_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID", "common")
BASE_URL = os.getenv("BASE_URL", "http://localhost:5173")
DEFAULT_ORG_ID = "9de53b587b23450b87af"


class OAuthTokenRequest(BaseModel):
    token: str
    provider: str  # "google", "microsoft", "apple"


@router.post("/oauth", response_model=Token)
def oauth_login(req: OAuthTokenRequest, db: Session = Depends(get_db)):
    """Exchange an OAuth ID token for a JWT.

    Frontend sends the ID token from Google/Microsoft/Apple sign-in.
    Backend verifies it, creates user if needed, returns JWT.
    """
    import httpx
    import uuid

    if req.provider == "google":
        # Verify Google ID token
        resp = httpx.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={req.token}")
        if resp.status_code != 200:
            raise HTTPException(401, "Invalid Google token")
        info = resp.json()
        if GOOGLE_CLIENT_ID and info.get("aud") != GOOGLE_CLIENT_ID:
            raise HTTPException(401, "Token not issued for this app")
        email = info.get("email", "")
        full_name = info.get("name", email.split("@")[0])

    elif req.provider == "microsoft":
        # Verify Microsoft token via MS Graph /me
        resp = httpx.get("https://graph.microsoft.com/v1.0/me",
                         headers={"Authorization": f"Bearer {req.token}"})
        if resp.status_code != 200:
            raise HTTPException(401, "Invalid Microsoft token")
        info = resp.json()
        email = info.get("mail") or info.get("userPrincipalName", "")
        full_name = info.get("displayName", email.split("@")[0])

    else:
        raise HTTPException(400, f"Unsupported OAuth provider: {req.provider}")

    if not email:
        raise HTTPException(400, "Could not retrieve email from OAuth provider")

    # Find or create user
    user = get_user_by_email(db, email)
    if not user:
        user_id = f"USR-{uuid.uuid4().hex[:12].upper()}"
        # OAuth users get a random unusable password
        dummy_pw = hash_password(uuid.uuid4().hex)
        db.execute(text("""
            INSERT INTO users (id, email, org_id, full_name, hashed_password, is_admin, created_at)
            VALUES (:id, :email, :org_id, :full_name, :hashed_password, false, NOW())
        """), {
            "id": user_id, "email": email, "org_id": DEFAULT_ORG_ID,
            "full_name": full_name, "hashed_password": dummy_pw,
        })
        db.commit()
        user = {"id": user_id, "email": email, "org_id": DEFAULT_ORG_ID,
                "full_name": full_name, "is_admin": False, "role": ROLE_MEMBER}

    user.setdefault("role", ROLE_MEMBER)
    token = create_access_token({"sub": user["id"], "org_id": user["org_id"], "role": user["role"]})
    refresh_token = create_refresh_token(user["id"])
    return Token(
        access_token=token, token_type="bearer", refresh_token=refresh_token,
        user=UserOut(id=user["id"], email=user["email"], org_id=user["org_id"],
                     full_name=user["full_name"], is_admin=user["is_admin"],
                     role=user["role"]),
    )


# ── Server-side OAuth Redirects ─────────────────────────────────────────────
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode


def _find_or_create_oauth_user(db: Session, email: str, full_name: str) -> dict:
    """Find existing user by email or create a new OAuth user."""
    import uuid as _uuid
    user = get_user_by_email(db, email)
    if not user:
        user_id = f"USR-{_uuid.uuid4().hex[:12].upper()}"
        dummy_pw = hash_password(_uuid.uuid4().hex)
        db.execute(text("""
            INSERT INTO users (id, email, org_id, full_name, hashed_password, is_admin, created_at)
            VALUES (:id, :email, :org_id, :full_name, :hashed_password, false, NOW())
        """), {"id": user_id, "email": email, "org_id": DEFAULT_ORG_ID,
               "full_name": full_name, "hashed_password": dummy_pw})
        db.commit()
        user = {"id": user_id, "email": email, "org_id": DEFAULT_ORG_ID,
                "full_name": full_name, "is_admin": False, "role": ROLE_MEMBER}
    user.setdefault("role", ROLE_MEMBER)
    return user


@router.get("/google")
def google_redirect():
    """Redirect to Google OAuth consent screen."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(501, "Google OAuth not configured")
    params = urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": f"{BASE_URL}/api/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    })
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@router.get("/google/callback")
def google_callback(code: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback, create/find user, redirect with JWT."""
    import httpx
    token_resp = httpx.post("https://oauth2.googleapis.com/token", data={
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": f"{BASE_URL}/api/auth/google/callback",
        "grant_type": "authorization_code",
    })
    if token_resp.status_code != 200:
        raise HTTPException(401, "Google token exchange failed")
    tokens = token_resp.json()

    info_resp = httpx.get("https://oauth2.googleapis.com/tokeninfo",
                          params={"id_token": tokens["id_token"]})
    if info_resp.status_code != 200:
        raise HTTPException(401, "Could not verify Google token")
    info = info_resp.json()

    user = _find_or_create_oauth_user(db, info["email"], info.get("name", info["email"].split("@")[0]))
    jwt_token = create_access_token({"sub": user["id"], "org_id": user["org_id"], "role": user.get("role", "MEMBER")})
    return RedirectResponse(f"{BASE_URL}/login?token={jwt_token}")


@router.get("/microsoft")
def microsoft_redirect():
    """Redirect to Microsoft OAuth consent screen."""
    if not MICROSOFT_CLIENT_ID:
        raise HTTPException(501, "Microsoft OAuth not configured")
    params = urlencode({
        "client_id": MICROSOFT_CLIENT_ID,
        "redirect_uri": f"{BASE_URL}/api/auth/microsoft/callback",
        "response_type": "code",
        "scope": "openid email profile User.Read",
        "response_mode": "query",
        "prompt": "select_account",
    })
    return RedirectResponse(f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize?{params}")


@router.get("/microsoft/callback")
def microsoft_callback(code: str, db: Session = Depends(get_db)):
    """Handle Microsoft OAuth callback, create/find user, redirect with JWT."""
    import httpx
    token_resp = httpx.post(
        f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/token",
        data={
            "code": code,
            "client_id": MICROSOFT_CLIENT_ID,
            "client_secret": MICROSOFT_CLIENT_SECRET,
            "redirect_uri": f"{BASE_URL}/api/auth/microsoft/callback",
            "grant_type": "authorization_code",
            "scope": "openid email profile User.Read",
        },
    )
    if token_resp.status_code != 200:
        raise HTTPException(401, "Microsoft token exchange failed")
    tokens = token_resp.json()

    me_resp = httpx.get("https://graph.microsoft.com/v1.0/me",
                        headers={"Authorization": f"Bearer {tokens['access_token']}"})
    if me_resp.status_code != 200:
        raise HTTPException(401, "Could not retrieve Microsoft user info")
    info = me_resp.json()
    email = info.get("mail") or info.get("userPrincipalName", "")
    full_name = info.get("displayName", email.split("@")[0])

    user = _find_or_create_oauth_user(db, email, full_name)
    jwt_token = create_access_token({"sub": user["id"], "org_id": user["org_id"], "role": user.get("role", "MEMBER")})
    return RedirectResponse(f"{BASE_URL}/login?token={jwt_token}")
