"""Tests for the async-query helper (post_for_async + poll_until_done).

Mirrors the test_retry.py pattern: builds httpx.Client instances backed by
httpx.MockTransport so request sequences are predictable, and patches
time.sleep / time.monotonic so tests run in milliseconds with deterministic
elapsed-time accounting.

Per Phase 2 design: zero edits to existing test files. F.1.5 framework
contract — POST retry posture is narrower than GET (see async_query
_post_with_retry body comment).
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest

from src.connectors._msgraph.async_query import (
    _post_with_retry,
    poll_until_done,
    post_for_async,
)
from src.connectors._msgraph.errors import (
    MsGraphAsyncFailureError,
    MsGraphAsyncTimeoutError,
    MsGraphError,
    MsGraphPermissionError,
    MsGraphThrottledError,
)


def _client(handler) -> httpx.Client:
    """Build an httpx.Client with a MockTransport invoking handler(request)."""
    return httpx.Client(transport=httpx.MockTransport(handler))


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture
def no_real_sleep():
    """Mock time.sleep so retry/poll cycles don't actually wait."""
    with patch("src.connectors._msgraph.async_query.time.sleep") as m:
        yield m


@pytest.fixture
def virtual_clock():
    """Mock both time.sleep and time.monotonic so polling tests can drive
    elapsed-time deterministically. Each fake_sleep call advances the
    virtual clock by the requested seconds; fake_monotonic reads it.
    """
    state = {"now": 0.0}

    def fake_sleep(seconds):
        state["now"] += float(seconds)

    def fake_monotonic():
        return state["now"]

    with patch(
        "src.connectors._msgraph.async_query.time.sleep",
        side_effect=fake_sleep,
    ) as sleep_mock, patch(
        "src.connectors._msgraph.async_query.time.monotonic",
        side_effect=fake_monotonic,
    ):
        yield sleep_mock


# ──────────────────────────────────────────────────────────────────────
# post_for_async — happy path + retry posture
# ──────────────────────────────────────────────────────────────────────


class TestPostForAsync:
    """post_for_async issues a POST and returns the parsed JSON body.

    Retry posture is intentionally narrower than get_with_retry:
        - retry on httpx.ConnectError (bytes never reached server)
        - retry on HTTP 429 (server invites retry)
        - DO NOT retry on 5xx (server may have created resource)
        - DO NOT retry on httpx.ReadTimeout / ReadError (response lost mid-flight)
    """

    def test_post_returns_parsed_body(self, no_real_sleep):
        def handler(req):
            assert req.method == "POST"
            return httpx.Response(
                201, json={"id": "query-1", "status": "notStarted"}
            )

        with _client(handler) as c:
            result = post_for_async(c, "https://example/q", {}, {"x": 1})
        assert result == {"id": "query-1", "status": "notStarted"}
        no_real_sleep.assert_not_called()

    def test_post_sends_body_as_json(self, no_real_sleep):
        captured = {}

        def handler(req):
            captured["content"] = req.content
            captured["content_type"] = req.headers.get("content-type", "")
            return httpx.Response(201, json={"id": "q", "status": "notStarted"})

        with _client(handler) as c:
            post_for_async(c, "https://example/q", {}, {"filter": "abc"})
        assert b'"filter"' in captured["content"]
        assert b'"abc"' in captured["content"]
        assert "json" in captured["content_type"]

    def test_post_429_retried_then_succeeds(self, no_real_sleep):
        calls = {"n": 0}

        def handler(req):
            calls["n"] += 1
            if calls["n"] == 1:
                return httpx.Response(
                    429, headers={"Retry-After": "2"}, json={"error": {}}
                )
            return httpx.Response(201, json={"id": "q", "status": "notStarted"})

        with _client(handler) as c:
            result = post_for_async(c, "https://example/q", {}, {})
        assert result == {"id": "q", "status": "notStarted"}
        no_real_sleep.assert_called_once()
        assert no_real_sleep.call_args[0][0] == 2.0

    def test_post_429_exhausted_raises_throttled(self, no_real_sleep):
        def handler(req):
            return httpx.Response(429, headers={"Retry-After": "1"}, json={})

        with _client(handler) as c:
            with pytest.raises(MsGraphThrottledError):
                post_for_async(c, "https://example/q", {}, {})
        # 3 sleeps (attempts 0,1,2 sleep; attempt 3 raises before sleep).
        assert no_real_sleep.call_count == 3

    def test_post_5xx_raises_immediately_no_retry(self, no_real_sleep):
        """Critical safety property: 5xx is NOT retried because the server
        may have already created the query resource before erroring."""
        calls = {"n": 0}

        def handler(req):
            calls["n"] += 1
            return httpx.Response(503, json={})

        with _client(handler) as c:
            with pytest.raises(httpx.HTTPStatusError):
                post_for_async(c, "https://example/q", {}, {})
        assert calls["n"] == 1
        no_real_sleep.assert_not_called()

    def test_post_500_raises_immediately_no_retry(self, no_real_sleep):
        calls = {"n": 0}

        def handler(req):
            calls["n"] += 1
            return httpx.Response(500, json={})

        with _client(handler) as c:
            with pytest.raises(httpx.HTTPStatusError):
                post_for_async(c, "https://example/q", {}, {})
        assert calls["n"] == 1

    def test_post_read_timeout_raises_immediately_no_retry(self, no_real_sleep):
        """ReadTimeout = response lost mid-flight; server may have completed
        the create. Treat as terminal, do not retry."""
        calls = {"n": 0}

        def handler(req):
            calls["n"] += 1
            raise httpx.ReadTimeout("simulated read timeout")

        with _client(handler) as c:
            with pytest.raises(httpx.ReadTimeout):
                post_for_async(c, "https://example/q", {}, {})
        assert calls["n"] == 1
        no_real_sleep.assert_not_called()

    def test_post_read_error_raises_immediately_no_retry(self, no_real_sleep):
        calls = {"n": 0}

        def handler(req):
            calls["n"] += 1
            raise httpx.ReadError("simulated read error")

        with _client(handler) as c:
            with pytest.raises(httpx.ReadError):
                post_for_async(c, "https://example/q", {}, {})
        assert calls["n"] == 1
        no_real_sleep.assert_not_called()

    def test_post_connect_error_retried_then_succeeds(self, no_real_sleep):
        """ConnectError = bytes never reached the server. No resource was
        created, safe to retry."""
        calls = {"n": 0}

        def handler(req):
            calls["n"] += 1
            if calls["n"] <= 2:
                raise httpx.ConnectError("simulated connect failure")
            return httpx.Response(201, json={"id": "q", "status": "notStarted"})

        with _client(handler) as c:
            result = post_for_async(c, "https://example/q", {}, {})
        assert result == {"id": "q", "status": "notStarted"}
        assert no_real_sleep.call_count == 2

    def test_post_connect_error_exhausted_reraises(self, no_real_sleep):
        def handler(req):
            raise httpx.ConnectError("persistent connect failure")

        with _client(handler) as c:
            with pytest.raises(httpx.ConnectError):
                post_for_async(c, "https://example/q", {}, {})
        # MAX_RETRIES=3 → 3 sleeps before final attempt that raises through.
        assert no_real_sleep.call_count == 3

    def test_post_403_raises_permission_error(self, no_real_sleep):
        def handler(req):
            return httpx.Response(
                403,
                json={
                    "error": {
                        "message": "Insufficient privileges. AuditLog.Read.All required."
                    }
                },
            )

        with _client(handler) as c:
            with pytest.raises(MsGraphPermissionError) as exc_info:
                post_for_async(
                    c, "https://example/security/auditLog/queries", {}, {}
                )
        assert exc_info.value.missing_permission == "AuditLog.Read.All"
        no_real_sleep.assert_not_called()

    def test_post_403_with_licensing_signal_round_trips(self, no_real_sleep):
        def handler(req):
            return httpx.Response(
                403,
                json={
                    "error": {
                        "code": "Forbidden_LicensingError",
                        "message": "Tenant requires license.",
                    }
                },
            )

        with _client(handler) as c:
            with pytest.raises(MsGraphPermissionError) as exc_info:
                post_for_async(c, "https://example/q", {}, {})
        assert exc_info.value.licensing_signal is True

    def test_post_400_raises_immediately(self, no_real_sleep):
        def handler(req):
            return httpx.Response(400, json={"error": {"message": "bad request"}})

        with _client(handler) as c:
            with pytest.raises(httpx.HTTPStatusError):
                post_for_async(c, "https://example/q", {}, {})
        no_real_sleep.assert_not_called()

    def test_post_404_raises_immediately(self, no_real_sleep):
        def handler(req):
            return httpx.Response(404, json={})

        with _client(handler) as c:
            with pytest.raises(httpx.HTTPStatusError):
                post_for_async(c, "https://example/q", {}, {})


# ──────────────────────────────────────────────────────────────────────
# poll_until_done — terminal handling, timeout, malformed responses
# ──────────────────────────────────────────────────────────────────────


class TestPollUntilDone:
    """poll_until_done sleeps poll_interval_seconds between GETs and uses
    time.monotonic() for elapsed-time accounting (clock-jump-safe).

    All tests use the virtual_clock fixture so fake_sleep advances a
    fake monotonic clock — mirrors how real time would behave but in
    milliseconds and deterministically.
    """

    def test_poll_succeeded_first_try(self, virtual_clock):
        calls = {"n": 0}

        def handler(req):
            calls["n"] += 1
            return httpx.Response(
                200, json={"id": "q-1", "status": "succeeded"}
            )

        with _client(handler) as c:
            result = poll_until_done(c, "https://example/q-1", {})
        assert result == {"id": "q-1", "status": "succeeded"}
        assert calls["n"] == 1
        virtual_clock.assert_not_called()

    def test_poll_running_then_succeeded(self, virtual_clock):
        calls = {"n": 0}

        def handler(req):
            calls["n"] += 1
            if calls["n"] == 1:
                return httpx.Response(
                    200, json={"id": "q", "status": "running"}
                )
            return httpx.Response(200, json={"id": "q", "status": "succeeded"})

        with _client(handler) as c:
            result = poll_until_done(c, "https://example/q", {})
        assert result["status"] == "succeeded"
        assert calls["n"] == 2
        # One sleep between the two polls.
        assert virtual_clock.call_count == 1
        assert virtual_clock.call_args[0][0] == 5

    def test_poll_notstarted_running_succeeded(self, virtual_clock):
        sequence = ["notStarted", "running", "succeeded"]
        calls = {"n": 0}

        def handler(req):
            status = sequence[calls["n"]]
            calls["n"] += 1
            return httpx.Response(200, json={"id": "q", "status": status})

        with _client(handler) as c:
            result = poll_until_done(c, "https://example/q", {})
        assert result["status"] == "succeeded"
        assert calls["n"] == 3
        assert virtual_clock.call_count == 2

    def test_poll_failed_raises_failure_with_status(self, virtual_clock):
        def handler(req):
            return httpx.Response(
                200, json={"id": "q-fail", "status": "failed"}
            )

        with _client(handler) as c:
            with pytest.raises(MsGraphAsyncFailureError) as exc_info:
                poll_until_done(c, "https://example/q-fail", {})
        assert exc_info.value.terminal_status == "failed"
        assert exc_info.value.query_id == "q-fail"
        virtual_clock.assert_not_called()

    def test_poll_cancelled_raises_failure_with_status(self, virtual_clock):
        def handler(req):
            return httpx.Response(
                200, json={"id": "q-cancel", "status": "cancelled"}
            )

        with _client(handler) as c:
            with pytest.raises(MsGraphAsyncFailureError) as exc_info:
                poll_until_done(c, "https://example/q-cancel", {})
        assert exc_info.value.terminal_status == "cancelled"
        assert exc_info.value.query_id == "q-cancel"

    def test_poll_failure_after_running_carries_query_id(self, virtual_clock):
        """query_id seen on the first running poll is retained when a later
        poll returns terminal failure with the same id."""
        sequence = [
            ("q-x", "running"),
            ("q-x", "running"),
            ("q-x", "failed"),
        ]
        calls = {"n": 0}

        def handler(req):
            qid, status = sequence[calls["n"]]
            calls["n"] += 1
            return httpx.Response(200, json={"id": qid, "status": status})

        with _client(handler) as c:
            with pytest.raises(MsGraphAsyncFailureError) as exc_info:
                poll_until_done(c, "https://example/q-x", {})
        assert exc_info.value.terminal_status == "failed"
        assert exc_info.value.query_id == "q-x"

    def test_poll_timeout_while_running(self, virtual_clock):
        def handler(req):
            return httpx.Response(
                200, json={"id": "q-slow", "status": "running"}
            )

        with _client(handler) as c:
            with pytest.raises(MsGraphAsyncTimeoutError) as exc_info:
                poll_until_done(
                    c,
                    "https://example/q-slow",
                    {},
                    max_wait_seconds=10,
                    poll_interval_seconds=5,
                )
        assert exc_info.value.last_status == "running"
        assert exc_info.value.query_id == "q-slow"

    def test_poll_unknown_status_warns_once_and_eventually_times_out(
        self, virtual_clock, caplog
    ):
        """An unknown status value is treated as non-terminal; warning fires
        once per unique value per session; timeout eventually fires."""
        import logging

        def handler(req):
            return httpx.Response(
                200, json={"id": "q-weird", "status": "weirdNewStatus"}
            )

        caplog.set_level(logging.WARNING)
        with _client(handler) as c:
            with pytest.raises(MsGraphAsyncTimeoutError) as exc_info:
                poll_until_done(
                    c,
                    "https://example/q-weird",
                    {},
                    max_wait_seconds=10,
                    poll_interval_seconds=5,
                )
        assert exc_info.value.last_status == "weirdNewStatus"
        # Warning must fire once even though we polled multiple times.
        unknown_warnings = [
            r for r in caplog.records if "unknown status" in r.getMessage()
        ]
        assert len(unknown_warnings) == 1

    def test_poll_missing_status_field_treated_non_terminal(
        self, virtual_clock, caplog
    ):
        import logging

        def handler(req):
            return httpx.Response(200, json={"id": "q-broken"})

        caplog.set_level(logging.WARNING)
        with _client(handler) as c:
            with pytest.raises(MsGraphAsyncTimeoutError) as exc_info:
                poll_until_done(
                    c,
                    "https://example/q-broken",
                    {},
                    max_wait_seconds=5,
                    poll_interval_seconds=5,
                )
        # Never observed a string status.
        assert exc_info.value.last_status is None
        # Warning fires once.
        missing_warnings = [
            r
            for r in caplog.records
            if "missing 'status'" in r.getMessage()
        ]
        assert len(missing_warnings) == 1

    def test_poll_non_string_status_treated_non_terminal(self, virtual_clock):
        """Defensive: non-string status (e.g. numeric) treated as non-terminal,
        not as a successful match against any frozenset."""

        def handler(req):
            return httpx.Response(
                200, json={"id": "q", "status": 42}
            )

        with _client(handler) as c:
            with pytest.raises(MsGraphAsyncTimeoutError) as exc_info:
                poll_until_done(
                    c,
                    "https://example/q",
                    {},
                    max_wait_seconds=5,
                    poll_interval_seconds=5,
                )
        assert exc_info.value.last_status is None

    def test_poll_non_json_raises_msgraph_error(self, virtual_clock):
        def handler(req):
            return httpx.Response(200, content=b"<html>not json</html>")

        with _client(handler) as c:
            with pytest.raises(MsGraphError):
                poll_until_done(c, "https://example/q", {})

    def test_poll_non_object_json_raises_msgraph_error(self, virtual_clock):
        """A JSON list (not an object) should raise rather than silently
        treating the response as a missing-status non-terminal."""

        def handler(req):
            return httpx.Response(200, json=["a", "b", "c"])

        with _client(handler) as c:
            with pytest.raises(MsGraphError) as exc_info:
                poll_until_done(c, "https://example/q", {})
        assert "non-object" in str(exc_info.value)

    def test_poll_custom_intervals_respected(self, virtual_clock):
        """Custom poll_interval_seconds is passed to time.sleep verbatim."""
        sequence = ["running", "running", "succeeded"]
        calls = {"n": 0}

        def handler(req):
            status = sequence[calls["n"]]
            calls["n"] += 1
            return httpx.Response(200, json={"id": "q", "status": status})

        with _client(handler) as c:
            result = poll_until_done(
                c,
                "https://example/q",
                {},
                max_wait_seconds=60,
                poll_interval_seconds=2,
            )
        assert result["status"] == "succeeded"
        assert virtual_clock.call_count == 2
        for call in virtual_clock.call_args_list:
            assert call[0][0] == 2


# ──────────────────────────────────────────────────────────────────────
# Error-class shape: kwarg-only, defaults, attribute round-trip
# ──────────────────────────────────────────────────────────────────────


class TestErrorClasses:
    """MsGraphAsyncTimeoutError and MsGraphAsyncFailureError both use
    keyword-only constructor signatures (* before the optional fields) to
    prevent silent breakage if field ordering ever changes.
    """

    def test_async_timeout_error_default_fields(self):
        e = MsGraphAsyncTimeoutError("timed out")
        assert e.query_id is None
        assert e.last_status is None
        assert str(e) == "timed out"

    def test_async_timeout_error_kwarg_round_trip(self):
        e = MsGraphAsyncTimeoutError(
            "timed out", query_id="q-1", last_status="running"
        )
        assert e.query_id == "q-1"
        assert e.last_status == "running"

    def test_async_timeout_error_kwarg_only(self):
        """Passing positional after the message should raise TypeError —
        the * in the signature enforces this."""
        with pytest.raises(TypeError):
            MsGraphAsyncTimeoutError("msg", "q-1", "running")  # type: ignore[misc]

    def test_async_failure_error_default_fields(self):
        e = MsGraphAsyncFailureError("failed")
        assert e.query_id is None
        assert e.terminal_status is None

    def test_async_failure_error_kwarg_round_trip(self):
        e = MsGraphAsyncFailureError(
            "failed", query_id="q-2", terminal_status="cancelled"
        )
        assert e.query_id == "q-2"
        assert e.terminal_status == "cancelled"

    def test_async_failure_error_kwarg_only(self):
        with pytest.raises(TypeError):
            MsGraphAsyncFailureError("msg", "q-2", "failed")  # type: ignore[misc]

    def test_both_inherit_from_msgraph_error(self):
        """Connector code that catches MsGraphError as a wide net should
        catch both new errors."""
        assert issubclass(MsGraphAsyncTimeoutError, MsGraphError)
        assert issubclass(MsGraphAsyncFailureError, MsGraphError)


# ──────────────────────────────────────────────────────────────────────
# _post_with_retry direct surface (for completeness)
# ──────────────────────────────────────────────────────────────────────


class TestPostWithRetryDirect:
    """post_for_async is a thin wrapper around _post_with_retry. A couple
    of direct tests document the lower-level contract: returns the raw
    httpx.Response on success, applies the same retry posture."""

    def test_returns_response_on_success(self, no_real_sleep):
        def handler(req):
            return httpx.Response(201, json={"ok": True})

        with _client(handler) as c:
            resp = _post_with_retry(c, "https://example/q", {}, {})
        assert isinstance(resp, httpx.Response)
        assert resp.status_code == 201
        assert resp.json() == {"ok": True}
