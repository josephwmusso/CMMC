"""Tests for _msgraph.errors — exception hierarchy and format_pull_error()."""

from __future__ import annotations

from src.connectors._msgraph.errors import (
    MsGraphAuthError,
    MsGraphError,
    MsGraphPermissionError,
    MsGraphThrottledError,
    format_pull_error,
)


class TestFormatPullError:
    """Contract tests for format_pull_error.

    The format is consumed by run.summary.errors[] in connector_runs and
    will be parsed by Pass I dashboard rendering. Changes here are
    contract-breaking — coordinate with Pass I work.
    """

    def test_basic_format_with_msgraph_error(self):
        exc = MsGraphError("token endpoint returned 503")
        result = format_pull_error("AC.L2-3.1.1", "/users", exc)
        assert result == (
            "AC.L2-3.1.1 | /users | MsGraphError: token endpoint returned 503"
        )

    def test_format_with_auth_error(self):
        exc = MsGraphAuthError(
            "Client secret has expired or is invalid.",
            aadsts_code="AADSTS7000222",
        )
        result = format_pull_error("auth", "auth", exc)
        assert result.startswith("auth | auth | MsGraphAuthError: ")
        assert "Client secret has expired" in result

    def test_format_with_permission_error_named(self):
        exc = MsGraphPermissionError(
            "Missing permission: AuditLog.Read.All",
            missing_permission="AuditLog.Read.All",
            endpoint="/auditLogs/signIns",
        )
        result = format_pull_error("AU.L2-3.3.1", "/auditLogs/signIns", exc)
        assert "AU.L2-3.3.1 | /auditLogs/signIns" in result
        assert "MsGraphPermissionError" in result
        assert result.endswith("[missing: AuditLog.Read.All]")

    def test_format_with_permission_error_no_named_permission(self):
        exc = MsGraphPermissionError("403 Forbidden on /policies/...")
        result = format_pull_error(
            "AC.L2-3.1.20", "/policies/crossTenantAccessPolicy/default", exc
        )
        assert "[missing:" not in result
        assert result == (
            "AC.L2-3.1.20 | /policies/crossTenantAccessPolicy/default "
            "| MsGraphPermissionError: 403 Forbidden on /policies/..."
        )

    def test_format_with_throttled_error(self):
        exc = MsGraphThrottledError("Throttled after 3 retries on /signIns")
        result = format_pull_error("AU.L2-3.3.1", "/auditLogs/signIns", exc)
        assert "AU.L2-3.3.1 | /auditLogs/signIns" in result
        assert "MsGraphThrottledError" in result
        assert "Throttled after 3 retries" in result

    def test_format_with_generic_python_exception(self):
        # Connectors may catch arbitrary exceptions during pull. Format
        # must handle non-MsGraph exception types gracefully.
        exc = ValueError("invalid response body")
        result = format_pull_error("AC.L2-3.1.1", "/users", exc)
        assert (
            result
            == "AC.L2-3.1.1 | /users | ValueError: invalid response body"
        )

    def test_empty_exception_message(self):
        exc = MsGraphError("")
        result = format_pull_error("AC.L2-3.1.1", "/users", exc)
        assert "<no message>" in result

    def test_pipe_in_message_is_escaped(self):
        # The ' | ' delimiter is reserved. Embedded pipes get escaped to
        # ' / ' so the parser doesn't split on them.
        exc = MsGraphError("a | b | c")
        result = format_pull_error("AC.L2-3.1.1", "/users", exc)
        # Three pipe-separated fields total in the output (control |
        # endpoint | error). The message's internal pipes are converted.
        assert result.count(" | ") == 2
        assert "a / b / c" in result

    def test_pipe_in_endpoint_is_escaped(self):
        exc = MsGraphError("oops")
        # Hypothetical malformed endpoint — defensive handling
        result = format_pull_error("AC.L2-3.1.1", "/users | weird", exc)
        assert result.count(" | ") == 2
        assert "/users / weird" in result

    def test_message_whitespace_stripped(self):
        exc = MsGraphError("   trailing space   ")
        result = format_pull_error("AC.L2-3.1.1", "/users", exc)
        assert "trailing space" in result
        assert "MsGraphError:    trailing" not in result  # no leading whitespace

    def test_permission_error_with_pipe_in_permission_name(self):
        # Permission names from Microsoft don't contain pipes, but
        # defensive: the [missing: ...] suffix should preserve whatever
        # the attribute holds. Don't escape inside the suffix — it's
        # past the last delimiter.
        exc = MsGraphPermissionError(
            "missing perm",
            missing_permission="Some.Weird.Permission",
        )
        result = format_pull_error("AC.L2-3.1.1", "/x", exc)
        assert "[missing: Some.Weird.Permission]" in result


class TestFormatPullErrorParseability:
    """The format is parseable by Pass I. Test that splitting on ' | '
    produces the expected three (or four) fields.
    """

    def test_split_yields_three_fields_for_normal_case(self):
        exc = MsGraphError("oops")
        result = format_pull_error("AC.L2-3.1.1", "/users", exc)
        parts = result.split(" | ")
        assert len(parts) == 3
        assert parts[0] == "AC.L2-3.1.1"
        assert parts[1] == "/users"
        assert parts[2] == "MsGraphError: oops"

    def test_split_yields_three_fields_with_missing_permission_suffix(self):
        exc = MsGraphPermissionError("403", missing_permission="X.Y.Z")
        result = format_pull_error("AC.L2-3.1.1", "/users", exc)
        # The [missing: ...] suffix is part of the third field — splitting
        # on ' | ' still yields exactly 3 parts.
        parts = result.split(" | ")
        assert len(parts) == 3
        assert "[missing: X.Y.Z]" in parts[2]
