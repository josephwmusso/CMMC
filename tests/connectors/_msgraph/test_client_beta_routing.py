"""Tests for MsGraphClient._build_url's /beta/ branch — added in F.3b.

The branch supports endpoints that don't exist in v1.0 (notably
/beta/security/informationProtection/sensitivityLabels). It uses
startswith('/beta/') for matching — defensive tests below confirm only
path-leading /beta/ routes as beta; embedded /beta/ segments do not.

This file is new in F.3b. Existing _msgraph/test_client.py tests are
untouched.
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest

from src.connectors._msgraph.client import MsGraphClient


@pytest.fixture(autouse=True)
def _patch_msal():
    """Replace MSAL so construction doesn't try to acquire a token."""
    with patch(
        "src.connectors._msgraph.auth.ConfidentialClientApplication"
    ) as cls:
        from unittest.mock import MagicMock
        inst = MagicMock()
        inst.acquire_token_for_client.return_value = {"access_token": "FAKE_TOKEN"}
        cls.return_value = inst
        yield inst


def _make_client(cloud_env: str = "commercial") -> MsGraphClient:
    """A real MsGraphClient with a mocked transport (no network)."""
    return MsGraphClient(
        tenant_id="tenant",
        client_id="client",
        client_secret="secret",
        cloud_env=cloud_env,
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={})
        ),
    )


class TestBetaPathRoutesToBeta:
    """Paths starting with /beta/ anchor at the cloud base URL WITHOUT
    the /v1.0/ prefix (the beta version is already in the path)."""

    def test_beta_path_routes_to_beta(self):
        c = _make_client()
        url = c._build_url("/beta/security/informationProtection/sensitivityLabels")
        assert url == (
            "https://graph.microsoft.com/beta/security/"
            "informationProtection/sensitivityLabels"
        )
        c.close()

    def test_beta_path_with_query_string(self):
        c = _make_client()
        url = c._build_url("/beta/security/labels?$top=10")
        assert url == "https://graph.microsoft.com/beta/security/labels?$top=10"
        c.close()


class TestBetaPathDoesNotRouteWhenNotAtStart:
    """Defensive: only path-LEADING /beta/ routes as beta. startswith()
    matching enforces this precisely. F.3b Phase 2 design requirement.
    """

    def test_embedded_beta_segment_does_not_route_as_beta(self):
        """A path like /foo/beta/bar should anchor at /v1.0 like any other
        relative path — the embedded /beta/ segment is just part of the
        resource name, not a routing signal."""
        c = _make_client()
        url = c._build_url("/foo/beta/bar")
        assert url == "https://graph.microsoft.com/v1.0/foo/beta/bar"
        c.close()

    def test_path_with_beta_substring_in_resource_name(self):
        """Even more adversarial: a resource literally named 'beta' deep
        in the path. Still v1.0."""
        c = _make_client()
        url = c._build_url("/users/some-beta-tester-id/messages")
        assert url == (
            "https://graph.microsoft.com/v1.0/users/"
            "some-beta-tester-id/messages"
        )
        c.close()

    def test_path_starting_with_beta_no_trailing_slash(self):
        """/beta is NOT /beta/ — without the trailing slash,
        startswith('/beta/') is False. Falls through to /v1.0. The
        resulting /v1.0/beta is a nonsense URL that Graph will 404 —
        which is the right behavior, surface the typo rather than
        silently rerouting."""
        c = _make_client()
        url = c._build_url("/beta")
        assert url == "https://graph.microsoft.com/v1.0/beta"
        c.close()


class TestBetaPathHonorsCloudEnvironment:
    """The cloud-specific base URL is honored on the /beta/ branch too."""

    def test_gcc_high_beta_path(self):
        c = _make_client(cloud_env="gcc_high")
        url = c._build_url("/beta/security/labels")
        assert url == "https://graph.microsoft.us/beta/security/labels"
        c.close()

    def test_dod_beta_path(self):
        c = _make_client(cloud_env="dod")
        url = c._build_url("/beta/security/labels")
        assert url == "https://dod-graph.microsoft.us/beta/security/labels"
        c.close()


class TestExistingV1BehaviorUnchanged:
    """Regression bar: F.3b's beta branch must not affect existing
    /v1.0 routing. These assertions duplicate test_client.py's coverage
    intentionally — local regression bar, not a replacement."""

    def test_v1_relative_with_leading_slash_unchanged(self):
        c = _make_client()
        assert c._build_url("/users") == "https://graph.microsoft.com/v1.0/users"
        c.close()

    def test_v1_relative_without_leading_slash_unchanged(self):
        c = _make_client()
        assert c._build_url("users") == "https://graph.microsoft.com/v1.0/users"
        c.close()

    def test_absolute_url_passes_through_unchanged(self):
        c = _make_client()
        nl = "https://graph.microsoft.com/v1.0/users?$skiptoken=abc"
        assert c._build_url(nl) == nl
        c.close()
