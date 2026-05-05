"""Unit tests for M365GccHighConnector — F.2 skeleton + F.3a control pulls.

Mirrors test_entra_id.py's structural test surface. F.3a replaces F.2's
TestPullStubbed class with four new classes covering the live pulls for
MP.L2-3.8.1, MP.L2-3.8.2, AC.L2-3.1.3 (partial), and the orchestrator's
per-control isolation. F.3b/c add classes for SC.L2-3.13.8 and AU.L2-3.3.1.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.connectors.connectors_builtin.m365_gcc_high import M365GccHighConnector
from src.connectors._msgraph.errors import (
    MsGraphAuthError,
    MsGraphCapabilityError,
    MsGraphError,
    MsGraphPermissionError,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "m365_gcc_high"


def load_fixture(name: str) -> dict:
    """Load a fixture JSON by control name (e.g. 'mp_3_8_1')."""
    return json.loads((FIXTURE_DIR / f"{name}.json").read_text(encoding="utf-8"))


def make_mock_client(get_responses: dict, paginate_responses: dict) -> MagicMock:
    """Build a MagicMock MsGraphClient that returns fixture data.

    get_responses: maps endpoint substring -> return value (single dict).
    paginate_responses: maps endpoint substring -> list of dicts.
    """
    client = MagicMock()
    client.__enter__.return_value = client
    client.__exit__.return_value = None

    def get_side_effect(path):
        for key, value in get_responses.items():
            if key in path:
                return value
        raise KeyError(f"no get fixture matched path: {path}")

    def paginate_side_effect(path):
        for key, value in paginate_responses.items():
            if key in path:
                return iter(value)
        raise KeyError(f"no paginate fixture matched path: {path}")

    client.get.side_effect = get_side_effect
    client.paginate.side_effect = paginate_side_effect
    return client


FIXED_NOW = datetime(2026, 5, 4, 12, 0, 0, tzinfo=timezone.utc)


VALID_CREDS = {
    "tenant_id": "00000000-1111-2222-3333-444444444444",
    "client_id": "55555555-6666-7777-8888-999999999999",
    "client_secret": "TEST_F2_SECRET_DO_NOT_LEAK_abc123",
    "cloud_environment": "gcc_high",
}

VALID_CONFIG: dict = {}


@pytest.fixture
def connector():
    return M365GccHighConnector(config=VALID_CONFIG, credentials=VALID_CREDS)


# ──────────────────────────────────────────────────────────────────────
# A. Class shape / static attributes (no I/O)
# ──────────────────────────────────────────────────────────────────────

class TestClassShape:

    def test_type_name_is_m365_gcc_high(self):
        assert M365GccHighConnector.type_name == "m365_gcc_high"

    def test_display_name(self):
        assert M365GccHighConnector.display_name == "Microsoft 365 (GCC High)"

    def test_supported_controls(self):
        assert M365GccHighConnector.supported_controls == [
            "AC.L2-3.1.3",
            "SC.L2-3.13.8",
            "MP.L2-3.8.1",
            "MP.L2-3.8.2",
            "AU.L2-3.3.1",
        ]

    def test_setup_component_is_none(self):
        assert M365GccHighConnector.setup_component is None

    def test_credentials_schema_has_four_fields(self):
        names = [f["name"] for f in M365GccHighConnector.credentials_schema]
        assert names == [
            "tenant_id",
            "client_id",
            "client_secret",
            "cloud_environment",
        ]

    def test_credentials_schema_field_types(self):
        types_by_name = {
            f["name"]: f["type"]
            for f in M365GccHighConnector.credentials_schema
        }
        assert types_by_name == {
            "tenant_id": "text",
            "client_id": "text",
            "client_secret": "password",
            "cloud_environment": "select",
        }

    def test_all_credentials_required(self):
        for f in M365GccHighConnector.credentials_schema:
            assert f["required"] is True, f"{f['name']} should be required"

    def test_cloud_environment_options(self):
        cloud_field = next(
            f for f in M365GccHighConnector.credentials_schema
            if f["name"] == "cloud_environment"
        )
        values = [opt["value"] for opt in cloud_field["options"]]
        assert values == ["commercial", "gcc_high", "dod"]

    def test_help_text_present_on_every_field(self):
        for f in M365GccHighConnector.credentials_schema:
            assert f.get("help"), f"{f['name']} missing help text"

    def test_help_text_no_mojibake_bytes(self):
        """Regression: help strings must not contain mojibake byte sequences
        from cp1252-misinterpreted UTF-8 (the bug surfaced during Pass E.3d
        production verification).
        """
        # Known mojibake patterns from cp1252 misinterpretation of common
        # UTF-8 sequences. These bytes appear when the writer's host shell
        # uses cp1252 but emits to a UTF-8-expecting consumer.
        MOJIBAKE_PATTERNS = [
            "â†",   # \xe2\x86 prefix as cp1252-mojibake (e.g. arrows)
            "â€",   # \xe2\x80 prefix as cp1252-mojibake (dashes/quotes)
            "Ã¢",   # double-encoded UTF-8 prefix
        ]
        for field in M365GccHighConnector.credentials_schema:
            help_text = field.get("help", "")
            for pattern in MOJIBAKE_PATTERNS:
                assert pattern not in help_text, (
                    f"mojibake byte sequence {pattern!r} found in "
                    f"{field['name']}.help: {help_text!r}"
                )


# ──────────────────────────────────────────────────────────────────────
# B. __init__ behavior (no I/O)
# ──────────────────────────────────────────────────────────────────────

class TestInit:

    def test_init_with_valid_creds(self, connector):
        assert connector._tenant_id == VALID_CREDS["tenant_id"]
        assert connector._client_id == VALID_CREDS["client_id"]
        assert connector._client_secret == VALID_CREDS["client_secret"]
        assert connector._cloud_env == "gcc_high"

    def test_init_strips_whitespace_from_tenant_and_client_id(self):
        creds = {
            **VALID_CREDS,
            "tenant_id": f"  {VALID_CREDS['tenant_id']}  ",
            "client_id": f"\t{VALID_CREDS['client_id']}\n",
        }
        c = M365GccHighConnector(config={}, credentials=creds)
        assert c._tenant_id == VALID_CREDS["tenant_id"]
        assert c._client_id == VALID_CREDS["client_id"]

    def test_init_does_not_strip_client_secret(self):
        # Principle: don't mutate secrets. The form trims on submit.
        # If the secret arrives with whitespace, that's the form's bug.
        creds = {**VALID_CREDS, "client_secret": "  spaced_secret  "}
        c = M365GccHighConnector(config={}, credentials=creds)
        assert c._client_secret == "  spaced_secret  "

    def test_init_default_cloud_environment(self):
        creds = {
            k: v for k, v in VALID_CREDS.items()
            if k != "cloud_environment"
        }
        c = M365GccHighConnector(config={}, credentials=creds)
        assert c._cloud_env == "commercial"

    def test_init_missing_required_field_raises_keyerror(self):
        creds = {k: v for k, v in VALID_CREDS.items() if k != "tenant_id"}
        with pytest.raises(KeyError):
            M365GccHighConnector(config={}, credentials=creds)


# ──────────────────────────────────────────────────────────────────────
# B'. lookback_hours config (mirrors Pass E.3a)
# ──────────────────────────────────────────────────────────────────────

class TestLookbackHoursConfig:
    """The _clamp_lookback_hours helper is copied verbatim from
    EntraIdConnector. F.3c's AU.L2-3.3.1 audit-log window depends on it.
    Tests on a class-method helper aren't redundant with Entra's tests
    even if the body is identical — divergence in F.2's copy wouldn't
    be caught by Entra's tests because they exercise EntraIdConnector,
    not M365GccHighConnector.
    """

    def test_default_when_config_empty(self):
        c = M365GccHighConnector(config={}, credentials=VALID_CREDS)
        assert c._lookback_hours == 24

    def test_default_when_key_absent(self):
        c = M365GccHighConnector(
            config={"other_key": "value"},
            credentials=VALID_CREDS,
        )
        assert c._lookback_hours == 24

    def test_valid_int_pass_through(self):
        c = M365GccHighConnector(
            config={"lookback_hours": 48},
            credentials=VALID_CREDS,
        )
        assert c._lookback_hours == 48

    def test_minimum_value_one_hour(self):
        c = M365GccHighConnector(
            config={"lookback_hours": 1},
            credentials=VALID_CREDS,
        )
        assert c._lookback_hours == 1

    def test_maximum_value_one_week(self):
        c = M365GccHighConnector(
            config={"lookback_hours": 168},
            credentials=VALID_CREDS,
        )
        assert c._lookback_hours == 168

    def test_below_minimum_clamps_to_one(self, caplog):
        with caplog.at_level(logging.WARNING):
            c = M365GccHighConnector(
                config={"lookback_hours": 0},
                credentials=VALID_CREDS,
            )
        assert c._lookback_hours == 1
        assert any("below minimum" in r.getMessage() for r in caplog.records)

    def test_negative_clamps_to_one(self, caplog):
        with caplog.at_level(logging.WARNING):
            c = M365GccHighConnector(
                config={"lookback_hours": -50},
                credentials=VALID_CREDS,
            )
        assert c._lookback_hours == 1
        assert any("below minimum" in r.getMessage() for r in caplog.records)

    def test_above_maximum_clamps_to_168(self, caplog):
        with caplog.at_level(logging.WARNING):
            c = M365GccHighConnector(
                config={"lookback_hours": 8760},
                credentials=VALID_CREDS,
            )
        assert c._lookback_hours == 168
        assert any("above maximum" in r.getMessage() for r in caplog.records)

    def test_string_int_coerced(self):
        c = M365GccHighConnector(
            config={"lookback_hours": "72"},
            credentials=VALID_CREDS,
        )
        assert c._lookback_hours == 72

    def test_float_truncated(self):
        # int(48.7) == 48. Document the behavior; don't pretend we round.
        c = M365GccHighConnector(
            config={"lookback_hours": 48.7},
            credentials=VALID_CREDS,
        )
        assert c._lookback_hours == 48

    def test_garbage_string_falls_back_to_default(self, caplog):
        with caplog.at_level(logging.WARNING):
            c = M365GccHighConnector(
                config={"lookback_hours": "not a number"},
                credentials=VALID_CREDS,
            )
        assert c._lookback_hours == 24
        assert any(
            "not coercible" in r.getMessage() for r in caplog.records
        )

    def test_none_falls_back_to_default(self, caplog):
        with caplog.at_level(logging.WARNING):
            c = M365GccHighConnector(
                config={"lookback_hours": None},
                credentials=VALID_CREDS,
            )
        assert c._lookback_hours == 24
        assert any(
            "not coercible" in r.getMessage() for r in caplog.records
        )


# ──────────────────────────────────────────────────────────────────────
# C. test_connection() success and failure paths
# ──────────────────────────────────────────────────────────────────────

class TestTestConnection:

    @patch("src.connectors.connectors_builtin.m365_gcc_high.MsGraphClient")
    def test_success_returns_true_with_tenant_name(
        self, mock_client_class, connector
    ):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.get.return_value = {
            "value": [{
                "id": "00000000-aaaa-bbbb-cccc-dddddddddddd",
                "displayName": "Apex Defense Solutions",
                "tenantType": "AAD",
            }]
        }
        mock_client_class.return_value = mock_client

        ok, msg = connector.test_connection()

        assert ok is True
        assert "Apex Defense Solutions" in msg
        assert "AAD" in msg
        # Confirm the canary endpoint is what we expect.
        mock_client.get.assert_called_once()
        call_arg = mock_client.get.call_args[0][0]
        assert "/organization" in call_arg
        assert "$select=" in call_arg

    @patch("src.connectors.connectors_builtin.m365_gcc_high.MsGraphClient")
    def test_empty_organization_response(
        self, mock_client_class, connector
    ):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.get.return_value = {"value": []}
        mock_client_class.return_value = mock_client

        ok, msg = connector.test_connection()

        assert ok is False
        assert "no rows" in msg.lower()

    @patch("src.connectors.connectors_builtin.m365_gcc_high.MsGraphClient")
    def test_auth_error_invalid_secret(
        self, mock_client_class, connector
    ):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.get.side_effect = MsGraphAuthError(
            "Client secret has expired or is invalid. Generate a new secret...",
            aadsts_code="AADSTS7000222",
        )
        mock_client_class.return_value = mock_client

        ok, msg = connector.test_connection()

        assert ok is False
        assert "Client secret" in msg

    @patch("src.connectors.connectors_builtin.m365_gcc_high.MsGraphClient")
    def test_auth_error_tenant_not_found(
        self, mock_client_class, connector
    ):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.get.side_effect = MsGraphAuthError(
            "Tenant not found. Verify the Tenant ID matches your Entra "
            "admin center...",
            aadsts_code="AADSTS90002",
        )
        mock_client_class.return_value = mock_client

        ok, msg = connector.test_connection()

        assert ok is False
        assert "Tenant not found" in msg

    @patch("src.connectors.connectors_builtin.m365_gcc_high.MsGraphClient")
    def test_permission_error_with_named_permission(
        self, mock_client_class, connector
    ):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.get.side_effect = MsGraphPermissionError(
            "Missing permission: Directory.Read.All",
            missing_permission="Directory.Read.All",
            endpoint="https://graph.microsoft.us/v1.0/organization",
        )
        mock_client_class.return_value = mock_client

        ok, msg = connector.test_connection()

        assert ok is False
        assert "Directory.Read.All" in msg
        assert "API permissions" in msg
        assert "admin consent" in msg

    @patch("src.connectors.connectors_builtin.m365_gcc_high.MsGraphClient")
    def test_permission_error_without_named_permission(
        self, mock_client_class, connector
    ):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.get.side_effect = MsGraphPermissionError(
            "403 Forbidden on /organization",
        )
        mock_client_class.return_value = mock_client

        ok, msg = connector.test_connection()

        assert ok is False
        assert "403" in msg

    @patch("src.connectors.connectors_builtin.m365_gcc_high.MsGraphClient")
    def test_generic_msgraph_error(
        self, mock_client_class, connector
    ):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.get.side_effect = MsGraphError("Unexpected Graph response")
        mock_client_class.return_value = mock_client

        ok, msg = connector.test_connection()

        assert ok is False
        assert "Microsoft Graph error" in msg

    @patch("src.connectors.connectors_builtin.m365_gcc_high.MsGraphClient")
    def test_unexpected_exception_does_not_propagate(
        self, mock_client_class, connector
    ):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.get.side_effect = RuntimeError("totally unexpected")
        mock_client_class.return_value = mock_client

        # BaseConnector contract: test_connection MUST NOT raise.
        ok, msg = connector.test_connection()

        assert ok is False
        assert "Unexpected error" in msg
        assert "RuntimeError" in msg


# ──────────────────────────────────────────────────────────────────────
# D. _pull_mp_3_8_1() — Media Protection (digital): SharePoint, retention,
#    Intune (license-conditional)
# ──────────────────────────────────────────────────────────────────────

class TestPullMP381:
    """MP.L2-3.8.1 — three Graph endpoints; Intune call is license-
    conditional and emits degraded evidence when unlicensed.
    """

    def _setup(self, connector):
        connector._now = lambda: FIXED_NOW
        fx = load_fixture("mp_3_8_1")
        client = make_mock_client(
            get_responses={
                "/admin/sharepoint/settings": fx["sharepoint_settings"],
            },
            paginate_responses={
                "/security/labels/retentionLabels": fx["retention_labels"],
                "/deviceManagement/deviceCompliancePolicies": fx[
                    "intune_compliance_policies"
                ],
            },
        )
        return connector, client, fx

    def test_returns_pulled_evidence(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_mp_3_8_1(client)
        assert ev is not None
        assert ev.control_ids == ["MP.L2-3.8.1"]

    def test_filename_includes_timestamp(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_mp_3_8_1(client)
        assert ev.filename.startswith("m365_mp_3_8_1_")
        assert ev.filename.endswith(".json")
        assert "2026-05-04" in ev.filename

    def test_content_includes_all_three_sub_components(self, connector):
        c, client, fx = self._setup(connector)
        ev = c._pull_mp_3_8_1(client)
        parsed = json.loads(ev.content.decode("utf-8"))
        assert parsed["sharepoint_settings"] == fx["sharepoint_settings"]
        assert parsed["retention_labels"] == fx["retention_labels"]
        assert parsed["intune_compliance_policies"] == fx[
            "intune_compliance_policies"
        ]
        assert parsed["fetched_at"] == FIXED_NOW.isoformat()

    def test_metadata_media_scope_is_digital(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_mp_3_8_1(client)
        assert ev.metadata["media_scope"] == "digital"

    def test_metadata_endpoints_listed(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_mp_3_8_1(client)
        assert ev.metadata["endpoints"] == [
            "/admin/sharepoint/settings",
            "/security/labels/retentionLabels",
            "/deviceManagement/deviceCompliancePolicies",
        ]

    def test_metadata_counts(self, connector):
        c, client, fx = self._setup(connector)
        ev = c._pull_mp_3_8_1(client)
        assert ev.metadata["retention_label_count"] == len(fx["retention_labels"])
        assert ev.metadata["intune_policy_count"] == len(
            fx["intune_compliance_policies"]
        )

    def test_intune_status_ok_on_happy_path(self, connector):
        """Closed-set value: 'ok' when Intune call succeeded."""
        c, client, _ = self._setup(connector)
        ev = c._pull_mp_3_8_1(client)
        assert ev.metadata["intune_status"] == "ok"
        assert ev.degraded is False
        assert ev.degradation_reason is None

    def test_sharepoint_status_ok_on_happy_path(self, connector):
        """Closed-set value: 'ok' when SharePoint call succeeded."""
        c, client, _ = self._setup(connector)
        ev = c._pull_mp_3_8_1(client)
        assert ev.metadata["sharepoint_status"] == "ok"

    def test_intune_403_with_licensing_signal_emits_degraded(self, connector):
        """The F.1 contract: Forbidden_LicensingError → licensing_signal=True
        → connector emits degraded evidence rather than failing."""
        c = connector
        c._now = lambda: FIXED_NOW
        fx = load_fixture("mp_3_8_1")

        def paginate_side_effect(path):
            if "/security/labels/retentionLabels" in path:
                return iter(fx["retention_labels"])
            if "/deviceManagement/deviceCompliancePolicies" in path:
                raise MsGraphPermissionError(
                    "Tenant requires Microsoft Intune license.",
                    missing_permission=None,
                    endpoint="/deviceManagement/deviceCompliancePolicies",
                    licensing_signal=True,
                )
            raise KeyError(f"unmatched paginate: {path}")

        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None
        client.get.side_effect = lambda p: fx["sharepoint_settings"]
        client.paginate.side_effect = paginate_side_effect

        ev = c._pull_mp_3_8_1(client)

        assert ev is not None
        assert ev.degraded is True
        assert ev.degradation_reason == "Intune license not detected on tenant"
        assert ev.metadata["intune_status"] == "license_not_detected"
        assert ev.metadata["intune_policy_count"] == 0
        # Other sub-components still present.
        parsed = json.loads(ev.content.decode("utf-8"))
        assert parsed["sharepoint_settings"] == fx["sharepoint_settings"]
        assert parsed["retention_labels"] == fx["retention_labels"]
        assert parsed["intune_compliance_policies"] == []

    def test_intune_403_without_licensing_signal_propagates(self, connector):
        """Non-licensing 403 (e.g. plain permission missing) should propagate
        to the orchestrator's per-control isolator, not be swallowed as
        degradation."""
        c = connector
        c._now = lambda: FIXED_NOW
        fx = load_fixture("mp_3_8_1")

        def paginate_side_effect(path):
            if "/security/labels/retentionLabels" in path:
                return iter(fx["retention_labels"])
            if "/deviceManagement/deviceCompliancePolicies" in path:
                raise MsGraphPermissionError(
                    "Missing permission: DeviceManagementConfiguration.Read.All",
                    missing_permission="DeviceManagementConfiguration.Read.All",
                    endpoint="/deviceManagement/deviceCompliancePolicies",
                    licensing_signal=False,
                )
            raise KeyError(f"unmatched paginate: {path}")

        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None
        client.get.side_effect = lambda p: fx["sharepoint_settings"]
        client.paginate.side_effect = paginate_side_effect

        with pytest.raises(MsGraphPermissionError) as exc_info:
            c._pull_mp_3_8_1(client)
        assert exc_info.value.licensing_signal is False
        assert exc_info.value.missing_permission == (
            "DeviceManagementConfiguration.Read.All"
        )

    def test_uses_get_for_singleton_sharepoint_settings(self, connector):
        """sharepoint_settings is a singleton; must use client.get(), not
        client.paginate() (would attempt to read .value array)."""
        c, client, _ = self._setup(connector)
        c._pull_mp_3_8_1(client)
        get_calls = [call.args[0] for call in client.get.call_args_list]
        assert any("/admin/sharepoint/settings" in p for p in get_calls)

    def test_uses_paginate_for_retention_and_intune(self, connector):
        c, client, _ = self._setup(connector)
        c._pull_mp_3_8_1(client)
        paginate_calls = [c.args[0] for c in client.paginate.call_args_list]
        assert any("/security/labels/retentionLabels" in p for p in paginate_calls)
        assert any(
            "/deviceManagement/deviceCompliancePolicies" in p
            for p in paginate_calls
        )

    def test_intune_400_capability_gap_emits_degraded(self, connector):
        """F.3a framework amendment: 400 + BadRequest + 'not applicable' on
        Intune endpoint → MsGraphCapabilityError → intune_status =
        'service_unavailable' on the parent PE."""
        c = connector
        c._now = lambda: FIXED_NOW
        fx = load_fixture("mp_3_8_1")

        def paginate_side_effect(path):
            if "/security/labels/retentionLabels" in path:
                return iter(fx["retention_labels"])
            if "/deviceManagement/deviceCompliancePolicies" in path:
                raise MsGraphCapabilityError(
                    "Capability gap on /deviceManagement/...: "
                    "Request not applicable to target tenant.",
                    endpoint="/deviceManagement/deviceCompliancePolicies",
                )
            raise KeyError(f"unmatched paginate: {path}")

        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None
        client.get.side_effect = lambda p: fx["sharepoint_settings"]
        client.paginate.side_effect = paginate_side_effect

        ev = c._pull_mp_3_8_1(client)

        assert ev is not None
        assert ev.metadata["intune_status"] == "service_unavailable"
        assert ev.metadata["intune_policy_count"] == 0
        assert ev.degraded is True
        assert "Intune service unavailable" in (ev.degradation_reason or "")
        # SharePoint sub-component is fine.
        assert ev.metadata["sharepoint_status"] == "ok"

    def test_sharepoint_400_capability_gap_emits_degraded(self, connector):
        """F.3a framework amendment: 400 + BadRequest + 'does not have' on
        SharePoint endpoint → MsGraphCapabilityError → sharepoint_status =
        'service_unavailable' on the parent PE."""
        c = connector
        c._now = lambda: FIXED_NOW
        fx = load_fixture("mp_3_8_1")

        def get_side_effect(path):
            if "/admin/sharepoint/settings" in path:
                raise MsGraphCapabilityError(
                    "Capability gap on /admin/sharepoint/settings: "
                    "Tenant does not have a SPO license.",
                    endpoint="/admin/sharepoint/settings",
                )
            raise KeyError(f"unmatched get: {path}")

        def paginate_side_effect(path):
            if "/security/labels/retentionLabels" in path:
                return iter(fx["retention_labels"])
            if "/deviceManagement/deviceCompliancePolicies" in path:
                return iter(fx["intune_compliance_policies"])
            raise KeyError(f"unmatched paginate: {path}")

        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None
        client.get.side_effect = get_side_effect
        client.paginate.side_effect = paginate_side_effect

        ev = c._pull_mp_3_8_1(client)

        assert ev is not None
        assert ev.metadata["sharepoint_status"] == "service_unavailable"
        assert ev.degraded is True
        assert "SharePoint Online unavailable" in (ev.degradation_reason or "")
        # Intune still ok in this scenario.
        assert ev.metadata["intune_status"] == "ok"
        # Content reflects the degraded sub-component.
        parsed = json.loads(ev.content.decode("utf-8"))
        assert parsed["sharepoint_settings"] is None
        assert parsed["sharepoint_status"] == "service_unavailable"

    def test_both_sharepoint_and_intune_degrade_combined_reason(self, connector):
        """Trial-tenant scenario: both SharePoint and Intune are unprovisioned.
        Both sub-components flag degraded; degradation_reason combines both."""
        c = connector
        c._now = lambda: FIXED_NOW
        fx = load_fixture("mp_3_8_1")

        def get_side_effect(path):
            raise MsGraphCapabilityError(
                "Capability gap on /admin/sharepoint/settings: "
                "Tenant does not have a SPO license.",
                endpoint="/admin/sharepoint/settings",
            )

        def paginate_side_effect(path):
            if "/security/labels/retentionLabels" in path:
                return iter(fx["retention_labels"])
            if "/deviceManagement/deviceCompliancePolicies" in path:
                raise MsGraphCapabilityError(
                    "Capability gap on /deviceManagement/...: "
                    "Request not applicable to target tenant.",
                    endpoint="/deviceManagement/deviceCompliancePolicies",
                )
            raise KeyError(f"unmatched: {path}")

        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None
        client.get.side_effect = get_side_effect
        client.paginate.side_effect = paginate_side_effect

        ev = c._pull_mp_3_8_1(client)

        assert ev is not None
        assert ev.degraded is True
        assert ev.metadata["sharepoint_status"] == "service_unavailable"
        assert ev.metadata["intune_status"] == "service_unavailable"
        assert "SharePoint Online unavailable" in (ev.degradation_reason or "")
        assert "Intune service unavailable" in (ev.degradation_reason or "")
        # Retention labels still pulled successfully.
        parsed = json.loads(ev.content.decode("utf-8"))
        assert parsed["retention_labels"] == fx["retention_labels"]


# ──────────────────────────────────────────────────────────────────────
# E. _pull_mp_3_8_2() — Media Access (digital): SharePoint + CA;
#    coverage_scope=partial because per-site sharingCapability isn't in
#    Graph v1.0
# ──────────────────────────────────────────────────────────────────────

class TestPullMP382:
    """MP.L2-3.8.2 — partial coverage on the per-site dimension."""

    def _setup(self, connector):
        connector._now = lambda: FIXED_NOW
        fx = load_fixture("mp_3_8_2")
        client = make_mock_client(
            get_responses={
                "/admin/sharepoint/settings": fx["sharepoint_settings"],
            },
            paginate_responses={
                "/identity/conditionalAccess/policies": fx[
                    "conditional_access_policies"
                ],
            },
        )
        return connector, client, fx

    def test_returns_pulled_evidence(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_mp_3_8_2(client)
        assert ev is not None
        assert ev.control_ids == ["MP.L2-3.8.2"]

    def test_coverage_scope_is_partial(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_mp_3_8_2(client)
        assert ev.coverage_scope == "partial"

    def test_missing_sources_lists_per_site_sharing(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_mp_3_8_2(client)
        assert ev.missing_sources == ["per_site_sharing"]

    def test_metadata_media_scope_is_digital(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_mp_3_8_2(client)
        assert ev.metadata["media_scope"] == "digital"

    def test_content_includes_sharepoint_and_ca(self, connector):
        c, client, fx = self._setup(connector)
        ev = c._pull_mp_3_8_2(client)
        parsed = json.loads(ev.content.decode("utf-8"))
        assert parsed["sharepoint_settings"] == fx["sharepoint_settings"]
        assert parsed["conditional_access_policies"] == fx[
            "conditional_access_policies"
        ]

    def test_metadata_endpoints_listed(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_mp_3_8_2(client)
        assert ev.metadata["endpoints"] == [
            "/admin/sharepoint/settings",
            "/identity/conditionalAccess/policies",
        ]

    def test_metadata_ca_policy_count(self, connector):
        c, client, fx = self._setup(connector)
        ev = c._pull_mp_3_8_2(client)
        assert ev.metadata["ca_policy_count"] == len(
            fx["conditional_access_policies"]
        )

    def test_calls_sharepoint_settings_independently_from_mp_3_8_1(
        self, connector
    ):
        """Per-control isolation contract: each control calls its endpoints
        independently. No shared-state caching of sharepoint_settings between
        MP.L2-3.8.1 and MP.L2-3.8.2."""
        c, client, _ = self._setup(connector)
        c._pull_mp_3_8_2(client)
        get_calls = [call.args[0] for call in client.get.call_args_list]
        assert any("/admin/sharepoint/settings" in p for p in get_calls)

    def test_sharepoint_status_ok_on_happy_path(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_mp_3_8_2(client)
        assert ev.metadata["sharepoint_status"] == "ok"
        assert ev.degraded is False

    def test_sharepoint_400_capability_gap_emits_degraded(self, connector):
        """F.3a framework amendment: 400 + BadRequest + 'does not have' on
        SharePoint → MsGraphCapabilityError → sharepoint_status =
        'service_unavailable' on the parent PE. CA component still works."""
        c = connector
        c._now = lambda: FIXED_NOW
        fx = load_fixture("mp_3_8_2")

        def get_side_effect(path):
            if "/admin/sharepoint/settings" in path:
                raise MsGraphCapabilityError(
                    "Capability gap on /admin/sharepoint/settings: "
                    "Tenant does not have a SPO license.",
                    endpoint="/admin/sharepoint/settings",
                )
            raise KeyError(f"unmatched get: {path}")

        def paginate_side_effect(path):
            if "/identity/conditionalAccess/policies" in path:
                return iter(fx["conditional_access_policies"])
            raise KeyError(f"unmatched paginate: {path}")

        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None
        client.get.side_effect = get_side_effect
        client.paginate.side_effect = paginate_side_effect

        ev = c._pull_mp_3_8_2(client)

        assert ev is not None
        assert ev.metadata["sharepoint_status"] == "service_unavailable"
        assert ev.degraded is True
        assert "SharePoint Online unavailable" in (ev.degradation_reason or "")
        # CA is still pulled successfully.
        parsed = json.loads(ev.content.decode("utf-8"))
        assert parsed["conditional_access_policies"] == fx[
            "conditional_access_policies"
        ]
        assert parsed["sharepoint_settings"] is None
        # coverage_scope and missing_sources unchanged.
        assert ev.coverage_scope == "partial"
        assert ev.missing_sources == ["per_site_sharing"]


# ──────────────────────────────────────────────────────────────────────
# F. _pull_ac_3_1_3() — Control CUI Flow (partial): Conditional Access only
# ──────────────────────────────────────────────────────────────────────

class TestPullAC313Partial:
    """AC.L2-3.1.3 — F.3a ships CA only; coverage_scope=partial with three
    missing_sources. F.3b removes 'sensitivity_labels' later.
    """

    def _setup(self, connector):
        connector._now = lambda: FIXED_NOW
        fx = load_fixture("ac_3_1_3")
        client = make_mock_client(
            get_responses={},
            paginate_responses={
                "/identity/conditionalAccess/policies": fx[
                    "conditional_access_policies"
                ],
            },
        )
        return connector, client, fx

    def test_returns_pulled_evidence(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_ac_3_1_3(client)
        assert ev is not None
        assert ev.control_ids == ["AC.L2-3.1.3"]

    def test_coverage_scope_is_partial(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_ac_3_1_3(client)
        assert ev.coverage_scope == "partial"

    def test_missing_sources_three_items_in_f3a(self, connector):
        """F.3a ships missing_sources=[sensitivity_labels, dlp_policies,
        label_policies]. F.3b removes sensitivity_labels."""
        c, client, _ = self._setup(connector)
        ev = c._pull_ac_3_1_3(client)
        assert ev.missing_sources == [
            "sensitivity_labels",
            "dlp_policies",
            "label_policies",
        ]

    def test_content_includes_ca_policies(self, connector):
        c, client, fx = self._setup(connector)
        ev = c._pull_ac_3_1_3(client)
        parsed = json.loads(ev.content.decode("utf-8"))
        assert parsed["conditional_access_policies"] == fx[
            "conditional_access_policies"
        ]

    def test_metadata_ca_policy_count(self, connector):
        c, client, fx = self._setup(connector)
        ev = c._pull_ac_3_1_3(client)
        assert ev.metadata["ca_policy_count"] == len(
            fx["conditional_access_policies"]
        )

    def test_filename_includes_control_id_slug(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_ac_3_1_3(client)
        assert ev.filename.startswith("m365_ac_3_1_3_")
        assert ev.filename.endswith(".json")


# ──────────────────────────────────────────────────────────────────────
# G. pull() orchestrator — F.3a (3 controls)
# ──────────────────────────────────────────────────────────────────────

def _build_all_three_succeed_client(fxs):
    """MagicMock client whose dispatch covers all three F.3a controls."""
    client = MagicMock()
    client.__enter__.return_value = client
    client.__exit__.return_value = None

    def paginate_side_effect(path):
        if "/security/labels/retentionLabels" in path:
            return iter(fxs["mp_3_8_1"]["retention_labels"])
        if "/deviceManagement/deviceCompliancePolicies" in path:
            return iter(fxs["mp_3_8_1"]["intune_compliance_policies"])
        if "/identity/conditionalAccess/policies" in path:
            # MP.L2-3.8.2 and AC.L2-3.1.3 both hit this; serve the same
            # CA policy list (real Graph would return identical data).
            return iter(fxs["mp_3_8_2"]["conditional_access_policies"])
        raise KeyError(f"unmatched paginate: {path}")

    def get_side_effect(path):
        if "/admin/sharepoint/settings" in path:
            return fxs["mp_3_8_1"]["sharepoint_settings"]
        raise KeyError(f"unmatched get: {path}")

    client.paginate.side_effect = paginate_side_effect
    client.get.side_effect = get_side_effect
    return client


class TestPullOrchestratorF3a:
    """The pull() method composing the three F.3a control helpers."""

    def _setup_all_succeed(self, connector):
        connector._now = lambda: FIXED_NOW
        fxs = {
            k: load_fixture(k)
            for k in ["mp_3_8_1", "mp_3_8_2", "ac_3_1_3"]
        }
        client = _build_all_three_succeed_client(fxs)
        connector._build_client = lambda: client
        return connector

    def test_all_three_controls_yield_evidence(self, connector):
        c = self._setup_all_succeed(connector)
        items = list(c.pull())
        assert len(items) == 3
        control_ids = [item.control_ids[0] for item in items]
        assert control_ids == [
            "MP.L2-3.8.1",
            "MP.L2-3.8.2",
            "AC.L2-3.1.3",
        ]

    def test_no_errors_when_all_succeed(self, connector):
        c = self._setup_all_succeed(connector)
        list(c.pull())
        assert c.get_pull_errors() == []

    def test_one_control_failure_isolated(self, connector):
        """MP.L2-3.8.1 fails (Intune endpoint blows up with non-licensing
        error); MP.L2-3.8.2 and AC.L2-3.1.3 still succeed."""
        c = connector
        c._now = lambda: FIXED_NOW
        fxs = {k: load_fixture(k) for k in ["mp_3_8_1", "mp_3_8_2", "ac_3_1_3"]}

        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None

        def paginate_side_effect(path):
            if "/security/labels/retentionLabels" in path:
                return iter(fxs["mp_3_8_1"]["retention_labels"])
            if "/deviceManagement/deviceCompliancePolicies" in path:
                raise RuntimeError("simulated graph 500 on Intune")
            if "/identity/conditionalAccess/policies" in path:
                return iter(fxs["mp_3_8_2"]["conditional_access_policies"])
            raise KeyError(f"unmatched: {path}")

        def get_side_effect(path):
            if "/admin/sharepoint/settings" in path:
                return fxs["mp_3_8_1"]["sharepoint_settings"]
            raise KeyError(f"unmatched: {path}")

        client.paginate.side_effect = paginate_side_effect
        client.get.side_effect = get_side_effect
        c._build_client = lambda: client

        items = list(c.pull())
        # MP.L2-3.8.1 fails outright; the other two succeed.
        assert len(items) == 2
        control_ids = [i.control_ids[0] for i in items]
        assert "MP.L2-3.8.1" not in control_ids
        assert "MP.L2-3.8.2" in control_ids
        assert "AC.L2-3.1.3" in control_ids

        errors = c.get_pull_errors()
        assert len(errors) == 1
        assert "MP.L2-3.8.1" in errors[0]
        assert "simulated graph 500 on Intune" in errors[0]
        assert " | " in errors[0]  # canonical format

    def test_all_controls_fail_yields_zero_evidence(self, connector):
        c = connector
        c._now = lambda: FIXED_NOW
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None
        client.paginate.side_effect = RuntimeError("everything broken")
        client.get.side_effect = RuntimeError("everything broken")
        c._build_client = lambda: client

        items = list(c.pull())
        assert items == []

        errors = c.get_pull_errors()
        assert len(errors) == 3
        for cid in ["MP.L2-3.8.1", "MP.L2-3.8.2", "AC.L2-3.1.3"]:
            assert any(cid in e for e in errors), f"missing {cid} in errors"

    def test_pull_resets_accumulator(self, connector):
        c = connector
        c._now = lambda: FIXED_NOW
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None
        client.paginate.side_effect = RuntimeError("broken")
        client.get.side_effect = RuntimeError("broken")
        c._build_client = lambda: client

        list(c.pull())
        assert len(c.get_pull_errors()) == 3

        list(c.pull())
        assert len(c.get_pull_errors()) == 3  # not 6

    def test_get_pull_errors_returns_copy(self, connector):
        c = connector
        c._now = lambda: FIXED_NOW
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None
        client.paginate.side_effect = RuntimeError("broken")
        client.get.side_effect = RuntimeError("broken")
        c._build_client = lambda: client

        list(c.pull())
        errors = c.get_pull_errors()
        errors.append("local mutation")
        assert "local mutation" not in c.get_pull_errors()


# ──────────────────────────────────────────────────────────────────────
# E. Secret hygiene — regression bar
# ──────────────────────────────────────────────────────────────────────

class TestSecretHygiene:
    """Asserts client_secret never reaches logs, repr, or exception messages
    via the connector's code paths.
    """

    UNIQUE_SECRET = "TEST_SECRET_F2_DO_NOT_LEAK_q9w8e7r6t5"

    @pytest.fixture
    def hygiene_connector(self):
        creds = {**VALID_CREDS, "client_secret": self.UNIQUE_SECRET}
        return M365GccHighConnector(config={}, credentials=creds)

    def test_secret_not_in_repr(self, hygiene_connector):
        assert self.UNIQUE_SECRET not in repr(hygiene_connector)

    def test_secret_not_in_str(self, hygiene_connector):
        assert self.UNIQUE_SECRET not in str(hygiene_connector)

    @patch("src.connectors.connectors_builtin.m365_gcc_high.MsGraphClient")
    def test_secret_not_in_logs_on_success(
        self, mock_client_class, hygiene_connector, caplog
    ):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.get.return_value = {
            "value": [{"id": "x", "displayName": "Test", "tenantType": "AAD"}]
        }
        mock_client_class.return_value = mock_client

        with caplog.at_level(logging.DEBUG):
            hygiene_connector.test_connection()

        for record in caplog.records:
            assert self.UNIQUE_SECRET not in record.getMessage()
            assert self.UNIQUE_SECRET not in str(record.args)

    @patch("src.connectors.connectors_builtin.m365_gcc_high.MsGraphClient")
    def test_secret_not_in_logs_on_unexpected_exception(
        self, mock_client_class, hygiene_connector, caplog
    ):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.get.side_effect = RuntimeError("boom")
        mock_client_class.return_value = mock_client

        with caplog.at_level(logging.DEBUG):
            ok, msg = hygiene_connector.test_connection()

        assert self.UNIQUE_SECRET not in msg
        for record in caplog.records:
            assert self.UNIQUE_SECRET not in record.getMessage()
            assert self.UNIQUE_SECRET not in str(record.args)
            if record.exc_info:
                assert self.UNIQUE_SECRET not in str(record.exc_info)

    def test_secret_not_in_msgraph_client_call_args(self, hygiene_connector):
        # Confirms the client gets the secret as a kwarg, not embedded in
        # log_context or some other fielded dict that might be logged.
        with patch(
            "src.connectors.connectors_builtin.m365_gcc_high.MsGraphClient"
        ) as mock:
            hygiene_connector._build_client()
            kwargs = mock.call_args.kwargs
            assert kwargs["client_secret"] == self.UNIQUE_SECRET
            log_context = kwargs.get("log_context", {})
            assert self.UNIQUE_SECRET not in str(log_context)
            assert "client_secret" not in log_context
            assert "client_id" not in log_context
