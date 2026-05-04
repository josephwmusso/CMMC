"""Sync Microsoft Graph helper for connector pull() lifecycles.

Public API surface — re-exports from internal modules. Connector code
imports only from src.connectors._msgraph; never reaches into submodules
directly.
"""

from src.connectors._msgraph.client import MsGraphClient
from src.connectors._msgraph.endpoints import (
    CloudEnvironment,
    get_authority_url,
    get_graph_base_url,
)
from src.connectors._msgraph.errors import (
    MsGraphAuthError,
    MsGraphError,
    MsGraphPermissionError,
    MsGraphThrottledError,
    format_pull_error,
)

__all__ = [
    "MsGraphClient",
    "CloudEnvironment",
    "get_authority_url",
    "get_graph_base_url",
    "MsGraphError",
    "MsGraphAuthError",
    "MsGraphPermissionError",
    "MsGraphThrottledError",
    "format_pull_error",
]
