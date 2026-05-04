"""Tests for the @odata.nextLink follower."""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest

from src.connectors._msgraph.pagination import paginate


@pytest.fixture(autouse=True)
def _no_sleep():
    with patch("src.connectors._msgraph.retry.time.sleep"):
        yield


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_single_page_yields_all_rows():
    def handler(req):
        return httpx.Response(200, json={"value": [{"id": 1}, {"id": 2}, {"id": 3}]})
    with _client(handler) as c:
        rows = list(paginate(c, "https://graph/users", {}))
    assert rows == [{"id": 1}, {"id": 2}, {"id": 3}]


def test_two_pages_yields_all_rows():
    pages = [
        {"value": [{"id": 1}, {"id": 2}], "@odata.nextLink": "https://graph/users?next=2"},
        {"value": [{"id": 3}, {"id": 4}]},
    ]
    state = {"i": 0}

    def handler(req):
        body = pages[state["i"]]
        state["i"] += 1
        return httpx.Response(200, json=body)

    with _client(handler) as c:
        rows = list(paginate(c, "https://graph/users", {}))
    assert rows == [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]


def test_empty_value_yields_nothing():
    def handler(req):
        return httpx.Response(200, json={"value": []})
    with _client(handler) as c:
        rows = list(paginate(c, "https://graph/users", {}))
    assert rows == []


def test_max_pages_honored():
    """max_pages=1 stops after the first page, even if nextLink is present."""
    def handler(req):
        return httpx.Response(
            200,
            json={"value": [{"id": 1}], "@odata.nextLink": "https://graph/users?next=2"},
        )
    with _client(handler) as c:
        rows = list(paginate(c, "https://graph/users", {}, max_pages=1))
    assert rows == [{"id": 1}]


def test_absolute_nextlink_url_used_unchanged():
    """Graph returns absolute nextLink URLs; we follow them as-is."""
    seen_urls: list[str] = []

    def handler(req):
        seen_urls.append(str(req.url))
        if "next=2" in str(req.url):
            return httpx.Response(200, json={"value": [{"id": 2}]})
        return httpx.Response(
            200,
            json={"value": [{"id": 1}], "@odata.nextLink": "https://graph.microsoft.com/v1.0/users?$skiptoken=next=2"},
        )

    with _client(handler) as c:
        rows = list(paginate(c, "https://graph.microsoft.com/v1.0/users", {}))

    assert rows == [{"id": 1}, {"id": 2}]
    assert seen_urls[0] == "https://graph.microsoft.com/v1.0/users"
    assert seen_urls[1] == "https://graph.microsoft.com/v1.0/users?$skiptoken=next=2"
