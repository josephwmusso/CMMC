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
    MsGraphCapabilityError,
    MsGraphError,
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

# Graph error.code values that indicate a tenant lacks a license / capability
# the connector tried to use. Connectors can convert these into degraded
# PulledEvidence rather than raising. F.1 framework contract.
# Initial set is intentionally narrow — grow on encounter as F.3a/F.3b live
# verification surfaces new codes (one new test per addition).
_LICENSING_ERROR_CODES = frozenset({
    "Forbidden_LicensingError",
})

# Substrings observed inside Graph 400 + BadRequest message bodies when a
# tenant entirely lacks the service the endpoint targets. Surfaced by
# F.3a live verification against the intranest-m365-test trial:
#
#   "Tenant does not have a SPO license."     (no SharePoint Online)
#   "Request not applicable to target tenant." (no Intune provisioning)
#
# Lowercase, substring-matched. Match implies the connector should treat
# the 400 as a capability gap (degraded evidence path) rather than a real
# bad-request bug. Distinct from licensing_signal — that path stays at 403.
_CAPABILITY_GAP_MESSAGE_FRAGMENTS = frozenset({
    "does not have",
    "not applicable to target tenant",
})

# Substrings observed inside Graph 400 + UnknownError error.message bodies
# when a tenant has unified audit logging disabled. Surfaced by F.3c live
# verification against the intranest-m365-test trial on the
# /beta/security/auditLog/queries endpoint:
#
#   error.code = "UnknownError"
#   error.message = '{"...","Status":"AuditingDisabledTenant",...}'
#     (stringified JSON blob with internal status fields)
#
# Case-sensitive, substring-matched against the message. Distinct from
# _CAPABILITY_GAP_MESSAGE_FRAGMENTS because the outer error.code is
# "UnknownError" (not "BadRequest") AND the message is a stringified
# JSON blob requiring substring match against the embedded Status field.
# The narrow two-condition AND (UnknownError + AuditingDisabledTenant
# fragment) prevents the generic UnknownError code from being silently
# reclassified as a capability gap on every other 400 that uses it.
_AUDIT_DISABLED_400_MESSAGE_FRAGMENTS = frozenset({
    "AuditingDisabledTenant",
})

# Substrings observed inside Graph 500 + generalException innerError.message
# bodies when an underlying Microsoft service backend (e.g. Purview /
# Information Protection's "PolicyProfile" service) rejects the otherwise-
# valid Graph bearer token because the tenant has no subscription /
# configuration to query. Surfaced by F.3b live verification against the
# intranest-m365-test trial on the
# /beta/security/informationProtection/sensitivityLabels endpoint:
#
#   error.code = "generalException"
#   innerError.message = "The service didn't accept the auth token. Challenge:[''] ..."
#   CorrelationId.Description = "PolicyProfile"
#
# Lowercase, substring-matched against the inner message. The narrow
# signature (code == "generalException" AND inner-message-fragment match)
# prevents transient 500s from being silently reclassified as capability
# gaps — only this specific Microsoft signal pattern is treated as a
# service-unavailable signal.
_SERVICE_UNAVAILABLE_500_INNER_FRAGMENTS = frozenset({
    "didn't accept the auth token",
    "did not accept the auth token",
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


def _detect_licensing_signal(response_body: dict) -> bool:
    """Return True if the Graph 403 body's error.code matches a known
    unlicensed-tenant signal (e.g. Forbidden_LicensingError).

    Defensive against absent or non-string code field — Graph occasionally
    returns numeric codes on certain endpoints. Returns False rather than
    raising on any malformed shape.
    """
    error = response_body.get("error") or {}
    code = error.get("code")
    if not isinstance(code, str):
        return False
    return code in _LICENSING_ERROR_CODES


def _detect_capability_gap(response_body: dict) -> bool:
    """Return True if the Graph 400 body indicates a tenant capability gap
    (service entirely unprovisioned) rather than a malformed-request bug.

    Match shape: error.code == "BadRequest" AND any fragment in
    _CAPABILITY_GAP_MESSAGE_FRAGMENTS appears as a substring in
    error.message (case-insensitive).

    Defensive against absent or non-string code/message fields — returns
    False rather than raising on any malformed shape. Surfaced by F.3a
    live verification.
    """
    error = response_body.get("error") or {}
    code = error.get("code")
    message = error.get("message")
    if not isinstance(code, str) or not isinstance(message, str):
        return False
    if code != "BadRequest":
        return False
    lowered = message.lower()
    return any(frag in lowered for frag in _CAPABILITY_GAP_MESSAGE_FRAGMENTS)


def _classify_500_or_raise(resp: httpx.Response, url: str) -> None:
    """Inspect a 5xx response body for known capability-gap shapes; raise
    MsGraphCapabilityError if matched, otherwise return None (caller
    decides retry-vs-raise based on verb semantics — GET retries 5xx,
    POST raises immediately).

    Used at both GET and POST 5xx raise sites so the detector surface
    stays symmetric across HTTP verbs. F.3c amendment for symmetry with
    _classify_400_or_raise; the only currently-known 5xx shape is
    Microsoft's PolicyProfile/InformationProtection 500 + generalException
    + token-rejection inner message (F.3b discovery).

    The "or_raise" suffix reflects the helper's only side effect (raising
    MsGraphCapabilityError on match). On no-match the helper is a no-op
    so the caller can continue with verb-specific retry-or-raise logic.
    """
    try:
        body = resp.json()
    except Exception:
        body = {}
    if _detect_service_unavailable_500(body):
        error_obj = body.get("error") or {}
        inner = error_obj.get("innerError") or {}
        inner_msg = inner.get("message") or "service unavailable"
        raise MsGraphCapabilityError(
            f"Service unavailable on {url}: {inner_msg}",
            endpoint=url,
        )
    return None


def _classify_400_or_raise(resp: httpx.Response, url: str) -> None:
    """Inspect a 400 response body for known capability-gap shapes; raise
    MsGraphCapabilityError if any detector matches, otherwise raise the
    raw httpx.HTTPStatusError.

    Used at both GET and POST 400 raise sites (get_with_retry and
    _post_with_retry in async_query.py) so the detection surface stays
    uniform across HTTP verbs. F.3c amendment — before this extraction,
    the detectors were applied only on the GET path, and POST capability
    gaps escaped as raw httpx.HTTPStatusError (live-smoke evidence:
    async_query.py:174 raise_for_status() bubbled past the connector's
    except MsGraphCapabilityError handler).

    Detector order at the 400 raise site is locked:
      1. _detect_capability_gap  (BadRequest + fragment match)
      2. _detect_audit_disabled_400  (UnknownError + AuditingDisabledTenant)
    The two error.code values are orthogonal (BadRequest vs UnknownError)
    so semantic ordering doesn't matter, but the explicit ordering is
    locked by TestAuditDisabled400Detection's cross-detector ordering
    test for future-detector-addition safety.
    """
    try:
        body = resp.json()
    except Exception:
        body = {}
    if _detect_capability_gap(body):
        error_obj = body.get("error") or {}
        graph_message = error_obj.get("message") or "Capability gap"
        raise MsGraphCapabilityError(
            f"Capability gap on {url}: {graph_message}",
            endpoint=url,
        )
    if _detect_audit_disabled_400(body):
        raise MsGraphCapabilityError(
            f"Audit log query unavailable on {url}: tenant has unified "
            f"audit logging disabled.",
            endpoint=url,
        )
    # Generic 400 — not a known capability gap. Existing behavior:
    # raise the httpx HTTPStatusError so the caller sees the status + URL.
    resp.raise_for_status()


def _detect_audit_disabled_400(response_body: dict) -> bool:
    """Return True if a Graph 400 body indicates a tenant has unified
    audit logging disabled (capability gap signaled with error.code
    "UnknownError" rather than "BadRequest").

    Match shape: error.code == "UnknownError" AND any fragment in
    _AUDIT_DISABLED_400_MESSAGE_FRAGMENTS appears as a substring in
    error.message (case-sensitive — Microsoft's embedded "Status"
    string is exact-cased).

    The two-condition AND is load-bearing: it prevents the generic
    "UnknownError" code from being silently reclassified as a capability
    gap on every 400 that uses it (Microsoft's catch-all). A 400 with
    "UnknownError" but no audit-disabled fragment match falls through
    to the existing httpx.HTTPStatusError path.

    Defensive against absent or non-string code/message fields — returns
    False rather than raising on any malformed shape. Surfaced by F.3c
    live verification against /beta/security/auditLog/queries.
    """
    error = response_body.get("error") or {}
    code = error.get("code")
    message = error.get("message")
    if not isinstance(code, str) or code != "UnknownError":
        return False
    if not isinstance(message, str):
        return False
    return any(
        frag in message for frag in _AUDIT_DISABLED_400_MESSAGE_FRAGMENTS
    )


def _detect_service_unavailable_500(response_body: dict) -> bool:
    """Return True if a Graph 500 body indicates an underlying service
    backend rejected the token because the tenant has no subscription
    / configuration for that service (capability gap signaled as a 500
    rather than a 400).

    Match shape: error.code == "generalException" AND any fragment in
    _SERVICE_UNAVAILABLE_500_INNER_FRAGMENTS appears in
    error.innerError.message (case-insensitive).

    The two-condition AND is load-bearing: it prevents transient 500
    outages from being silently reclassified as capability gaps. A 500
    with a different code, or a 500 whose inner message doesn't match
    the narrow service-rejection fragments, falls through to the
    existing retry-then-raise behavior.

    Defensive against absent or non-string code/innerError/message
    fields — returns False rather than raising on any malformed shape.
    Surfaced by F.3b live verification against the
    /beta/security/informationProtection/sensitivityLabels endpoint
    (Purview / PolicyProfile backend rejected the token on the
    unprovisioned trial tenant).
    """
    error = response_body.get("error") or {}
    code = error.get("code")
    if not isinstance(code, str) or code != "generalException":
        return False
    inner = error.get("innerError") or {}
    if not isinstance(inner, dict):
        return False
    inner_message = inner.get("message")
    if not isinstance(inner_message, str):
        return False
    lowered = inner_message.lower()
    return any(frag in lowered for frag in _SERVICE_UNAVAILABLE_500_INNER_FRAGMENTS)


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
            # F.3c amendment: 5xx classification shared with the POST path
            # via _classify_500_or_raise. On capability match, raise
            # immediately (don't burn the retry budget on an unrecoverable
            # 500). On no match, continue to the GET-specific retry logic.
            _classify_500_or_raise(resp, url)
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
            licensing = _detect_licensing_signal(body)
            message = f"403 Forbidden on {url}"
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

        if resp.status_code == 400:
            # F.3c amendment: 400 classification is shared with the POST
            # path via _classify_400_or_raise. Detectors stay GET-and-POST
            # symmetric.
            _classify_400_or_raise(resp, url)

        if 400 <= resp.status_code < 500:
            resp.raise_for_status()

        return resp

    # All retries exhausted on a network error.
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("get_with_retry exited without response or exception")
