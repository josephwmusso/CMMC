"""Fernet-based credential encryption with a dev-mode fallback."""

from __future__ import annotations

import base64
import json
import logging

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

DEV_PREFIX = "dev:"
ENC_PREFIX = "enc:"


def _get_key() -> str:
    """Read the key fresh on every call so test env mutations are seen."""
    from configs import settings  # late import to allow test patching
    return settings.CONNECTOR_ENCRYPTION_KEY or ""


def _fernet() -> Fernet | None:
    key = _get_key()
    if not key:
        return None
    return Fernet(key.encode())


def encrypt_credentials(creds: dict) -> str:
    """Encrypt a credentials dict for storage. Returns a string with mode prefix."""
    payload = json.dumps(creds, sort_keys=True).encode("utf-8")
    f = _fernet()
    if f is None:
        logger.warning(
            "CONNECTOR_ENCRYPTION_KEY not set — credentials stored as base64 plaintext "
            "(dev/test only). Set the env var before any production traffic."
        )
        return DEV_PREFIX + base64.b64encode(payload).decode("ascii")
    return ENC_PREFIX + f.encrypt(payload).decode("ascii")


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
        f = _fernet()
        if f is None:
            raise ValueError(
                "Encrypted token present but CONNECTOR_ENCRYPTION_KEY is not set."
            )
        try:
            payload = f.decrypt(token[len(ENC_PREFIX):].encode("ascii"))
        except InvalidToken as e:
            raise ValueError("Invalid encryption token (wrong key or corrupted)") from e
        return json.loads(payload.decode("utf-8"))
    raise ValueError("Unrecognized credentials token format (no dev: or enc: prefix)")
