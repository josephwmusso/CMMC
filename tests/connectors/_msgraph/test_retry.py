"""Tests for the get_with_retry HTTP retry helper.

Uses httpx.MockTransport to construct httpx.Client instances with
predictable response sequences. time.sleep is patched out so tests
run in milliseconds.
"""

from __future__ import annotations

from email.utils import format_datetime
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import httpx
import pytest

from src.connectors._msgraph.errors import (
    MsGraphPermissionError,
    MsGraphThrottledError,
)
from src.connectors._msgraph.retry import get_with_retry, _parse_retry_after


def _client(handler) -> httpx.Client:
    """Build an httpx.Client with a MockTransport invoking handler(request)."""
    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.fixture(autouse=True)
def _no_real_sleep():
    """Mock time.sleep so retries don't actually wait. Verify call counts via the mock."""
    with patch("src.connectors._msgraph.retry.time.sleep") as m:
        yield m


def test_200_first_try(_no_real_sleep):
    def handler(req):
        return httpx.Response(200, json={"value": []})
    with _client(handler) as c:
        resp = get_with_retry(c, "https://example/x", {})
    assert resp.status_code == 200
    _no_real_sleep.assert_not_called()


def test_429_numeric_retry_after_succeeds(_no_real_sleep):
    calls = {"n": 0}

    def handler(req):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "2"}, json={"error": {}})
        return httpx.Response(200, json={"ok": True})

    with _client(handler) as c:
        resp = get_with_retry(c, "https://example/x", {})
    assert resp.status_code == 200
    _no_real_sleep.assert_called_once()
    assert _no_real_sleep.call_args[0][0] == 2.0


def test_429_http_date_retry_after_parses(_no_real_sleep):
    """Retry-After in HTTP-date format is parsed via parsedate_to_datetime."""
    target = datetime.now(timezone.utc) + timedelta(seconds=3)
    http_date = format_datetime(target)

    calls = {"n": 0}

    def handler(req):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": http_date}, json={})
        return httpx.Response(200, json={"ok": True})

    with _client(handler) as c:
        resp = get_with_retry(c, "https://example/x", {})
    assert resp.status_code == 200
    # Slept for ~3 seconds (small drift acceptable).
    slept = _no_real_sleep.call_args[0][0]
    assert 0 < slept <= 5


def test_429_three_retries_exhausted_raises(_no_real_sleep):
    def handler(req):
        return httpx.Response(429, headers={"Retry-After": "1"}, json={})
    with _client(handler) as c:
        with pytest.raises(MsGraphThrottledError):
            get_with_retry(c, "https://example/x", {})
    # 3 sleeps (attempts 0, 1, 2 sleep; attempt 3 raises before sleep).
    assert _no_real_sleep.call_count == 3


def test_503_retries_then_succeeds(_no_real_sleep):
    calls = {"n": 0}

    def handler(req):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503, json={})
        return httpx.Response(200, json={"ok": True})

    with _client(handler) as c:
        resp = get_with_retry(c, "https://example/x", {})
    assert resp.status_code == 200
    assert _no_real_sleep.call_count == 1


def test_503_retries_exhausted_raises(_no_real_sleep):
    def handler(req):
        return httpx.Response(503, json={})
    with _client(handler) as c:
        with pytest.raises(httpx.HTTPStatusError):
            get_with_retry(c, "https://example/x", {})


def test_403_with_known_permission_in_body(_no_real_sleep):
    def handler(req):
        return httpx.Response(
            403,
            json={"error": {"message": "Insufficient privileges. AuditLog.Read.All required."}},
        )
    with _client(handler) as c:
        with pytest.raises(MsGraphPermissionError) as exc_info:
            get_with_retry(c, "https://example/auditLogs/signIns", {})
    assert exc_info.value.missing_permission == "AuditLog.Read.All"
    assert exc_info.value.endpoint == "https://example/auditLogs/signIns"


def test_403_generic_body(_no_real_sleep):
    def handler(req):
        return httpx.Response(403, json={"error": {"message": "Forbidden"}})
    with _client(handler) as c:
        with pytest.raises(MsGraphPermissionError) as exc_info:
            get_with_retry(c, "https://example/x", {})
    assert exc_info.value.missing_permission is None


def test_404_raises_immediately_no_retry(_no_real_sleep):
    def handler(req):
        return httpx.Response(404, json={})
    with _client(handler) as c:
        with pytest.raises(httpx.HTTPStatusError):
            get_with_retry(c, "https://example/x", {})
    _no_real_sleep.assert_not_called()


def test_connect_error_retries(_no_real_sleep):
    calls = {"n": 0}

    def handler(req):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise httpx.ConnectError("simulated connection failure")
        return httpx.Response(200, json={"ok": True})

    with _client(handler) as c:
        resp = get_with_retry(c, "https://example/x", {})
    assert resp.status_code == 200
    assert _no_real_sleep.call_count == 2


def test_connect_error_exhausted_reraises(_no_real_sleep):
    def handler(req):
        raise httpx.ConnectError("persistent connection failure")
    with _client(handler) as c:
        with pytest.raises(httpx.ConnectError):
            get_with_retry(c, "https://example/x", {})


def test_parse_retry_after_numeric():
    assert _parse_retry_after("5") == 5.0


def test_parse_retry_after_http_date():
    target = datetime.now(timezone.utc) + timedelta(seconds=10)
    parsed = _parse_retry_after(format_datetime(target))
    assert parsed is not None
    assert 0 < parsed <= 12


def test_parse_retry_after_none():
    assert _parse_retry_after(None) is None
    assert _parse_retry_after("garbage-not-a-date") is None


# ──────────────────────────────────────────────────────────────────────
# F.1 framework contract: licensing_signal on MsGraphPermissionError
# ──────────────────────────────────────────────────────────────────────

class TestLicensingSignal:
    """When the Graph 403 body's error.code matches a known unlicensed-tenant
    signal (e.g. Forbidden_LicensingError), the raised MsGraphPermissionError
    carries licensing_signal=True. Connector code can choose to convert these
    into a degraded PulledEvidence rather than raising.

    Initial detection set is narrow per Phase 2 design (one code:
    Forbidden_LicensingError). Future commits add codes one at a time as
    F.3a/F.3b live verification surfaces them.
    """

    def test_403_with_licensing_error_code_sets_signal(self):
        def handler(req):
            return httpx.Response(
                403,
                json={
                    "error": {
                        "code": "Forbidden_LicensingError",
                        "message": "Tenant requires Microsoft Intune license.",
                    }
                },
            )
        with _client(handler) as c:
            with pytest.raises(MsGraphPermissionError) as exc_info:
                get_with_retry(c, "https://example/x", {})
        assert exc_info.value.licensing_signal is True

    def test_403_with_generic_code_leaves_signal_false(self):
        def handler(req):
            return httpx.Response(
                403,
                json={"error": {"code": "Forbidden", "message": "Access denied."}},
            )
        with _client(handler) as c:
            with pytest.raises(MsGraphPermissionError) as exc_info:
                get_with_retry(c, "https://example/x", {})
        assert exc_info.value.licensing_signal is False

    def test_403_with_no_code_field_leaves_signal_false(self):
        def handler(req):
            return httpx.Response(
                403,
                json={"error": {"message": "denied"}},
            )
        with _client(handler) as c:
            with pytest.raises(MsGraphPermissionError) as exc_info:
                get_with_retry(c, "https://example/x", {})
        assert exc_info.value.licensing_signal is False

    def test_403_with_non_string_code_leaves_signal_false(self):
        # Defensive: Microsoft has occasionally returned numeric codes
        # in some endpoints. Don't crash if the field type is unexpected.
        def handler(req):
            return httpx.Response(
                403,
                json={"error": {"code": 12345, "message": "weird"}},
            )
        with _client(handler) as c:
            with pytest.raises(MsGraphPermissionError) as exc_info:
                get_with_retry(c, "https://example/x", {})
        assert exc_info.value.licensing_signal is False

    def test_403_with_no_error_object_leaves_signal_false(self):
        def handler(req):
            return httpx.Response(403, json={})
        with _client(handler) as c:
            with pytest.raises(MsGraphPermissionError) as exc_info:
                get_with_retry(c, "https://example/x", {})
        assert exc_info.value.licensing_signal is False

    def test_default_attribute_when_constructed_directly(self):
        """Backward compat: existing catch-and-inspect sites that construct
        MsGraphPermissionError without the new kwarg still work. The default
        value False applies."""
        e = MsGraphPermissionError("test", missing_permission="X.Y.Z")
        assert e.licensing_signal is False
        # Existing attributes preserved.
        assert e.missing_permission == "X.Y.Z"
        assert e.endpoint is None

    def test_explicit_signal_round_trip_when_constructed_directly(self):
        """Direct construction with licensing_signal=True works and round-trips."""
        e = MsGraphPermissionError(
            "test", missing_permission=None, endpoint="/x", licensing_signal=True
        )
        assert e.licensing_signal is True
