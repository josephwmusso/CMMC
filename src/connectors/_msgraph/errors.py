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
    """

    def __init__(
        self,
        message: str,
        missing_permission: str | None = None,
        endpoint: str | None = None,
    ):
        super().__init__(message)
        self.missing_permission = missing_permission
        self.endpoint = endpoint


class MsGraphThrottledError(MsGraphError):
    """Graph 429 — exceeded retry budget on a single endpoint."""
