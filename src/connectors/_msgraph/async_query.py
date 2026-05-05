"""Async-query helper for Microsoft Graph endpoints that follow the
POST → poll → GET-results pattern (e.g. /security/auditLog/queries).

Lifecycle:
  1. post_for_async(): POST a query body, receive the initial query
     resource (id and status).
  2. poll_until_done(): GET the query resource until status reaches a
     terminal value (succeeded → return body; failed/cancelled → raise
     MsGraphAsyncFailureError) or the wait budget is exhausted (raise
     MsGraphAsyncTimeoutError).

Retry posture is deliberately narrower for POST than for GET — POST is
non-idempotent and a retry can create duplicate state on the tenant.
The reasoning lives both in this module's docstring and in a body
comment inside _post_with_retry, because future maintainers will read
the body before the docstring.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from src.connectors._msgraph.errors import (
    MsGraphAsyncFailureError,
    MsGraphAsyncTimeoutError,
    MsGraphError,
    MsGraphPermissionError,
    MsGraphThrottledError,
)
from src.connectors._msgraph.retry import (
    BACKOFF_BASE_SECONDS,
    BACKOFF_MAX_SECONDS,
    MAX_RETRIES,
    MAX_RETRY_AFTER_SECONDS,
    _classify_400_or_raise,
    _classify_500_or_raise,
    _detect_licensing_signal,
    _identify_missing_permission,
    _parse_retry_after,
    get_with_retry,
)

log = logging.getLogger(__name__)

# auditLogQuery status taxonomy. Per Microsoft Graph documentation:
#   notStarted, running, succeeded, failed, cancelled.
# Unknown values are treated as non-terminal (warning logged once per
# value per polling session, timeout fires) rather than as a false
# success — silent acceptance of an unknown terminal value is the worse
# failure mode.
_TERMINAL_SUCCESS_STATUSES = frozenset({"succeeded"})
_TERMINAL_FAILURE_STATUSES = frozenset({"failed", "cancelled"})
_NON_TERMINAL_STATUSES = frozenset({"notStarted", "running"})


def _post_with_retry(
    client: httpx.Client,
    url: str,
    headers: dict,
    body: dict,
    *,
    log_context: dict | None = None,
) -> httpx.Response:
    """POST with a narrowed retry posture: ConnectError + 429 only.

    See body comment for the why behind the narrowing — it is load-bearing
    for the safety of /security/auditLog/queries (and any other endpoint
    where POST creates a tenant-side resource).
    """
    # ──────────────────────────────────────────────────────────────────
    # WHY this retry posture is narrower than get_with_retry:
    #
    # POST against an async-query endpoint creates a server-side
    # resource (a query). The verb is non-idempotent. If a retry is
    # issued AFTER the server has already created the resource (a
    # partial-success scenario where the response was lost), the retry
    # produces a DUPLICATE query that lingers in the tenant.
    #
    # The only retry conditions that are SAFE under "the server may
    # have already created state" reasoning are:
    #
    #   - httpx.ConnectError: bytes never reached the server. No
    #     resource was created. Safe to retry.
    #
    #   - HTTP 429: Microsoft explicitly invites retry via the
    #     Retry-After header. A 429 means the server actively rejected
    #     and did NOT create the resource. Safe to retry.
    #
    # Conditions DELIBERATELY NOT retried (which get_with_retry DOES
    # retry, because GET is idempotent):
    #
    #   - 5xx: server may have created the resource before erroring.
    #
    #   - httpx.ReadTimeout / httpx.ReadError: response was lost
    #     mid-flight; the server may have completed creation. Treat
    #     as terminal for this call.
    #
    # If F.3a/b/c live verification finds these no-retry cases hurt
    # reliability for /security/auditLog/queries specifically, the
    # mitigation lives at the connector level (e.g. an idempotency key
    # in the body, or query-by-name de-dupe before issuing a new POST),
    # NOT in loosening this retry policy.
    # ──────────────────────────────────────────────────────────────────
    ctx = log_context or {}
    last_exc: Exception | None = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = client.post(url, headers=headers, json=body)
        except httpx.ConnectError as exc:
            last_exc = exc
            if attempt == MAX_RETRIES:
                break
            sleep_for = min(
                BACKOFF_BASE_SECONDS * (2 ** attempt), BACKOFF_MAX_SECONDS
            )
            log.warning(
                "graph POST connect error, retrying",
                extra={
                    **ctx,
                    "attempt": attempt,
                    "sleep_for": sleep_for,
                    "error": str(exc),
                },
            )
            time.sleep(sleep_for)
            continue

        if resp.status_code == 429:
            retry_after = _parse_retry_after(resp.headers.get("Retry-After"))
            sleep_for = min(
                retry_after
                if retry_after is not None
                else (BACKOFF_BASE_SECONDS * (2 ** attempt)),
                MAX_RETRY_AFTER_SECONDS,
            )
            if attempt == MAX_RETRIES:
                raise MsGraphThrottledError(
                    f"Throttled after {MAX_RETRIES} retries on POST {url}"
                )
            log.warning(
                "graph POST 429, retrying",
                extra={**ctx, "attempt": attempt, "sleep_for": sleep_for},
            )
            time.sleep(sleep_for)
            continue

        if resp.status_code == 403:
            try:
                body_json = resp.json()
            except Exception:
                body_json = {}
            missing = _identify_missing_permission(body_json)
            licensing = _detect_licensing_signal(body_json)
            message = f"403 Forbidden on POST {url}"
            if missing:
                message = (
                    f"Missing permission: {missing} — grant in Entra app "
                    f"registration → API permissions, then click "
                    f"'Grant admin consent for <tenant>'."
                )
            raise MsGraphPermissionError(
                message,
                missing_permission=missing,
                endpoint=url,
                licensing_signal=licensing,
            )

        # F.3c amendment: classify 400 and 5xx shapes via the shared
        # detector helpers (extracted from get_with_retry's 4xx/5xx
        # raise sites for GET/POST symmetry). The helpers raise
        # MsGraphCapabilityError on match; on no match they fall through.
        # POST does NOT retry 5xx — see body comment above — so a 500
        # that's not a capability gap raises raw HTTPStatusError here.
        if resp.status_code == 400:
            _classify_400_or_raise(resp, url)
        if 500 <= resp.status_code < 600:
            _classify_500_or_raise(resp, url)

        # All other non-2xx (4xx other than 400 already handled above,
        # and any 5xx that didn't match a capability-gap shape) raise
        # immediately.
        if resp.status_code >= 400:
            resp.raise_for_status()

        return resp

    # Retry budget exhausted on ConnectError.
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("_post_with_retry exited without response or exception")


def post_for_async(
    client: httpx.Client,
    url: str,
    headers: dict,
    body: dict,
    *,
    log_context: dict | None = None,
) -> dict:
    """POST a body to an async-query endpoint; return the parsed JSON.

    The returned dict is the initial query resource (id, status, etc.).
    Callers pass the id back into poll_until_done via the query_path
    GET URL.
    """
    resp = _post_with_retry(client, url, headers, body, log_context=log_context)
    return resp.json()


def poll_until_done(
    client: httpx.Client,
    url: str,
    headers: dict,
    *,
    max_wait_seconds: int = 300,
    poll_interval_seconds: int = 5,
    log_context: dict | None = None,
) -> dict:
    """Poll an async-query resource until it reaches a terminal status.

    Uses get_with_retry for each poll (GET is idempotent — full retry
    posture is safe). Sleeps poll_interval_seconds between polls. Uses
    time.monotonic() for elapsed-time accounting so a wall-clock jump
    (e.g. NTP correction) does not skew the timeout.

    Returns:
        The final query resource dict on terminal success ('succeeded').

    Raises:
        MsGraphAsyncFailureError: terminal failure status ('failed' or
            'cancelled'). Carries terminal_status and query_id.
        MsGraphAsyncTimeoutError: max_wait_seconds elapsed without a
            terminal status. Carries last_status and query_id.
        MsGraphError: response body was not a JSON object (protocol-level
            malformed). If this pattern recurs in F.3 we promote it to a
            dedicated class.
    """
    ctx = log_context or {}
    seen_unknown_statuses: set[str] = set()
    last_status: str | None = None
    last_query_id: str | None = None
    start = time.monotonic()

    while True:
        resp = get_with_retry(client, url, headers, log_context=ctx)
        try:
            body = resp.json()
        except Exception as exc:
            raise MsGraphError(
                f"Async query poll on {url} returned a non-JSON response"
            ) from exc

        if not isinstance(body, dict):
            raise MsGraphError(
                f"Async query poll on {url} returned a non-object JSON "
                f"payload (got {type(body).__name__})"
            )

        raw_id = body.get("id")
        if isinstance(raw_id, str):
            last_query_id = raw_id

        status = body.get("status")
        if isinstance(status, str):
            last_status = status
            if status in _TERMINAL_SUCCESS_STATUSES:
                return body
            if status in _TERMINAL_FAILURE_STATUSES:
                raise MsGraphAsyncFailureError(
                    f"Async query terminated with status {status!r} on {url}",
                    query_id=last_query_id,
                    terminal_status=status,
                )
            if status not in _NON_TERMINAL_STATUSES:
                if status not in seen_unknown_statuses:
                    seen_unknown_statuses.add(status)
                    log.warning(
                        "async query returned unknown status; treating as "
                        "non-terminal",
                        extra={**ctx, "status": status, "url": url},
                    )
        else:
            # Missing or non-string 'status' field — treat as non-terminal,
            # log once per polling session.
            if "<missing>" not in seen_unknown_statuses:
                seen_unknown_statuses.add("<missing>")
                log.warning(
                    "async query response missing 'status' field; treating "
                    "as non-terminal",
                    extra={**ctx, "url": url},
                )

        # Decide whether we have budget for another sleep+poll cycle.
        # Predicting the next sleep against the budget keeps us from
        # sleeping past max_wait_seconds.
        elapsed = time.monotonic() - start
        if elapsed + poll_interval_seconds > max_wait_seconds:
            raise MsGraphAsyncTimeoutError(
                f"Async query on {url} did not reach a terminal status "
                f"within {max_wait_seconds}s (last_status={last_status!r}).",
                query_id=last_query_id,
                last_status=last_status,
            )

        time.sleep(poll_interval_seconds)
