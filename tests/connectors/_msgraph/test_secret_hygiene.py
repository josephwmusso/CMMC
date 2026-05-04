"""Strict secret-leak guard.

Constructs MsGraphClient with unique-marker credentials and asserts the
markers never appear in:
  - any log record (any level)
  - repr(client) / str(client)
  - repr(token_manager) / str(token_manager)
  - str(any caught exception)

If this test ever fails, a code change has introduced a credential leak.
Treat it as a hard regression — do not modify or relax this test without
explicit security review.
"""

from __future__ import annotations

import logging
from unittest.mock import patch, MagicMock

import httpx
import pytest

from src.connectors._msgraph.auth import TokenManager
from src.connectors._msgraph.client import MsGraphClient
from src.connectors._msgraph.endpoints import CloudEnvironment
from src.connectors._msgraph.errors import MsGraphAuthError


# Three unique markers — each must NEVER reach observable output.
MARKER_TENANT = "TEST_TENANT_SHOULD_NEVER_LEAK_zzz000"
MARKER_CLIENT = "TEST_CLIENT_SHOULD_NEVER_LEAK_zzz111"
MARKER_SECRET = "TEST_SECRET_SHOULD_NEVER_LEAK_zzz222"


@pytest.fixture(autouse=True)
def _patch_msal_for_hygiene():
    """Pass MSAL through but capture acquire_token_for_client calls. The
    important thing is that we don't try to actually authenticate against
    a real authority (the markers aren't valid credentials)."""
    with patch(
        "src.connectors._msgraph.auth.ConfidentialClientApplication"
    ) as cls:
        instance = MagicMock()
        cls.return_value = instance
        yield instance, cls


@pytest.fixture(autouse=True)
def _no_real_sleep():
    with patch("src.connectors._msgraph.retry.time.sleep"):
        yield


def _assert_no_marker_in(text: str, where: str) -> None:
    for marker, name in (
        (MARKER_TENANT, "tenant"),
        (MARKER_CLIENT, "client_id"),
        (MARKER_SECRET, "client_secret"),
    ):
        assert marker not in text, f"{name} marker leaked into {where}"


def test_repr_str_do_not_leak(_patch_msal_for_hygiene, _no_real_sleep):
    instance, _ = _patch_msal_for_hygiene
    instance.acquire_token_for_client.return_value = {"access_token": "FAKE"}

    tm = TokenManager(MARKER_TENANT, MARKER_CLIENT, MARKER_SECRET, CloudEnvironment.COMMERCIAL)
    _assert_no_marker_in(repr(tm), "TokenManager.__repr__")
    _assert_no_marker_in(str(tm), "TokenManager.__str__")

    client = MsGraphClient(
        tenant_id=MARKER_TENANT,
        client_id=MARKER_CLIENT,
        client_secret=MARKER_SECRET,
        cloud_env="commercial",
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})),
    )
    _assert_no_marker_in(repr(client), "MsGraphClient.__repr__")
    _assert_no_marker_in(str(client), "MsGraphClient.__str__")


def test_logs_do_not_leak_on_success(_patch_msal_for_hygiene, _no_real_sleep, caplog):
    """Successful path: token acquired, GET succeeds. Markers must not appear
    in any log output."""
    instance, _ = _patch_msal_for_hygiene
    instance.acquire_token_for_client.return_value = {"access_token": "FAKE"}

    def handler(req):
        return httpx.Response(200, json={"value": []})

    caplog.set_level(logging.DEBUG, logger="src.connectors._msgraph")

    with MsGraphClient(
        tenant_id=MARKER_TENANT,
        client_id=MARKER_CLIENT,
        client_secret=MARKER_SECRET,
        cloud_env="commercial",
        transport=httpx.MockTransport(handler),
    ) as client:
        list(client.paginate("/users"))

    full_log = "\n".join(rec.getMessage() for rec in caplog.records)
    _assert_no_marker_in(full_log, "log records (success path)")


def test_logs_do_not_leak_on_429_retry(_patch_msal_for_hygiene, _no_real_sleep, caplog):
    """Retry path: 429 then 200. Retry warning logs must not include credentials."""
    instance, _ = _patch_msal_for_hygiene
    instance.acquire_token_for_client.return_value = {"access_token": "FAKE"}

    state = {"n": 0}

    def handler(req):
        state["n"] += 1
        if state["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "1"}, json={})
        return httpx.Response(200, json={"value": []})

    caplog.set_level(logging.DEBUG, logger="src.connectors._msgraph")

    with MsGraphClient(
        tenant_id=MARKER_TENANT,
        client_id=MARKER_CLIENT,
        client_secret=MARKER_SECRET,
        cloud_env="commercial",
        transport=httpx.MockTransport(handler),
    ) as client:
        list(client.paginate("/users"))

    full_log = "\n".join(rec.getMessage() for rec in caplog.records)
    _assert_no_marker_in(full_log, "log records (429 retry path)")


def test_auth_error_message_does_not_leak(_patch_msal_for_hygiene, _no_real_sleep):
    """AADSTS error path: the raised MsGraphAuthError message must not echo
    credentials back to the caller."""
    instance, _ = _patch_msal_for_hygiene
    instance.acquire_token_for_client.return_value = {
        "error": "invalid_client",
        "error_description": "AADSTS7000222: secret expired (no markers in this body)",
    }

    tm = TokenManager(MARKER_TENANT, MARKER_CLIENT, MARKER_SECRET, CloudEnvironment.COMMERCIAL)
    with pytest.raises(MsGraphAuthError) as exc_info:
        tm.get_token()

    _assert_no_marker_in(str(exc_info.value), "MsGraphAuthError str")
    _assert_no_marker_in(repr(exc_info.value), "MsGraphAuthError repr")
