"""Integration smoke test for EntraIdConnector registration.

Pass E.3d — verifies the connector is properly registered with the framework
and that its metadata (credentials_schema, supported_controls, etc.) serializes
correctly through the registry.list_types() path used by /api/connectors/types.

This test uses NO mocks. It exercises the real registry decorator, the real
list_types() lookup, and the real schema serialization. It is the regression
bar for the registration chain.
"""

from __future__ import annotations

import json

import pytest

# Force the eager-import to fire by importing the package.
import src.connectors  # noqa: F401

from src.connectors.registry import list_types, get_connector_class
from src.connectors.connectors_builtin.entra_id import EntraIdConnector


class TestRegistration:
    """The connector is registered with the framework registry."""

    def test_entra_id_in_list_types(self):
        types = list_types()
        type_names = [t["type"] for t in types]
        assert "entra_id" in type_names

    def test_get_connector_class_returns_entra_id(self):
        cls = get_connector_class("entra_id")
        assert cls is EntraIdConnector

    def test_registry_includes_both_echo_and_entra_id(self):
        types = list_types()
        type_names = sorted(t["type"] for t in types)
        assert "echo" in type_names
        assert "entra_id" in type_names


class TestListTypesPayload:
    """The /api/connectors/types response payload shape for entra_id."""

    @pytest.fixture
    def entra_payload(self):
        types = list_types()
        return next(t for t in types if t["type"] == "entra_id")

    def test_type_field(self, entra_payload):
        assert entra_payload["type"] == "entra_id"

    def test_display_name_field(self, entra_payload):
        assert entra_payload["display_name"] == "Microsoft Entra ID"

    def test_supported_controls_field(self, entra_payload):
        assert entra_payload["supported_controls"] == [
            "AC.L2-3.1.1",
            "IA.L2-3.5.3",
            "AC.L2-3.1.5",
            "AU.L2-3.3.1",
            "AC.L2-3.1.20",
        ]

    def test_setup_component_field(self, entra_payload):
        assert entra_payload["setup_component"] is None

    def test_credentials_schema_has_four_fields(self, entra_payload):
        names = [f["name"] for f in entra_payload["credentials_schema"]]
        assert names == ["tenant_id", "client_id", "client_secret", "cloud_environment"]

    def test_credentials_schema_field_types(self, entra_payload):
        types_by_name = {f["name"]: f["type"]
                         for f in entra_payload["credentials_schema"]}
        assert types_by_name == {
            "tenant_id": "text",
            "client_id": "text",
            "client_secret": "password",
            "cloud_environment": "select",
        }

    def test_cloud_environment_options_present(self, entra_payload):
        cloud_field = next(
            f for f in entra_payload["credentials_schema"]
            if f["name"] == "cloud_environment"
        )
        values = [opt["value"] for opt in cloud_field["options"]]
        assert values == ["commercial", "gcc_high", "dod"]

    def test_payload_is_json_serializable(self, entra_payload):
        # The /api/connectors/types endpoint serializes this as JSON.
        # Confirm nothing in the payload breaks json.dumps.
        serialized = json.dumps(entra_payload)
        assert "entra_id" in serialized
        assert "Microsoft Entra ID" in serialized

    def test_help_text_present_on_every_field(self, entra_payload):
        for f in entra_payload["credentials_schema"]:
            assert f.get("help"), f"{f['name']} missing help text"


class TestSafeFailureWithFakeCredentials:
    """test_connection() with obviously-fake credentials returns (False, msg)
    cleanly — does not raise, does not hang, does not leak secrets in logs.

    This exercises the real auth path against Microsoft's login endpoint.
    Fake credentials produce a deterministic AADSTS error response; we
    verify the connector handles it gracefully.

    NOTE: This test makes a real HTTP call to login.microsoftonline.com
    (or .us, depending on cloud_environment). It is NOT a hermetic unit
    test. It is a smoke test for the full auth pipeline. If the test
    environment is offline, this test is expected to fail with a network
    error, NOT to be silently skipped.
    """

    def test_fake_credentials_return_false_not_raise(self):
        # Use commercial cloud — fastest auth endpoint, no GCC routing.
        # The tenant ID format is valid GUID; the credentials themselves
        # are obviously fake.
        connector = EntraIdConnector(
            config={},
            credentials={
                "tenant_id":      "00000000-0000-0000-0000-000000000000",
                "client_id":      "00000000-0000-0000-0000-000000000001",
                "client_secret":  "fake_secret_for_smoke_test_e3d",
                "cloud_environment": "commercial",
            },
        )

        ok, msg = connector.test_connection()

        # Per BaseConnector contract: never raises.
        # With fake credentials, must return (False, message).
        assert ok is False
        assert isinstance(msg, str)
        assert len(msg) > 0
        # The message should be human-readable, not a raw stack trace.
        # Common AADSTS codes for fake-tenant scenarios:
        #   AADSTS90002 — tenant not found
        #   AADSTS700016 — application not found in tenant
        # We don't assert on the specific code (it can vary by region/
        # endpoint); we assert the message is non-empty and doesn't
        # contain the secret.
        assert "fake_secret_for_smoke_test_e3d" not in msg
