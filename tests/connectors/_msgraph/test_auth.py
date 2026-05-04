"""Tests for the MSAL TokenManager wrapper."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from src.connectors._msgraph.auth import TokenManager, AADSTS_MESSAGES, _scope_for
from src.connectors._msgraph.endpoints import CloudEnvironment
from src.connectors._msgraph.errors import MsGraphAuthError


@pytest.fixture
def _patch_msal():
    """Replace msal.ConfidentialClientApplication with a MagicMock so tests
    don't need network access. The mock instance is returned for assertion."""
    with patch(
        "src.connectors._msgraph.auth.ConfidentialClientApplication"
    ) as cls:
        instance = MagicMock()
        cls.return_value = instance
        yield instance


def test_get_token_success(_patch_msal):
    _patch_msal.acquire_token_for_client.return_value = {
        "access_token": "FAKE-TOKEN-VALUE",
        "expires_in": 3600,
    }
    mgr = TokenManager("tenant", "client", "secret", CloudEnvironment.COMMERCIAL)
    assert mgr.get_token() == "FAKE-TOKEN-VALUE"


def test_get_token_aadsts7000222_humanized(_patch_msal):
    _patch_msal.acquire_token_for_client.return_value = {
        "error": "invalid_client",
        "error_description": "AADSTS7000222: The provided client secret keys for app are expired.",
    }
    mgr = TokenManager("tenant", "client", "secret", CloudEnvironment.COMMERCIAL)
    with pytest.raises(MsGraphAuthError) as exc_info:
        mgr.get_token()
    assert exc_info.value.aadsts_code == "AADSTS7000222"
    assert "expired" in str(exc_info.value).lower()


def test_get_token_aadsts90002_humanized(_patch_msal):
    _patch_msal.acquire_token_for_client.return_value = {
        "error": "invalid_request",
        "error_description": "AADSTS90002: Tenant 'X' not found.",
    }
    mgr = TokenManager("tenant", "client", "secret", CloudEnvironment.COMMERCIAL)
    with pytest.raises(MsGraphAuthError) as exc_info:
        mgr.get_token()
    assert exc_info.value.aadsts_code == "AADSTS90002"
    assert "Tenant ID" in str(exc_info.value)


def test_get_token_unknown_aadsts_passes_through_raw(_patch_msal):
    _patch_msal.acquire_token_for_client.return_value = {
        "error": "invalid_grant",
        "error_description": "AADSTS99999: Some new code we don't recognize.",
    }
    mgr = TokenManager("tenant", "client", "secret", CloudEnvironment.COMMERCIAL)
    with pytest.raises(MsGraphAuthError) as exc_info:
        mgr.get_token()
    assert exc_info.value.aadsts_code is None
    assert "AADSTS99999" in str(exc_info.value)


def test_repr_does_not_contain_secret(_patch_msal):
    secret = "TEST_SECRET_SHOULD_NEVER_LEAK_repr_abc123"
    mgr = TokenManager("t", "c", secret, CloudEnvironment.COMMERCIAL)
    assert secret not in repr(mgr)
    assert secret not in str(mgr)


def test_scope_per_cloud():
    assert _scope_for(CloudEnvironment.COMMERCIAL) == "https://graph.microsoft.com/.default"
    assert _scope_for(CloudEnvironment.GCC_HIGH)   == "https://graph.microsoft.us/.default"
    assert _scope_for(CloudEnvironment.DOD)        == "https://dod-graph.microsoft.us/.default"


def test_token_manager_uses_correct_scope(_patch_msal):
    _patch_msal.acquire_token_for_client.return_value = {"access_token": "x"}
    mgr = TokenManager("t", "c", "s", CloudEnvironment.GCC_HIGH)
    mgr.get_token()
    _patch_msal.acquire_token_for_client.assert_called_once_with(
        scopes=["https://graph.microsoft.us/.default"]
    )


def test_aadsts_messages_dict_has_all_required_codes():
    """The five codes the discovery report committed to handling."""
    for code in ("AADSTS7000222", "AADSTS7000215", "AADSTS90002",
                 "AADSTS700016", "AADSTS50194"):
        assert code in AADSTS_MESSAGES
