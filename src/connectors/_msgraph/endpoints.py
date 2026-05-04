"""Cloud environment to URL mapping. Static data, no runtime logic.

Per Phase 5.2 discovery §7.1:

    Cloud      | Token authority                    | Graph endpoint
    -----------+------------------------------------+--------------------------
    COMMERCIAL | https://login.microsoftonline.com  | https://graph.microsoft.com
    GCC_HIGH   | https://login.microsoftonline.us   | https://graph.microsoft.us
    DOD        | https://login.microsoftonline.us   | https://dod-graph.microsoft.us

Note: GCC (the lower tier, not GCC High) uses commercial endpoints.
"""

from __future__ import annotations

from enum import Enum


class CloudEnvironment(str, Enum):
    COMMERCIAL = "commercial"
    GCC_HIGH = "gcc_high"
    DOD = "dod"


_AUTHORITY_URLS: dict[CloudEnvironment, str] = {
    CloudEnvironment.COMMERCIAL: "https://login.microsoftonline.com",
    CloudEnvironment.GCC_HIGH:   "https://login.microsoftonline.us",
    CloudEnvironment.DOD:        "https://login.microsoftonline.us",
}

_GRAPH_BASE_URLS: dict[CloudEnvironment, str] = {
    CloudEnvironment.COMMERCIAL: "https://graph.microsoft.com",
    CloudEnvironment.GCC_HIGH:   "https://graph.microsoft.us",
    CloudEnvironment.DOD:        "https://dod-graph.microsoft.us",
}


def _coerce(env: CloudEnvironment | str) -> CloudEnvironment:
    return env if isinstance(env, CloudEnvironment) else CloudEnvironment(env)


def get_authority_url(env: CloudEnvironment | str, tenant_id: str) -> str:
    """Compose the OAuth2 authority URL for client_credentials.

    Example: get_authority_url("gcc_high", "<tenant>") →
        "https://login.microsoftonline.us/<tenant>"
    """
    return f"{_AUTHORITY_URLS[_coerce(env)]}/{tenant_id}"


def get_graph_base_url(env: CloudEnvironment | str) -> str:
    """Return the Graph API base URL for the given cloud environment."""
    return _GRAPH_BASE_URLS[_coerce(env)]
