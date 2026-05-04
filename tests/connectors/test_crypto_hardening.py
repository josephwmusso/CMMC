"""Tests for the production fail-closed gate on src/connectors/crypto.py.

The gate raises RuntimeError at module import time when RENDER is set and
CONNECTOR_ENCRYPTION_KEY is unset. Tests vary env vars and reload the
module to exercise both code paths.
"""

from __future__ import annotations

import importlib
import sys

import pytest

from cryptography.fernet import Fernet


def _reload_crypto(monkeypatch, *, render: bool, key: str | None):
    """Reload src.connectors.crypto with specific env conditions.

    Patches both the OS env var and configs.settings.CONNECTOR_ENCRYPTION_KEY
    (which the module reads at import time), then reloads the module.
    """
    if render:
        monkeypatch.setenv("RENDER", "true")
    else:
        monkeypatch.delenv("RENDER", raising=False)

    if key is not None:
        monkeypatch.setenv("CONNECTOR_ENCRYPTION_KEY", key)
    else:
        monkeypatch.delenv("CONNECTOR_ENCRYPTION_KEY", raising=False)

    # crypto reads from configs.settings, which reads from env at its own
    # import time. Patch the cached attribute directly.
    from configs import settings
    monkeypatch.setattr(settings, "CONNECTOR_ENCRYPTION_KEY", key or "")

    # Drop the cached module so the import-time check re-runs.
    sys.modules.pop("src.connectors.crypto", None)
    return importlib.import_module("src.connectors.crypto")


def test_dev_mode_no_key_succeeds(monkeypatch):
    """Dev (no RENDER) without key: import succeeds, falls back to dev: prefix."""
    crypto = _reload_crypto(monkeypatch, render=False, key=None)
    token = crypto.encrypt_credentials({"a": 1})
    assert token.startswith(crypto.DEV_PREFIX)


def test_production_no_key_raises(monkeypatch):
    """Production (RENDER set) without key: import raises RuntimeError."""
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("CONNECTOR_ENCRYPTION_KEY", raising=False)
    from configs import settings
    monkeypatch.setattr(settings, "CONNECTOR_ENCRYPTION_KEY", "")

    sys.modules.pop("src.connectors.crypto", None)
    with pytest.raises(RuntimeError, match="CONNECTOR_ENCRYPTION_KEY"):
        importlib.import_module("src.connectors.crypto")


def test_dev_roundtrip(monkeypatch):
    """Dev mode round-trip: encrypt → decrypt yields the original dict."""
    crypto = _reload_crypto(monkeypatch, render=False, key=None)
    creds = {"client_id": "abc", "secret": "xyz", "tenant": "t1"}
    token = crypto.encrypt_credentials(creds)
    assert crypto.decrypt_credentials(token) == creds


def test_production_roundtrip(monkeypatch):
    """Production mode with a real Fernet key: round-trip yields the original."""
    key = Fernet.generate_key().decode()
    crypto = _reload_crypto(monkeypatch, render=True, key=key)
    creds = {"client_id": "abc", "secret": "xyz", "tenant": "t1"}
    token = crypto.encrypt_credentials(creds)
    assert token.startswith(crypto.ENC_PREFIX)
    assert crypto.decrypt_credentials(token) == creds


def test_prefix_used_correctly(monkeypatch):
    """enc: prefix in production with key, dev: prefix in dev without key."""
    key = Fernet.generate_key().decode()

    crypto = _reload_crypto(monkeypatch, render=True, key=key)
    assert crypto.encrypt_credentials({"x": 1}).startswith(crypto.ENC_PREFIX)

    crypto = _reload_crypto(monkeypatch, render=False, key=None)
    assert crypto.encrypt_credentials({"x": 1}).startswith(crypto.DEV_PREFIX)


# ──────────────────────────────────────────────────────────────────────
# Restore the module to its default (dev-mode-no-key) state for downstream
# tests in the same pytest session. Without this fixture, a test that ran
# in production mode could leave a stale _FERNET cached.

@pytest.fixture(autouse=True, scope="module")
def _restore_dev_mode():
    yield
    # After this test module's tests run, force a reload back to dev mode
    # so other test modules see the default state.
    sys.modules.pop("src.connectors.crypto", None)
    importlib.import_module("src.connectors.crypto")
