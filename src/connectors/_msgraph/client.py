"""MsGraphClient — top-level facade for connector pull() lifecycles.

Wraps TokenManager + httpx.Client + the helper modules. One instance per
connector pull. Usage:

    with MsGraphClient(tenant, client_id, secret, "gcc_high") as client:
        for user in client.paginate("/users?$select=id,displayName"):
            ...
        org = client.get("/organization?$top=1")
"""

from __future__ import annotations

import logging
from typing import Iterator

import httpx

from src.connectors._msgraph import async_query
from src.connectors._msgraph.auth import TokenManager
from src.connectors._msgraph.endpoints import (
    CloudEnvironment,
    get_graph_base_url,
)
from src.connectors._msgraph.pagination import paginate
from src.connectors._msgraph.retry import get_with_retry

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


class MsGraphClient:
    """Sync Microsoft Graph client for client_credentials flow.

    SECURITY: tenant_id, client_id, and client_secret are NEVER returned by
    __repr__ / __str__. The TokenManager protects the secret internally.
    """

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        cloud_env: str | CloudEnvironment,
        *,
        log_context: dict | None = None,
        transport: httpx.BaseTransport | None = None,
    ):
        env = CloudEnvironment(cloud_env) if isinstance(cloud_env, str) else cloud_env
        self._token_manager = TokenManager(
            tenant_id, client_id, client_secret, env
        )
        self._base_url = get_graph_base_url(env)
        # `transport` is exposed so tests can inject httpx.MockTransport.
        client_kwargs: dict = {"timeout": DEFAULT_TIMEOUT}
        if transport is not None:
            client_kwargs["transport"] = transport
        self._http = httpx.Client(**client_kwargs)
        self._log_context = log_context or {}

    def _build_url(self, path: str) -> str:
        """Build the full Graph URL.

        Absolute URLs (e.g. @odata.nextLink) pass through unchanged. Relative
        paths are anchored at /v1.0 under the cloud-specific base URL.
        """
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if path.startswith("/"):
            return f"{self._base_url}/v1.0{path}"
        return f"{self._base_url}/v1.0/{path}"

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token_manager.get_token()}",
            "Accept": "application/json",
            # ConsistencyLevel: eventual is required for some Graph queries
            # (e.g. /users with $count or $filter). Harmless on others.
            "ConsistencyLevel": "eventual",
        }

    def get(self, path: str) -> dict:
        """Single GET, returns parsed JSON. Use for non-paginated endpoints."""
        resp = get_with_retry(
            self._http,
            self._build_url(path),
            self._headers(),
            log_context=self._log_context,
        )
        return resp.json()

    def paginate(self, path: str, *, max_pages: int = 100) -> Iterator[dict]:
        """Iterate rows from a Graph collection, following nextLinks."""
        return paginate(
            self._http,
            self._build_url(path),
            self._headers(),
            max_pages=max_pages,
            log_context=self._log_context,
        )

    def post_for_async(self, path: str, body: dict) -> dict:
        """POST a body to an async-query endpoint (e.g. /security/auditLog/queries).

        Returns the parsed initial query resource (id, status, ...). Use
        poll_until_done(query_path) to wait for terminal status. Retry
        posture is narrower than get() — see async_query._post_with_retry.
        """
        return async_query.post_for_async(
            self._http,
            self._build_url(path),
            self._headers(),
            body,
            log_context=self._log_context,
        )

    def poll_until_done(
        self,
        query_path: str,
        *,
        max_wait_seconds: int = 300,
        poll_interval_seconds: int = 5,
    ) -> dict:
        """Poll a query resource until terminal. See async_query.poll_until_done."""
        return async_query.poll_until_done(
            self._http,
            self._build_url(query_path),
            self._headers(),
            max_wait_seconds=max_wait_seconds,
            poll_interval_seconds=poll_interval_seconds,
            log_context=self._log_context,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "MsGraphClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def __repr__(self) -> str:
        # NEVER include credentials in repr.
        return f"MsGraphClient(base_url={self._base_url!r})"

    __str__ = __repr__
