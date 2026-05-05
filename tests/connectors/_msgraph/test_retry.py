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
    MsGraphCapabilityError,
    MsGraphError,
    MsGraphPermissionError,
    MsGraphThrottledError,
)
from src.connectors._msgraph.retry import (
    _detect_capability_gap,
    _detect_service_unavailable_500,
    _parse_retry_after,
    get_with_retry,
)


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


# ──────────────────────────────────────────────────────────────────────
# F.3a framework amendment: capability-gap detection on HTTP 400
# ──────────────────────────────────────────────────────────────────────

class TestCapabilityGapDetection:
    """When a Graph endpoint returns 400 + BadRequest + a message
    indicating the service isn't available on the tenant, get_with_retry
    raises MsGraphCapabilityError instead of httpx.HTTPStatusError.

    Surfaced by F.3a live verification against the intranest-m365-test
    trial, where:
      - /admin/sharepoint/settings returns 400 BadRequest 'Tenant does not
        have a SPO license.'
      - /deviceManagement/deviceCompliancePolicies returns 400 BadRequest
        'Request not applicable to target tenant.'

    Distinct from the 403 + Forbidden_LicensingError path (licensing_signal
    on MsGraphPermissionError) — that path is unchanged.
    """

    def test_400_bad_request_spo_license_raises_capability(self, _no_real_sleep):
        def handler(req):
            return httpx.Response(
                400,
                json={
                    "error": {
                        "code": "BadRequest",
                        "message": "Tenant does not have a SPO license.",
                    }
                },
            )
        with _client(handler) as c:
            with pytest.raises(MsGraphCapabilityError) as exc_info:
                get_with_retry(c, "https://example/admin/sharepoint/settings", {})
        assert "SPO license" in str(exc_info.value)
        assert exc_info.value.endpoint == "https://example/admin/sharepoint/settings"

    def test_400_bad_request_not_applicable_raises_capability(self, _no_real_sleep):
        def handler(req):
            return httpx.Response(
                400,
                json={
                    "error": {
                        "code": "BadRequest",
                        "message": "Request not applicable to target tenant.",
                    }
                },
            )
        with _client(handler) as c:
            with pytest.raises(MsGraphCapabilityError) as exc_info:
                get_with_retry(
                    c,
                    "https://example/deviceManagement/deviceCompliancePolicies",
                    {},
                )
        assert "not applicable to target tenant" in str(exc_info.value).lower()

    def test_400_bad_request_generic_message_raises_http_status_not_capability(
        self, _no_real_sleep
    ):
        """A 400 with BadRequest code but no capability-fragment match must
        NOT be misclassified as a capability gap. Falls through to the
        existing httpx.HTTPStatusError path."""
        def handler(req):
            return httpx.Response(
                400,
                json={
                    "error": {
                        "code": "BadRequest",
                        "message": "Property 'displayName' is required.",
                    }
                },
            )
        with _client(handler) as c:
            with pytest.raises(httpx.HTTPStatusError):
                get_with_retry(c, "https://example/x", {})

    def test_400_with_non_bad_request_code_raises_http_status(self, _no_real_sleep):
        """A 400 with a different error.code (e.g. 'InvalidRequest') is not
        a capability gap — falls through to httpx.HTTPStatusError."""
        def handler(req):
            return httpx.Response(
                400,
                json={
                    "error": {
                        "code": "InvalidRequest",
                        "message": "Tenant does not have a SPO license.",
                    }
                },
            )
        with _client(handler) as c:
            with pytest.raises(httpx.HTTPStatusError):
                get_with_retry(c, "https://example/x", {})

    def test_400_with_malformed_body_no_error_key(self, _no_real_sleep):
        """Defensive: a 400 with no 'error' key in the body must not crash
        the detection helper. Falls through to httpx.HTTPStatusError."""
        def handler(req):
            return httpx.Response(400, json={"unexpected": "shape"})
        with _client(handler) as c:
            with pytest.raises(httpx.HTTPStatusError):
                get_with_retry(c, "https://example/x", {})

    def test_400_with_non_string_code(self, _no_real_sleep):
        """Defensive: error.code is a non-string (e.g. numeric)."""
        def handler(req):
            return httpx.Response(
                400,
                json={"error": {"code": 12345, "message": "does not have"}},
            )
        with _client(handler) as c:
            with pytest.raises(httpx.HTTPStatusError):
                get_with_retry(c, "https://example/x", {})

    def test_400_with_non_string_message(self, _no_real_sleep):
        """Defensive: error.message is a non-string."""
        def handler(req):
            return httpx.Response(
                400,
                json={"error": {"code": "BadRequest", "message": ["weird"]}},
            )
        with _client(handler) as c:
            with pytest.raises(httpx.HTTPStatusError):
                get_with_retry(c, "https://example/x", {})

    def test_400_non_json_body_falls_through(self, _no_real_sleep):
        """Defensive: a 400 whose body isn't JSON at all must not crash."""
        def handler(req):
            return httpx.Response(400, content=b"<html>not json</html>")
        with _client(handler) as c:
            with pytest.raises(httpx.HTTPStatusError):
                get_with_retry(c, "https://example/x", {})

    def test_capability_message_match_is_case_insensitive(self, _no_real_sleep):
        def handler(req):
            return httpx.Response(
                400,
                json={
                    "error": {
                        "code": "BadRequest",
                        "message": "TENANT DOES NOT HAVE A SPO LICENSE.",
                    }
                },
            )
        with _client(handler) as c:
            with pytest.raises(MsGraphCapabilityError):
                get_with_retry(c, "https://example/x", {})

    # ----- _detect_capability_gap helper unit tests -----

    def test_detect_capability_gap_spo_license(self):
        body = {"error": {"code": "BadRequest", "message": "Tenant does not have a SPO license."}}
        assert _detect_capability_gap(body) is True

    def test_detect_capability_gap_not_applicable(self):
        body = {"error": {"code": "BadRequest", "message": "Request not applicable to target tenant."}}
        assert _detect_capability_gap(body) is True

    def test_detect_capability_gap_returns_false_on_empty_body(self):
        assert _detect_capability_gap({}) is False

    def test_detect_capability_gap_returns_false_on_non_bad_request_code(self):
        body = {"error": {"code": "Forbidden", "message": "does not have"}}
        assert _detect_capability_gap(body) is False

    def test_detect_capability_gap_returns_false_when_no_fragment_match(self):
        body = {"error": {"code": "BadRequest", "message": "Property is required."}}
        assert _detect_capability_gap(body) is False


class TestServiceUnavailable500Detection:
    """F.3b framework amendment: a Graph 500 + generalException + inner
    message indicating the underlying service rejected the token is
    treated as a capability gap (MsGraphCapabilityError raised
    immediately) rather than letting retry burn through the budget on
    an unrecoverable 500.

    The narrow two-condition AND signature prevents transient 500s from
    being silently reclassified as capability gaps — the load-bearing
    safety property exercised by the final test in this class.

    Surfaced by F.3b live verification against
    /beta/security/informationProtection/sensitivityLabels on the
    intranest-m365-test trial.
    """

    def test_500_general_exception_with_token_rejection_raises_capability(
        self, _no_real_sleep
    ):
        """The exact shape Microsoft returns for an unprovisioned Purview
        tenant on the InformationProtection beta endpoint."""
        def handler(req):
            return httpx.Response(
                500,
                json={
                    "error": {
                        "code": "generalException",
                        "message": "There was an internal server error while processing the request.",
                        "innerError": {
                            "message": "The service didn't accept the auth token. Challenge:['']",
                            "CorrelationId.Description": "PolicyProfile",
                        },
                    }
                },
            )
        with _client(handler) as c:
            with pytest.raises(MsGraphCapabilityError) as exc_info:
                get_with_retry(
                    c,
                    "https://example/beta/security/informationProtection/sensitivityLabels",
                    {},
                )
        assert "didn't accept the auth token" in str(exc_info.value).lower()
        assert exc_info.value.endpoint == (
            "https://example/beta/security/informationProtection/sensitivityLabels"
        )
        # Critical: the 500 path must NOT have burned the retry budget. A
        # capability-gap signal raises immediately on attempt 0.
        _no_real_sleep.assert_not_called()

    def test_500_alternative_message_variant(self, _no_real_sleep):
        """Defensive: 'did not accept' (no contraction) also matches."""
        def handler(req):
            return httpx.Response(
                500,
                json={
                    "error": {
                        "code": "generalException",
                        "message": "Internal error.",
                        "innerError": {
                            "message": "The service did not accept the auth token.",
                        },
                    }
                },
            )
        with _client(handler) as c:
            with pytest.raises(MsGraphCapabilityError):
                get_with_retry(c, "https://example/x", {})

    def test_500_case_insensitive_inner_message_match(self, _no_real_sleep):
        def handler(req):
            return httpx.Response(
                500,
                json={
                    "error": {
                        "code": "generalException",
                        "message": "Internal error.",
                        "innerError": {
                            "message": "The Service Didn't Accept The Auth Token.",
                        },
                    }
                },
            )
        with _client(handler) as c:
            with pytest.raises(MsGraphCapabilityError):
                get_with_retry(c, "https://example/x", {})

    # ───── Defensive cases: must NOT silently turn 500s into capability gaps ─────

    def test_500_with_no_error_key_falls_through_to_retry(self, _no_real_sleep):
        """Defensive: a 500 with no 'error' key in the body must not crash
        the detector AND must fall through to the existing 5xx retry
        behavior (eventually raising httpx.HTTPStatusError after retry
        exhaustion)."""
        def handler(req):
            return httpx.Response(500, json={"unexpected": "shape"})
        with _client(handler) as c:
            with pytest.raises(httpx.HTTPStatusError):
                get_with_retry(c, "https://example/x", {})
        # Should have retried 3 times before raising — proves the existing
        # 5xx retry path is preserved.
        assert _no_real_sleep.call_count == 3

    def test_500_with_error_code_but_no_inner_error(self, _no_real_sleep):
        """Defensive: a 500 with error.code but no innerError dict must
        not match the detector. Falls through to retry."""
        def handler(req):
            return httpx.Response(
                500,
                json={
                    "error": {
                        "code": "generalException",
                        "message": "Internal error.",
                    }
                },
            )
        with _client(handler) as c:
            with pytest.raises(httpx.HTTPStatusError):
                get_with_retry(c, "https://example/x", {})
        assert _no_real_sleep.call_count == 3

    def test_500_general_exception_but_inner_message_no_match(self, _no_real_sleep):
        """Defensive: error.code=='generalException' alone is NOT enough —
        the inner message must also match. Without the fragment, the 500
        is a real internal error and falls through to retry."""
        def handler(req):
            return httpx.Response(
                500,
                json={
                    "error": {
                        "code": "generalException",
                        "message": "Internal error.",
                        "innerError": {
                            "message": "Database connection pool exhausted.",
                        },
                    }
                },
            )
        with _client(handler) as c:
            with pytest.raises(httpx.HTTPStatusError):
                get_with_retry(c, "https://example/x", {})
        assert _no_real_sleep.call_count == 3

    def test_500_token_rejection_message_but_wrong_code(self, _no_real_sleep):
        """Defensive: the inner message matches but error.code is NOT
        'generalException'. Must NOT fire — proves the AND. Falls through
        to retry."""
        def handler(req):
            return httpx.Response(
                500,
                json={
                    "error": {
                        "code": "InternalServerError",
                        "message": "Internal error.",
                        "innerError": {
                            "message": "The service didn't accept the auth token.",
                        },
                    }
                },
            )
        with _client(handler) as c:
            with pytest.raises(httpx.HTTPStatusError):
                get_with_retry(c, "https://example/x", {})
        assert _no_real_sleep.call_count == 3

    def test_real_5xx_outage_falls_through_to_retry(self, _no_real_sleep):
        """LOAD-BEARING: a generic 5xx outage with no token-rejection
        marker must still be retried by the existing helper. This is
        the safety property — narrow detection means transient outages
        are NOT silently silenced as capability gaps."""
        def handler(req):
            return httpx.Response(503, json={})  # Service Unavailable
        with _client(handler) as c:
            with pytest.raises(httpx.HTTPStatusError):
                get_with_retry(c, "https://example/x", {})
        # 503 retries 3x before giving up.
        assert _no_real_sleep.call_count == 3

    def test_500_non_dict_inner_error(self, _no_real_sleep):
        """Defensive: innerError is not a dict (e.g. None, list, string).
        Must not crash; falls through to retry."""
        def handler(req):
            return httpx.Response(
                500,
                json={
                    "error": {
                        "code": "generalException",
                        "innerError": "not a dict",
                    }
                },
            )
        with _client(handler) as c:
            with pytest.raises(httpx.HTTPStatusError):
                get_with_retry(c, "https://example/x", {})

    # ───── Direct unit tests of the detector helper ─────

    def test_detect_helper_matches_canonical_purview_shape(self):
        body = {
            "error": {
                "code": "generalException",
                "innerError": {
                    "message": "The service didn't accept the auth token. Challenge:['']",
                },
            }
        }
        assert _detect_service_unavailable_500(body) is True

    def test_detect_helper_returns_false_on_empty_body(self):
        assert _detect_service_unavailable_500({}) is False

    def test_detect_helper_returns_false_on_wrong_code(self):
        body = {
            "error": {
                "code": "InternalServerError",
                "innerError": {"message": "didn't accept the auth token"},
            }
        }
        assert _detect_service_unavailable_500(body) is False

    def test_detect_helper_returns_false_on_non_matching_inner(self):
        body = {
            "error": {
                "code": "generalException",
                "innerError": {"message": "Database timeout"},
            }
        }
        assert _detect_service_unavailable_500(body) is False

    def test_detect_helper_returns_false_when_inner_missing(self):
        body = {"error": {"code": "generalException"}}
        assert _detect_service_unavailable_500(body) is False


class TestCapabilityErrorIsSubclassOfMsGraphError:
    """MsGraphCapabilityError must inherit from MsGraphError so existing
    catch-MsGraphError sites still trap it (defensive — connectors should
    upgrade to catch MsGraphCapabilityError specifically, but a fallback
    is preserved)."""

    def test_subclass_relation(self):
        assert issubclass(MsGraphCapabilityError, MsGraphError)

    def test_constructor_kwarg_only_endpoint(self):
        with pytest.raises(TypeError):
            MsGraphCapabilityError("msg", "/some/endpoint")  # type: ignore[misc]

    def test_default_endpoint_is_none(self):
        e = MsGraphCapabilityError("msg")
        assert e.endpoint is None

    def test_endpoint_round_trip(self):
        e = MsGraphCapabilityError("msg", endpoint="/x")
        assert e.endpoint == "/x"
