"""Token acquisition via MSAL — per-pull caching strategy (discovery §4).

One TokenManager instance per connector pull lifecycle. MSAL's built-in
cache (>= 1.23) handles in-memory deduplication across calls within the
same instance. Cache lives only as long as the TokenManager.

Sovereignty: msal contacts ONLY login.microsoftonline.{com|us}. No
telemetry, no Anthropic / Intranest network surface.
"""

from __future__ import annotations

from msal import ConfidentialClientApplication

from src.connectors._msgraph.endpoints import (
    CloudEnvironment,
    get_authority_url,
)
from src.connectors._msgraph.errors import MsGraphAuthError


# AADSTS codes seen during onboarding mapped to humanized messages.
# Source: Microsoft Entra error code reference + observed customer paste-errors.
AADSTS_MESSAGES: dict[str, str] = {
    "AADSTS7000222": (
        "Client secret has expired or is invalid. Generate a new secret in "
        "Entra → App registrations → Certificates & secrets, then update "
        "this connector."
    ),
    "AADSTS7000215": (
        "Client secret is invalid. Verify the secret VALUE was copied "
        "(not the secret ID), and that no whitespace was included."
    ),
    "AADSTS90002": (
        "Tenant not found. Verify the Tenant ID matches your Entra admin "
        "center → Identity → Overview → Tenant ID."
    ),
    "AADSTS700016": (
        "Application (Client) ID not found in this tenant. Verify the "
        "client_id matches the app registration's 'Application (client) ID' "
        "in the Overview page."
    ),
    "AADSTS50194": (
        "Application is not configured as a multi-tenant application. "
        "Verify the app registration is in the same tenant as the Tenant ID."
    ),
}


def _scope_for(env: CloudEnvironment) -> str:
    """Per-cloud .default scope. Each cloud's Graph endpoint requires its own
    scope string for the client_credentials flow."""
    if env == CloudEnvironment.COMMERCIAL:
        return "https://graph.microsoft.com/.default"
    if env == CloudEnvironment.GCC_HIGH:
        return "https://graph.microsoft.us/.default"
    if env == CloudEnvironment.DOD:
        return "https://dod-graph.microsoft.us/.default"
    raise ValueError(f"unsupported cloud environment: {env}")


class TokenManager:
    """Per-pull token cache. One instance per connector pull lifecycle.

    Holds a MSAL ConfidentialClientApplication and lazily acquires a token
    on first call to get_token(). Subsequent calls hit MSAL's in-memory
    cache.

    SECURITY: client_secret is never logged, repr'd, or str'd.
    """

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        cloud_env: CloudEnvironment,
    ):
        authority = get_authority_url(cloud_env, tenant_id)
        # MSAL holds the secret internally; do NOT keep our own copy.
        self._app = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=authority,
        )
        self._scope = _scope_for(cloud_env)

    def get_token(self) -> str:
        """Acquire access token via client_credentials flow.

        Raises MsGraphAuthError on failure with a humanized message when the
        AADSTS code is recognized.
        """
        result = self._app.acquire_token_for_client(scopes=[self._scope])
        if "access_token" in result:
            return result["access_token"]

        # Failure path — extract AADSTS code if present anywhere in the
        # error_description (Microsoft includes it inline).
        error_desc = result.get("error_description", "") or ""
        aadsts_code: str | None = None
        for code in AADSTS_MESSAGES:
            if code in error_desc:
                aadsts_code = code
                break

        message = (
            AADSTS_MESSAGES[aadsts_code]
            if aadsts_code
            else (error_desc or "Token acquisition failed")
        )
        raise MsGraphAuthError(message, aadsts_code=aadsts_code)

    def __repr__(self) -> str:
        # NEVER include the secret. Only the (already-public) class name.
        return f"<TokenManager scope={self._scope!r}>"

    __str__ = __repr__
