"""Fernet-based credential encryption with fail-closed production gate.

Behavior matrix:

    RENDER env var | CONNECTOR_ENCRYPTION_KEY | result
    ---------------+--------------------------+--------------------------
    set            | unset / empty            | RuntimeError at import
    set            | set                      | enc: prefix (Fernet)
    unset          | unset / empty            | dev: prefix (base64) + warning
    unset          | set                      | enc: prefix (Fernet)

The fail-closed gate prevents EntraIdConnector (Pass E.2) and any future
connector from storing customer credentials as base64-equivalent in
production. RENDER is auto-set by Render on every deploy; local dev,
tests, and CI do not set it.

Module-level cache: the encryption mode is decided once at import time.
Tests that need to vary env vars use importlib.reload(crypto).
"""

from __future__ import annotations

import base64
import json
import logging
import os

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

DEV_PREFIX = "dev:"
ENC_PREFIX = "enc:"


def _is_production() -> bool:
    """RENDER env var is auto-set on every Render deploy. The codebase
    already uses this signal in src/api/main.py and src/utils/service_check.py.
    """
    return bool(os.environ.get("RENDER"))


def _read_key() -> str:
    """Read encryption key from configs.settings (which reads from env)."""
    from configs import settings
    return (settings.CONNECTOR_ENCRYPTION_KEY or "").strip()


# ── Module import-time gate ──────────────────────────────────────────────

_IS_PRODUCTION = _is_production()
_KEY = _read_key()

if _IS_PRODUCTION and not _KEY:
    raise RuntimeError(
        "CONNECTOR_ENCRYPTION_KEY env var is required in production "
        "(RENDER environment detected). Refusing to start — connector "
        "credentials would otherwise be stored as base64 plaintext. "
        "Generate a key with: "
        'python -c "from cryptography.fernet import Fernet; '
        'print(Fernet.generate_key().decode())" '
        "and set as a Render environment variable."
    )

if not _KEY:
    logger.warning(
        "CONNECTOR_ENCRYPTION_KEY not set — credentials stored as base64 "
        "plaintext (dev/test only). Set the env var before any production "
        "traffic."
    )
    _FERNET: Fernet | None = None
else:
    _FERNET = Fernet(_KEY.encode())


# ── Public API ───────────────────────────────────────────────────────────


def encrypt_credentials(creds: dict) -> str:
    """Encrypt a credentials dict for storage. Returns a string with mode prefix."""
    payload = json.dumps(creds, sort_keys=True).encode("utf-8")
    if _FERNET is None:
        return DEV_PREFIX + base64.b64encode(payload).decode("ascii")
    return ENC_PREFIX + _FERNET.encrypt(payload).decode("ascii")


def decrypt_credentials(token: str) -> dict:
    """Reverse encrypt_credentials. Raises ValueError on malformed input."""
    if token.startswith(DEV_PREFIX):
        body = token[len(DEV_PREFIX):]
        try:
            payload = base64.b64decode(body.encode("ascii"))
        except Exception as e:
            raise ValueError(f"Invalid dev-mode credentials token: {e}") from e
        return json.loads(payload.decode("utf-8"))
    if token.startswith(ENC_PREFIX):
        if _FERNET is None:
            raise ValueError(
                "Encrypted token present but CONNECTOR_ENCRYPTION_KEY is not set."
            )
        try:
            payload = _FERNET.decrypt(token[len(ENC_PREFIX):].encode("ascii"))
        except InvalidToken as e:
            raise ValueError("Invalid encryption token (wrong key or corrupted)") from e
        return json.loads(payload.decode("utf-8"))
    raise ValueError("Unrecognized credentials token format (no dev: or enc: prefix)")
