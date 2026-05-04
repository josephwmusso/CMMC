"""HTTP retry helper for Microsoft Graph.

Wraps httpx GET with exponential backoff on:
  - 429 Too Many Requests (honors Retry-After: numeric seconds OR HTTP-date)
  - 5xx server errors
  - transient network errors (ConnectError, ReadTimeout, ReadError)

Other 4xx (404, 400, etc.) raise httpx.HTTPStatusError immediately — they
are not transient.

403 raises MsGraphPermissionError with the missing permission name parsed
from the Graph error body when identifiable.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from email.utils import parsedate_to_datetime

import httpx

from src.connectors._msgraph.errors import (
    MsGraphPermissionError,
    MsGraphThrottledError,
)

log = logging.getLogger(__name__)

MAX_RETRIES = 3
MAX_RETRY_AFTER_SECONDS = 60
BACKOFF_BASE_SECONDS = 1.0
BACKOFF_MAX_SECONDS = 30.0

# Permission names commonly cited in Graph 403 error messages — used to
# surface the specific permission a customer needs to grant.
_KNOWN_PERMISSIONS = frozenset({
    "User.Read.All",
    "GroupMember.Read.All",
    "Policy.Read.All",
    "UserAuthenticationMethod.Read.All",
    "RoleManagement.Read.Directory",
    "AuditLog.Read.All",
    "Directory.Read.All",
})


def _parse_retry_after(header_value: str | None) -> float | None:
    """Parse Retry-After. Numeric (seconds) or HTTP-date. Returns seconds or None."""
    if not header_value:
        return None
    # Numeric form first.
    try:
        return float(header_value)
    except ValueError:
        pass
    # HTTP-date form.
    try:
        target = parsedate_to_datetime(header_value)
        delta = (target - datetime.now(target.tzinfo)).total_seconds()
        return max(0.0, delta)
    except (TypeError, ValueError):
        return None


def _identify_missing_permission(response_body: dict) -> str | None:
    """Look for a known permission name inside the Graph error message."""
    message = (response_body.get("error") or {}).get("message", "")
    for perm in _KNOWN_PERMISSIONS:
        if perm in message:
            return perm
    return None


def get_with_retry(
    client: httpx.Client,
    url: str,
    headers: dict,
    *,
    log_context: dict | None = None,
) -> httpx.Response:
    """GET with exponential backoff on 429 / 5xx / network errors.

    Raises:
        MsGraphPermissionError on 403 (with parsed permission name when possible).
        MsGraphThrottledError when 429 retries exhaust.
        httpx.HTTPStatusError on non-403 4xx and on 5xx after retry budget.
        httpx.RequestError on persistent network errors.
    """
    ctx = log_context or {}
    last_exc: Exception | None = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = client.get(url, headers=headers)
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.ReadError) as exc:
            last_exc = exc
            if attempt == MAX_RETRIES:
                break
            sleep_for = min(
                BACKOFF_BASE_SECONDS * (2 ** attempt), BACKOFF_MAX_SECONDS
            )
            log.warning(
                "graph network error, retrying",
                extra={**ctx, "attempt": attempt, "sleep_for": sleep_for, "error": str(exc)},
            )
            time.sleep(sleep_for)
            continue

        if resp.status_code == 429:
            retry_after = _parse_retry_after(resp.headers.get("Retry-After"))
            sleep_for = min(
                retry_after if retry_after is not None else (BACKOFF_BASE_SECONDS * (2 ** attempt)),
                MAX_RETRY_AFTER_SECONDS,
            )
            if attempt == MAX_RETRIES:
                raise MsGraphThrottledError(
                    f"Throttled after {MAX_RETRIES} retries on {url}"
                )
            log.warning(
                "graph 429, retrying",
                extra={**ctx, "attempt": attempt, "sleep_for": sleep_for},
            )
            time.sleep(sleep_for)
            continue

        if 500 <= resp.status_code < 600:
            if attempt == MAX_RETRIES:
                resp.raise_for_status()
            sleep_for = min(
                BACKOFF_BASE_SECONDS * (2 ** attempt), BACKOFF_MAX_SECONDS
            )
            log.warning(
                "graph 5xx, retrying",
                extra={**ctx, "attempt": attempt, "status": resp.status_code, "sleep_for": sleep_for},
            )
            time.sleep(sleep_for)
            continue

        if resp.status_code == 403:
            try:
                body = resp.json()
            except Exception:
                body = {}
            missing = _identify_missing_permission(body)
            message = f"403 Forbidden on {url}"
            if missing:
                message = (
                    f"Missing permission: {missing} — grant in Entra app "
                    f"registration → API permissions, then click "
                    f"'Grant admin consent for <tenant>'."
                )
            raise MsGraphPermissionError(
                message, missing_permission=missing, endpoint=url
            )

        if 400 <= resp.status_code < 500:
            resp.raise_for_status()

        return resp

    # All retries exhausted on a network error.
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("get_with_retry exited without response or exception")
