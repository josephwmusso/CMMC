"""Exception hierarchy for the _msgraph helper.

Connector code catches these to produce useful messages in test_connection()
return values and in pull() per-item error reporting.
"""

from __future__ import annotations


class MsGraphError(Exception):
    """Base for all _msgraph errors."""


class MsGraphAuthError(MsGraphError):
    """Token acquisition failed. Includes AADSTS code if recognizable.

    Common AADSTS codes: 7000222 (secret expired), 7000215 (secret invalid),
    90002 (tenant not found), 700016 (client_id not found in tenant).
    """

    def __init__(self, message: str, aadsts_code: str | None = None):
        super().__init__(message)
        self.aadsts_code = aadsts_code


class MsGraphPermissionError(MsGraphError):
    """Graph 403 — missing or insufficient permission.

    Includes the permission name (e.g. "AuditLog.Read.All") parsed from the
    Graph error body when identifiable, plus the endpoint URL.

    licensing_signal is set to True when the Graph error body's error.code
    matches a known unlicensed-tenant signal (e.g. Forbidden_LicensingError).
    Connector code can choose to convert these into a degraded PulledEvidence
    rather than raising — see PulledEvidence.degraded in
    src.connectors.base. F.1 framework contract.
    """

    def __init__(
        self,
        message: str,
        missing_permission: str | None = None,
        endpoint: str | None = None,
        licensing_signal: bool = False,
    ):
        super().__init__(message)
        self.missing_permission = missing_permission
        self.endpoint = endpoint
        self.licensing_signal = licensing_signal


class MsGraphThrottledError(MsGraphError):
    """Graph 429 — exceeded retry budget on a single endpoint."""


class MsGraphAsyncTimeoutError(MsGraphError):
    """poll_until_done exceeded max_wait_seconds without reaching a terminal status.

    Carries the last status string observed before timeout (when known) and the
    query_id, for diagnostic surfacing in connector logs / format_pull_error
    tails. F.1.5 framework contract.
    """

    def __init__(
        self,
        message: str,
        *,
        query_id: str | None = None,
        last_status: str | None = None,
    ):
        super().__init__(message)
        self.query_id = query_id
        self.last_status = last_status


class MsGraphAsyncFailureError(MsGraphError):
    """Async query reached a terminal failure status (failed/cancelled).

    Carries the terminal_status string so connector code can branch:
    'failed' is a genuine error condition; 'cancelled' is operator- or
    policy-driven (different remediation path). F.1.5 framework contract.
    """

    def __init__(
        self,
        message: str,
        *,
        query_id: str | None = None,
        terminal_status: str | None = None,
    ):
        super().__init__(message)
        self.query_id = query_id
        self.terminal_status = terminal_status


def format_pull_error(
    control_id: str,
    endpoint: str,
    exc: Exception,
) -> str:
    """Format an exception encountered during pull() into the canonical
    error string consumed by run.summary.errors[].

    Format: '<control_id> | <endpoint> | <error_class>: <message>'

    The pipe delimiter is reserved — neither control_id, endpoint, nor
    exception messages should contain a literal ' | ' substring. Embedded
    pipes are escaped to ' / ' to avoid breaking downstream parsers.

    Args:
        control_id: CMMC control identifier (e.g. 'AC.L2-3.1.1') or
            literal 'auth' / 'test' for non-control errors.
        endpoint: Graph endpoint path (e.g. '/users') or 'auth' for
            token-acquisition failures.
        exc: The exception to format.

    Returns:
        A single-line string. For MsGraphPermissionError with a known
        missing_permission, the permission name is appended as
        ' [missing: <perm>]' past the last delimiter.
    """
    error_class = type(exc).__name__
    message = str(exc).strip() or "<no message>"

    # Escape any literal pipes to preserve the delimiter contract.
    message = message.replace(" | ", " / ")
    control_id_safe = control_id.replace(" | ", " / ")
    endpoint_safe = endpoint.replace(" | ", " / ")

    parts = f"{control_id_safe} | {endpoint_safe} | {error_class}: {message}"

    # If the exception carries a missing_permission attribute, surface it
    # as a parseable suffix. Pass I parser splits on ' | ' first, then
    # checks for ' [missing: <perm>]' in the tail.
    if isinstance(exc, MsGraphPermissionError) and exc.missing_permission:
        parts += f" [missing: {exc.missing_permission}]"

    return parts
