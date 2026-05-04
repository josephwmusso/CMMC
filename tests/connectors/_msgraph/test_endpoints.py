"""Cloud environment URL mapping."""

from __future__ import annotations

import pytest

from src.connectors._msgraph.endpoints import (
    CloudEnvironment,
    get_authority_url,
    get_graph_base_url,
)


def test_authority_urls():
    assert get_authority_url(CloudEnvironment.COMMERCIAL, "T1") == \
        "https://login.microsoftonline.com/T1"
    assert get_authority_url(CloudEnvironment.GCC_HIGH, "T1") == \
        "https://login.microsoftonline.us/T1"
    assert get_authority_url(CloudEnvironment.DOD, "T1") == \
        "https://login.microsoftonline.us/T1"


def test_graph_base_urls():
    assert get_graph_base_url(CloudEnvironment.COMMERCIAL) == \
        "https://graph.microsoft.com"
    assert get_graph_base_url(CloudEnvironment.GCC_HIGH) == \
        "https://graph.microsoft.us"
    assert get_graph_base_url(CloudEnvironment.DOD) == \
        "https://dod-graph.microsoft.us"


def test_string_coercion():
    """Helpers accept either the enum or its string value."""
    assert get_graph_base_url("commercial") == "https://graph.microsoft.com"
    assert get_graph_base_url("gcc_high") == "https://graph.microsoft.us"
    assert get_authority_url("dod", "abc") == "https://login.microsoftonline.us/abc"


def test_invalid_string_raises():
    with pytest.raises(ValueError):
        get_graph_base_url("not_a_real_cloud")


def test_authority_composes_tenant_id():
    """Tenant ID is composed correctly into the path, not query."""
    url = get_authority_url(CloudEnvironment.COMMERCIAL, "00000000-0000-0000-0000-000000000000")
    assert url.endswith("/00000000-0000-0000-0000-000000000000")
    assert "?" not in url
