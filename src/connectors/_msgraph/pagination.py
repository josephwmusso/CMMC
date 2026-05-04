"""OData @odata.nextLink follower for Graph collection endpoints.

Each Graph collection response has shape:
    {"value": [...rows...], "@odata.nextLink": "https://..."}

When nextLink is absent, iteration stops. nextLink URLs are absolute (Graph
returns the full host) — they're passed through to httpx unchanged.
"""

from __future__ import annotations

from typing import Iterator

import httpx

from src.connectors._msgraph.retry import get_with_retry


def paginate(
    client: httpx.Client,
    initial_url: str,
    headers: dict,
    *,
    max_pages: int = 100,
    log_context: dict | None = None,
) -> Iterator[dict]:
    """Yield rows from a Graph collection endpoint, following @odata.nextLink.

    max_pages is a hard ceiling to prevent runaway loops on misconfigured
    queries. 100 pages × 1000 rows/page = 100k rows, which is well above any
    realistic Pass E pull (Apex sign-in logs at 24h ≈ 200-500 rows).
    """
    url: str | None = initial_url
    pages = 0
    while url and pages < max_pages:
        resp = get_with_retry(client, url, headers, log_context=log_context)
        body = resp.json()
        for item in body.get("value", []):
            yield item
        url = body.get("@odata.nextLink")
        pages += 1
