"""Tests for the MsGraphClient facade."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import httpx
import pytest

from src.connectors._msgraph.client import MsGraphClient
from src.connectors._msgraph.endpoints import CloudEnvironment


@pytest.fixture(autouse=True)
def _patch_msal():
    """Replace MSAL so no network call is attempted for token acquisition."""
    with patch(
        "src.connectors._msgraph.auth.ConfidentialClientApplication"
    ) as cls:
        inst = MagicMock()
        inst.acquire_token_for_client.return_value = {"access_token": "FAKE_TOKEN"}
        cls.return_value = inst
        yield inst


@pytest.fixture(autouse=True)
def _no_real_sleep():
    with patch("src.connectors._msgraph.retry.time.sleep"):
        yield


def _make_client(handler) -> MsGraphClient:
    return MsGraphClient(
        tenant_id="tenant",
        client_id="client",
        client_secret="secret",
        cloud_env="commercial",
        transport=httpx.MockTransport(handler),
    )


def test_build_url_relative_path():
    c = MsGraphClient("t", "c", "s", "commercial",
                      transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})))
    assert c._build_url("/users") == "https://graph.microsoft.com/v1.0/users"
    assert c._build_url("users/$count") == "https://graph.microsoft.com/v1.0/users/$count"


def test_build_url_absolute_passes_through():
    c = MsGraphClient("t", "c", "s", "commercial",
                      transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})))
    nextlink = "https://graph.microsoft.com/v1.0/users?$skiptoken=abc"
    assert c._build_url(nextlink) == nextlink


def test_build_url_uses_cloud_specific_base():
    c_gov = MsGraphClient("t", "c", "s", "gcc_high",
                          transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})))
    assert c_gov._build_url("/users") == "https://graph.microsoft.us/v1.0/users"

    c_dod = MsGraphClient("t", "c", "s", "dod",
                          transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})))
    assert c_dod._build_url("/users") == "https://dod-graph.microsoft.us/v1.0/users"


def test_get_returns_parsed_json():
    seen_urls: list[str] = []
    seen_auth: list[str] = []

    def handler(req):
        seen_urls.append(str(req.url))
        seen_auth.append(req.headers.get("authorization", ""))
        return httpx.Response(200, json={"id": "abc", "displayName": "X"})

    with _make_client(handler) as c:
        body = c.get("/organization")

    assert body == {"id": "abc", "displayName": "X"}
    assert seen_urls[0] == "https://graph.microsoft.com/v1.0/organization"
    assert seen_auth[0] == "Bearer FAKE_TOKEN"


def test_paginate_yields_rows():
    pages = [
        {"value": [{"id": 1}], "@odata.nextLink": "https://graph.microsoft.com/v1.0/users?next"},
        {"value": [{"id": 2}, {"id": 3}]},
    ]
    state = {"i": 0}

    def handler(req):
        body = pages[state["i"]]
        state["i"] += 1
        return httpx.Response(200, json=body)

    with _make_client(handler) as c:
        rows = list(c.paginate("/users"))

    assert rows == [{"id": 1}, {"id": 2}, {"id": 3}]


def test_close_closes_underlying_client():
    c = _make_client(lambda r: httpx.Response(200, json={}))
    assert not c._http.is_closed
    c.close()
    assert c._http.is_closed


def test_context_manager():
    with _make_client(lambda r: httpx.Response(200, json={})) as c:
        assert not c._http.is_closed
    assert c._http.is_closed


def test_repr_does_not_leak_credentials():
    """The most basic credential-leak guard. See test_secret_hygiene.py for
    comprehensive coverage."""
    secret = "TEST_SECRET_SHOULD_NEVER_LEAK_repr_xyz789"
    tenant = "TEST_TENANT_ID_SHOULD_NEVER_LEAK"
    cid = "TEST_CLIENT_ID_SHOULD_NEVER_LEAK"
    c = MsGraphClient(
        tenant_id=tenant,
        client_id=cid,
        client_secret=secret,
        cloud_env="commercial",
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})),
    )
    r = repr(c)
    s = str(c)
    assert tenant not in r and tenant not in s
    assert cid not in r and cid not in s
    assert secret not in r and secret not in s


def test_consistency_level_header_is_set():
    """ConsistencyLevel: eventual is required for /users $count and $filter."""
    captured: dict = {}

    def handler(req):
        captured["headers"] = dict(req.headers)
        return httpx.Response(200, json={"value": []})

    with _make_client(handler) as c:
        c.get("/users")

    assert captured["headers"].get("consistencylevel") == "eventual"
