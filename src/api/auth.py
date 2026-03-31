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
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.db.session import get_db

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# ── Config ──────────────────────────────────────────────────────────────────
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

DEV_MODE = JWT_SECRET_KEY == "dev-secret-change-in-production"
DEV_USER = {
    "id": "dev-user",
    "email": "david.kim@apex-defense.us",
    "org_id": "9de53b587b23450b87af",
    "full_name": "Dev User",
    "is_admin": True,
}


# ── Pydantic models ─────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: str
    password: str
    org_id: str
    full_name: str = ""


class UserOut(BaseModel):
    id: str
    email: str
    org_id: str
    full_name: str
    is_admin: bool


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


# ── Password helpers ────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT helpers ─────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=JWT_EXPIRE_MINUTES))
    payload["exp"] = expire
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# ── DB helpers ──────────────────────────────────────────────────────────────

def get_user_by_email(db: Session, email: str) -> Optional[dict]:
    row = db.execute(
        text("SELECT id, email, org_id, full_name, hashed_password, is_admin FROM users WHERE email = :email"),
        {"email": email},
    ).fetchone()
    if not row:
        return None
    return dict(zip(["id", "email", "org_id", "full_name", "hashed_password", "is_admin"], row))


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
        org_id: str = payload.get("org_id")
        if user_id is None:
            raise credentials_error
    except JWTError:
        raise credentials_error

    row = db.execute(
        text("SELECT id, email, org_id, full_name, is_admin FROM users WHERE id = :id"),
        {"id": user_id},
    ).fetchone()
    if not row:
        raise credentials_error

    return dict(zip(["id", "email", "org_id", "full_name", "is_admin"], row))


def verify_org_access(org_id: str, current_user: dict) -> None:
    """
    Ensure the authenticated user belongs to org_id (or is admin).
    Raises 403 if not.
    """
    if current_user["org_id"] != org_id and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Access denied to this organization")


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Create a new user account."""
    existing = get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(400, "Email already registered")

    import uuid
    user_id = f"USR-{uuid.uuid4().hex[:12].upper()}"
    hashed_pw = hash_password(user_in.password)

    db.execute(
        text(
            """
            INSERT INTO users (id, email, org_id, full_name, hashed_password, is_admin, created_at)
            VALUES (:id, :email, :org_id, :full_name, :hashed_password, false, NOW())
            """
        ),
        {
            "id": user_id,
            "email": user_in.email,
            "org_id": user_in.org_id,
            "full_name": user_in.full_name,
            "hashed_password": hashed_pw,
        },
    )
    db.commit()

    return UserOut(
        id=user_id,
        email=user_in.email,
        org_id=user_in.org_id,
        full_name=user_in.full_name,
        is_admin=False,
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

    token = create_access_token({"sub": user["id"], "org_id": user["org_id"]})
    return Token(
        access_token=token,
        token_type="bearer",
        user=UserOut(
            id=user["id"],
            email=user["email"],
            org_id=user["org_id"],
            full_name=user["full_name"],
            is_admin=user["is_admin"],
        ),
    )


@router.get("/me", response_model=UserOut)
def get_me(current_user: dict = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return UserOut(**{k: current_user[k] for k in UserOut.model_fields})


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
                "full_name": full_name, "is_admin": False}

    token = create_access_token({"sub": user["id"], "org_id": user["org_id"]})
    return Token(
        access_token=token, token_type="bearer",
        user=UserOut(id=user["id"], email=user["email"], org_id=user["org_id"],
                     full_name=user["full_name"], is_admin=user["is_admin"]),
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
                "full_name": full_name, "is_admin": False}
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
    jwt_token = create_access_token({"sub": user["id"], "org_id": user["org_id"]})
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
    jwt_token = create_access_token({"sub": user["id"], "org_id": user["org_id"]})
    return RedirectResponse(f"{BASE_URL}/login?token={jwt_token}")
