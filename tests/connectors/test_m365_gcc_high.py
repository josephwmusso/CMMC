"""Unit tests for M365GccHighConnector — Pass F.2 skeleton.

Mirrors test_entra_id.py's structural test surface. Per-control pull tests
arrive in F.3a/b/c when pull() is implemented. F.2 stubs pull() with a
NotImplementedError that names all five controls and the F.3a/b/c/d
roadmap; TestPullStubbed pins the stub message contract.

Default-respect contract: zero edits to existing tests. This file is
purely additive.
"""

from __future__ import annotations

import logging
from unittest.mock import patch, MagicMock

import pytest

from src.connectors.connectors_builtin.m365_gcc_high import M365GccHighConnector
from src.connectors._msgraph.errors import (
    MsGraphAuthError,
    MsGraphError,
    MsGraphPermissionError,
)


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
# D. pull() — F.2 stub
# ──────────────────────────────────────────────────────────────────────

class TestPullStubbed:
    """F.2 stubs pull() with a NotImplementedError that names the five
    controls and the F.3a/b/c/d roadmap. The stub is self-documenting:
    anyone hitting it sees the next steps without chasing docs.

    F.3a will REPLACE this entire test class when the orchestrator and
    per-control pulls land.
    """

    def test_pull_raises_not_implemented(self, connector):
        with pytest.raises(NotImplementedError):
            connector.pull()

    def test_stub_message_names_class(self, connector):
        with pytest.raises(NotImplementedError) as exc_info:
            connector.pull()
        assert "M365GccHighConnector" in str(exc_info.value)

    def test_stub_message_names_all_five_controls(self, connector):
        with pytest.raises(NotImplementedError) as exc_info:
            connector.pull()
        msg = str(exc_info.value)
        for control_id in [
            "AC.L2-3.1.3",
            "SC.L2-3.13.8",
            "MP.L2-3.8.1",
            "MP.L2-3.8.2",
            "AU.L2-3.3.1",
        ]:
            assert control_id in msg, (
                f"Stub message must reference {control_id}"
            )

    def test_stub_message_names_pass_phases(self, connector):
        with pytest.raises(NotImplementedError) as exc_info:
            connector.pull()
        msg = str(exc_info.value)
        for phase in ["F.3a", "F.3b", "F.3c", "F.3d"]:
            assert phase in msg, f"Stub message must reference {phase}"

    def test_get_pull_errors_returns_empty_in_f2(self, connector):
        """F.2's pull() raises before any accumulation; get_pull_errors()
        returns []. F.3a wires real accumulation."""
        assert connector.get_pull_errors() == []


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
