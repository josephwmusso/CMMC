"""Unit tests for EntraIdConnector — Pass E.2 + E.3a + E.3c."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.connectors.connectors_builtin.entra_id import EntraIdConnector
from src.connectors._msgraph.errors import (
    MsGraphAuthError,
    MsGraphError,
    MsGraphPermissionError,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "entra"


def load_fixture(name: str) -> dict:
    """Load a fixture JSON by control name (e.g. 'ac_3_1_1')."""
    return json.loads((FIXTURE_DIR / f"{name}.json").read_text(encoding="utf-8"))


def make_mock_client(get_responses: dict, paginate_responses: dict) -> MagicMock:
    """Build a MagicMock MsGraphClient that returns fixture data.

    get_responses: maps endpoint substring -> return value (single dict).
    paginate_responses: maps endpoint substring -> list of dicts.

    Endpoint matching is by 'first substring that's in the URL'.
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
    "client_secret": "TEST_SECRET_DO_NOT_LEAK_xyz789",
    "cloud_environment": "gcc_high",
}

VALID_CONFIG: dict = {}


@pytest.fixture
def connector():
    return EntraIdConnector(config=VALID_CONFIG, credentials=VALID_CREDS)


# ──────────────────────────────────────────────────────────────────────
# A. Class shape / static attributes (no I/O)
# ──────────────────────────────────────────────────────────────────────

class TestClassShape:

    def test_type_name_is_entra_id(self):
        assert EntraIdConnector.type_name == "entra_id"

    def test_display_name(self):
        assert EntraIdConnector.display_name == "Microsoft Entra ID"

    def test_supported_controls(self):
        assert EntraIdConnector.supported_controls == [
            "AC.L2-3.1.1",
            "IA.L2-3.5.3",
            "AC.L2-3.1.5",
            "AU.L2-3.3.1",
            "AC.L2-3.1.20",
        ]

    def test_setup_component_is_none(self):
        assert EntraIdConnector.setup_component is None

    def test_credentials_schema_has_four_fields(self):
        names = [f["name"] for f in EntraIdConnector.credentials_schema]
        assert names == ["tenant_id", "client_id", "client_secret", "cloud_environment"]

    def test_credentials_schema_field_types(self):
        types_by_name = {f["name"]: f["type"]
                         for f in EntraIdConnector.credentials_schema}
        assert types_by_name == {
            "tenant_id": "text",
            "client_id": "text",
            "client_secret": "password",
            "cloud_environment": "select",
        }

    def test_all_credentials_required(self):
        for f in EntraIdConnector.credentials_schema:
            assert f["required"] is True, f"{f['name']} should be required"

    def test_cloud_environment_options(self):
        cloud_field = next(f for f in EntraIdConnector.credentials_schema
                           if f["name"] == "cloud_environment")
        values = [opt["value"] for opt in cloud_field["options"]]
        assert values == ["commercial", "gcc_high", "dod"]

    def test_help_text_present_on_every_field(self):
        for f in EntraIdConnector.credentials_schema:
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
            "Ã¢",   # double-encoded UTF-8 prefix (Ã¢)
        ]
        for field in EntraIdConnector.credentials_schema:
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
        creds = {**VALID_CREDS,
                 "tenant_id": f"  {VALID_CREDS['tenant_id']}  ",
                 "client_id": f"\t{VALID_CREDS['client_id']}\n"}
        c = EntraIdConnector(config={}, credentials=creds)
        assert c._tenant_id == VALID_CREDS["tenant_id"]
        assert c._client_id == VALID_CREDS["client_id"]

    def test_init_does_not_strip_client_secret(self):
        # Principle: don't mutate secrets. The form trims on submit.
        # If the secret arrives with whitespace, that's the form's bug.
        creds = {**VALID_CREDS, "client_secret": "  spaced_secret  "}
        c = EntraIdConnector(config={}, credentials=creds)
        assert c._client_secret == "  spaced_secret  "

    def test_init_default_cloud_environment(self):
        creds = {k: v for k, v in VALID_CREDS.items()
                 if k != "cloud_environment"}
        c = EntraIdConnector(config={}, credentials=creds)
        assert c._cloud_env == "commercial"

    def test_init_missing_required_field_raises_keyerror(self):
        creds = {k: v for k, v in VALID_CREDS.items() if k != "tenant_id"}
        with pytest.raises(KeyError):
            EntraIdConnector(config={}, credentials=creds)


# ──────────────────────────────────────────────────────────────────────
# B'. lookback_hours config (Pass E.3a)
# ──────────────────────────────────────────────────────────────────────

class TestLookbackHoursConfig:
    """Pass E.3a — config-driven lookback_hours with [1, 168] clamp.

    Per discovery §5.3 and §10 Q11: lookback_hours lives in `config`
    (not credentials_schema), defaults to 24, and out-of-range values
    are clamped server-side rather than rejected.
    """

    def test_default_when_config_empty(self):
        c = EntraIdConnector(config={}, credentials=VALID_CREDS)
        assert c._lookback_hours == 24

    def test_default_when_key_absent(self):
        c = EntraIdConnector(config={"other_key": "value"}, credentials=VALID_CREDS)
        assert c._lookback_hours == 24

    def test_valid_int_pass_through(self):
        c = EntraIdConnector(config={"lookback_hours": 48}, credentials=VALID_CREDS)
        assert c._lookback_hours == 48

    def test_minimum_value_one_hour(self):
        c = EntraIdConnector(config={"lookback_hours": 1}, credentials=VALID_CREDS)
        assert c._lookback_hours == 1

    def test_maximum_value_one_week(self):
        c = EntraIdConnector(config={"lookback_hours": 168}, credentials=VALID_CREDS)
        assert c._lookback_hours == 168

    def test_below_minimum_clamps_to_one(self, caplog):
        with caplog.at_level(logging.WARNING):
            c = EntraIdConnector(config={"lookback_hours": 0}, credentials=VALID_CREDS)
        assert c._lookback_hours == 1
        assert any("below minimum" in r.getMessage() for r in caplog.records)

    def test_negative_clamps_to_one(self, caplog):
        with caplog.at_level(logging.WARNING):
            c = EntraIdConnector(config={"lookback_hours": -50}, credentials=VALID_CREDS)
        assert c._lookback_hours == 1
        assert any("below minimum" in r.getMessage() for r in caplog.records)

    def test_above_maximum_clamps_to_168(self, caplog):
        with caplog.at_level(logging.WARNING):
            c = EntraIdConnector(config={"lookback_hours": 8760}, credentials=VALID_CREDS)
        assert c._lookback_hours == 168
        assert any("above maximum" in r.getMessage() for r in caplog.records)

    def test_string_int_coerced(self):
        c = EntraIdConnector(config={"lookback_hours": "72"}, credentials=VALID_CREDS)
        assert c._lookback_hours == 72

    def test_float_truncated(self):
        # int(48.7) == 48. Document the behavior; don't pretend we round.
        c = EntraIdConnector(config={"lookback_hours": 48.7}, credentials=VALID_CREDS)
        assert c._lookback_hours == 48

    def test_garbage_string_falls_back_to_default(self, caplog):
        with caplog.at_level(logging.WARNING):
            c = EntraIdConnector(
                config={"lookback_hours": "not a number"},
                credentials=VALID_CREDS,
            )
        assert c._lookback_hours == 24
        assert any("not coercible" in r.getMessage() for r in caplog.records)

    def test_none_falls_back_to_default(self, caplog):
        with caplog.at_level(logging.WARNING):
            c = EntraIdConnector(
                config={"lookback_hours": None},
                credentials=VALID_CREDS,
            )
        assert c._lookback_hours == 24
        assert any("not coercible" in r.getMessage() for r in caplog.records)

    def test_dict_falls_back_to_default(self, caplog):
        # Defensive: someone direct-DB-pokes a non-scalar value.
        with caplog.at_level(logging.WARNING):
            c = EntraIdConnector(
                config={"lookback_hours": {"hours": 24}},
                credentials=VALID_CREDS,
            )
        assert c._lookback_hours == 24


class TestSchemaUnchangedByPassE3a:
    """Sanity: Pass E.3a does NOT add lookback_hours to credentials_schema.
    Per discovery §5.3 — it's a config field, not a credential.
    """

    def test_credentials_schema_still_has_four_fields(self):
        names = {f["name"] for f in EntraIdConnector.credentials_schema}
        assert names == {"tenant_id", "client_id", "client_secret", "cloud_environment"}
        assert "lookback_hours" not in names


# ──────────────────────────────────────────────────────────────────────
# C. test_connection() success and failure paths
# ──────────────────────────────────────────────────────────────────────

class TestTestConnection:

    @patch("src.connectors.connectors_builtin.entra_id.MsGraphClient")
    def test_success_returns_true_with_tenant_name(self, mock_client_class, connector):
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

    @patch("src.connectors.connectors_builtin.entra_id.MsGraphClient")
    def test_empty_organization_response(self, mock_client_class, connector):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.get.return_value = {"value": []}
        mock_client_class.return_value = mock_client

        ok, msg = connector.test_connection()

        assert ok is False
        assert "no rows" in msg.lower()

    @patch("src.connectors.connectors_builtin.entra_id.MsGraphClient")
    def test_auth_error_invalid_secret(self, mock_client_class, connector):
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

    @patch("src.connectors.connectors_builtin.entra_id.MsGraphClient")
    def test_auth_error_tenant_not_found(self, mock_client_class, connector):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.get.side_effect = MsGraphAuthError(
            "Tenant not found. Verify the Tenant ID matches your Entra admin center...",
            aadsts_code="AADSTS90002",
        )
        mock_client_class.return_value = mock_client

        ok, msg = connector.test_connection()

        assert ok is False
        assert "Tenant not found" in msg

    @patch("src.connectors.connectors_builtin.entra_id.MsGraphClient")
    def test_permission_error_with_named_permission(self, mock_client_class, connector):
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

    @patch("src.connectors.connectors_builtin.entra_id.MsGraphClient")
    def test_permission_error_without_named_permission(self, mock_client_class, connector):
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

    @patch("src.connectors.connectors_builtin.entra_id.MsGraphClient")
    def test_generic_msgraph_error(self, mock_client_class, connector):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client.get.side_effect = MsGraphError("Unexpected Graph response")
        mock_client_class.return_value = mock_client

        ok, msg = connector.test_connection()

        assert ok is False
        assert "Microsoft Graph error" in msg

    @patch("src.connectors.connectors_builtin.entra_id.MsGraphClient")
    def test_unexpected_exception_does_not_propagate(self, mock_client_class, connector):
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
# D. pull() — Pass E.2's deferred-implementation test removed in E.3c.
#    pull() is now implemented; orchestrator + per-control tests live in
#    sections F and G below.
# ──────────────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────────────
# E. Secret hygiene — regression bar
# ──────────────────────────────────────────────────────────────────────

class TestSecretHygiene:
    """Asserts client_secret never reaches logs, repr, or exception messages
    via the connector's code paths.
    """

    UNIQUE_SECRET = "TEST_SECRET_E2_DO_NOT_LEAK_q9w8e7r6t5"

    @pytest.fixture
    def hygiene_connector(self):
        creds = {**VALID_CREDS, "client_secret": self.UNIQUE_SECRET}
        return EntraIdConnector(config={}, credentials=creds)

    def test_secret_not_in_repr(self, hygiene_connector):
        assert self.UNIQUE_SECRET not in repr(hygiene_connector)

    def test_secret_not_in_str(self, hygiene_connector):
        assert self.UNIQUE_SECRET not in str(hygiene_connector)

    @patch("src.connectors.connectors_builtin.entra_id.MsGraphClient")
    def test_secret_not_in_logs_on_success(self, mock_client_class,
                                           hygiene_connector, caplog):
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

    @patch("src.connectors.connectors_builtin.entra_id.MsGraphClient")
    def test_secret_not_in_logs_on_unexpected_exception(self, mock_client_class,
                                                        hygiene_connector, caplog):
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
            # caplog also captures exc_info on .exception() calls
            if record.exc_info:
                assert self.UNIQUE_SECRET not in str(record.exc_info)

    def test_secret_not_in_msgraph_client_call_args(self, hygiene_connector):
        # Confirms the client gets the secret as a kwarg, not embedded in
        # log_context or some other fielded dict that might be logged.
        with patch("src.connectors.connectors_builtin.entra_id.MsGraphClient") as mock:
            hygiene_connector._build_client()
            kwargs = mock.call_args.kwargs
            assert kwargs["client_secret"] == self.UNIQUE_SECRET
            log_context = kwargs.get("log_context", {})
            assert self.UNIQUE_SECRET not in str(log_context)
            assert "client_secret" not in log_context
            assert "client_id" not in log_context


# ──────────────────────────────────────────────────────────────────────
# F. Per-control _pull_<control>() methods (Pass E.3c)
# ──────────────────────────────────────────────────────────────────────

class TestPullAC311:
    """AC.L2-3.1.1 — users, groups, group memberships."""

    def _setup(self, connector):
        connector._now = lambda: FIXED_NOW
        fx = load_fixture("ac_3_1_1")
        client = make_mock_client(
            get_responses={},
            paginate_responses={
                "/users?": fx["users"],
                "/groups?": fx["groups"],
                "/groups/group-id-1/members": fx["group_id_1_members"],
                "/groups/group-id-2/members": fx["group_id_2_members"],
            },
        )
        return connector, client, fx

    def test_returns_pulled_evidence(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_ac_3_1_1(client)
        assert ev is not None
        assert ev.control_ids == ["AC.L2-3.1.1"]

    def test_filename_includes_timestamp(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_ac_3_1_1(client)
        assert ev.filename.startswith("entra_users_groups_")
        assert ev.filename.endswith(".json")
        assert "2026-05-04" in ev.filename

    def test_content_is_bytes(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_ac_3_1_1(client)
        assert isinstance(ev.content, bytes)

    def test_content_parses_to_expected_shape(self, connector):
        c, client, fx = self._setup(connector)
        ev = c._pull_ac_3_1_1(client)
        parsed = json.loads(ev.content.decode("utf-8"))
        assert parsed["users"] == fx["users"]
        assert parsed["groups"] == fx["groups"]
        assert parsed["fetched_at"] == FIXED_NOW.isoformat()

    def test_membership_aggregation(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_ac_3_1_1(client)
        parsed = json.loads(ev.content.decode("utf-8"))
        assert len(parsed["group_memberships"]) == 2
        member_counts = {
            m["group_id"]: len(m["members"])
            for m in parsed["group_memberships"]
        }
        assert member_counts == {"group-id-1": 1, "group-id-2": 1}

    def test_metadata_counts(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_ac_3_1_1(client)
        assert ev.metadata["user_count"] == 2
        assert ev.metadata["group_count"] == 2
        assert ev.metadata["membership_count"] == 2
        assert ev.metadata["skipped_group_count"] == 0

    def test_per_group_failure_isolation(self, connector):
        c = connector
        c._now = lambda: FIXED_NOW
        fx = load_fixture("ac_3_1_1")

        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None

        def paginate_side_effect(path):
            if "/users?" in path and "members" not in path:
                return iter(fx["users"])
            if "/groups?" in path:
                return iter(fx["groups"])
            if "/groups/group-id-1/members" in path:
                return iter(fx["group_id_1_members"])
            if "/groups/group-id-2/members" in path:
                raise RuntimeError("simulated graph 500")
            raise KeyError(f"unmatched path: {path}")

        client.paginate.side_effect = paginate_side_effect

        ev = c._pull_ac_3_1_1(client)
        assert ev is not None
        parsed = json.loads(ev.content.decode("utf-8"))
        assert len(parsed["group_memberships"]) == 1
        assert parsed["skipped_groups"] == ["group-id-2"]
        assert ev.metadata["skipped_group_count"] == 1


class TestPullIA353:
    """IA.L2-3.5.3 — conditional access + per-user auth methods."""

    def _setup(self, connector):
        connector._now = lambda: FIXED_NOW
        fx = load_fixture("ia_3_5_3")
        client = make_mock_client(
            get_responses={},
            paginate_responses={
                "/identity/conditionalAccess/policies": fx["conditional_access_policies"],
                "/users?": fx["users"],
                "/users/user-id-1/authentication/methods": fx["user_id_1_methods"],
                "/users/user-id-2/authentication/methods": fx["user_id_2_methods"],
            },
        )
        return connector, client, fx

    def test_returns_pulled_evidence(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_ia_3_5_3(client)
        assert ev is not None
        assert ev.control_ids == ["IA.L2-3.5.3"]

    def test_content_includes_policies_and_methods(self, connector):
        c, client, fx = self._setup(connector)
        ev = c._pull_ia_3_5_3(client)
        parsed = json.loads(ev.content.decode("utf-8"))
        assert parsed["conditional_access_policies"] == fx["conditional_access_policies"]
        assert len(parsed["user_authentication_methods"]) == 2

    def test_metadata_counts(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_ia_3_5_3(client)
        assert ev.metadata["policy_count"] == 1
        assert ev.metadata["users_examined"] == 2
        assert ev.metadata["skipped_user_count"] == 0

    def test_per_user_failure_isolation(self, connector):
        c = connector
        c._now = lambda: FIXED_NOW
        fx = load_fixture("ia_3_5_3")

        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None

        def paginate_side_effect(path):
            if "/identity/conditionalAccess/policies" in path:
                return iter(fx["conditional_access_policies"])
            if "/users?" in path:
                return iter(fx["users"])
            if "/users/user-id-1/authentication/methods" in path:
                return iter(fx["user_id_1_methods"])
            if "/users/user-id-2/authentication/methods" in path:
                raise RuntimeError("simulated 500")
            raise KeyError(f"unmatched: {path}")

        client.paginate.side_effect = paginate_side_effect

        ev = c._pull_ia_3_5_3(client)
        assert ev is not None
        parsed = json.loads(ev.content.decode("utf-8"))
        assert len(parsed["user_authentication_methods"]) == 1
        assert parsed["skipped_users"] == ["user-id-2"]


class TestPullAC315:
    """AC.L2-3.1.5 — privileged role assignments."""

    def _setup(self, connector):
        connector._now = lambda: FIXED_NOW
        fx = load_fixture("ac_3_1_5")
        client = make_mock_client(
            get_responses={},
            paginate_responses={
                "/roleManagement/directory/roleAssignments": fx["role_assignments"],
                "/roleManagement/directory/roleDefinitions": fx["role_definitions"],
            },
        )
        return connector, client, fx

    def test_returns_pulled_evidence(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_ac_3_1_5(client)
        assert ev is not None
        assert ev.control_ids == ["AC.L2-3.1.5"]

    def test_metadata_counts(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_ac_3_1_5(client)
        assert ev.metadata["assignment_count"] == 1
        assert ev.metadata["definition_count"] == 1
        assert ev.metadata["roles_observed"] == [
            "62e90394-69f5-4237-9190-012177145e10"
        ]

    def test_content_includes_assignments_and_definitions(self, connector):
        c, client, fx = self._setup(connector)
        ev = c._pull_ac_3_1_5(client)
        parsed = json.loads(ev.content.decode("utf-8"))
        assert parsed["role_assignments"] == fx["role_assignments"]
        assert parsed["role_definitions"] == fx["role_definitions"]


class TestPullAU331:
    """AU.L2-3.3.1 — sign-in and directory audit logs."""

    def _setup(self, connector):
        connector._now = lambda: FIXED_NOW
        fx = load_fixture("au_3_3_1")
        client = make_mock_client(
            get_responses={},
            paginate_responses={
                "/auditLogs/signIns": fx["sign_ins"],
                "/auditLogs/directoryAudits": fx["directory_audits"],
            },
        )
        return connector, client, fx

    def test_returns_pulled_evidence(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_au_3_3_1(client)
        assert ev is not None
        assert ev.control_ids == ["AU.L2-3.3.1"]

    def test_filename_includes_lookback_hours(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_au_3_3_1(client)
        assert "_24h_" in ev.filename

    def test_window_is_lookback_hours_before_now(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_au_3_3_1(client)
        parsed = json.loads(ev.content.decode("utf-8"))
        window_end = datetime.fromisoformat(parsed["window_end"])
        window_start = datetime.fromisoformat(parsed["window_start"])
        delta_hours = (window_end - window_start).total_seconds() / 3600
        assert delta_hours == 24.0

    def test_filter_uses_z_suffix(self, connector):
        c = connector
        c._now = lambda: FIXED_NOW

        captured_paths = []

        def paginate_side_effect(path):
            captured_paths.append(path)
            return iter([])

        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None
        client.paginate.side_effect = paginate_side_effect

        c._pull_au_3_3_1(client)

        for p in captured_paths:
            assert "Z" in p
            assert "+00:00" not in p

    def test_lookback_hours_in_metadata(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_au_3_3_1(client)
        assert ev.metadata["lookback_hours"] == 24

    def test_custom_lookback_hours(self):
        c = EntraIdConnector(config={"lookback_hours": 72}, credentials=VALID_CREDS)
        c._now = lambda: FIXED_NOW
        fx = load_fixture("au_3_3_1")
        client = make_mock_client(
            get_responses={},
            paginate_responses={
                "/auditLogs/signIns": fx["sign_ins"],
                "/auditLogs/directoryAudits": fx["directory_audits"],
            },
        )
        ev = c._pull_au_3_3_1(client)
        assert "_72h_" in ev.filename
        assert ev.metadata["lookback_hours"] == 72


class TestPullAC3120:
    """AC.L2-3.1.20 — external collaboration."""

    def _setup(self, connector):
        connector._now = lambda: FIXED_NOW
        fx = load_fixture("ac_3_1_20")
        client = make_mock_client(
            get_responses={
                "/policies/crossTenantAccessPolicy/default": fx["cross_tenant_access_policy"],
            },
            paginate_responses={
                "/invitations": fx["b2b_invitations"],
            },
        )
        return connector, client, fx

    def test_returns_pulled_evidence(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_ac_3_1_20(client)
        assert ev is not None
        assert ev.control_ids == ["AC.L2-3.1.20"]

    def test_uses_get_for_singleton_policy(self, connector):
        # crossTenantAccessPolicy/default is a SINGLE OBJECT, not a collection.
        # The connector must use client.get(), not client.paginate().
        c, client, _ = self._setup(connector)
        c._pull_ac_3_1_20(client)
        get_calls = [call.args[0] for call in client.get.call_args_list]
        assert any("crossTenantAccessPolicy" in p for p in get_calls)

    def test_uses_paginate_for_invitations(self, connector):
        c, client, _ = self._setup(connector)
        c._pull_ac_3_1_20(client)
        paginate_calls = [call.args[0] for call in client.paginate.call_args_list]
        assert any("/invitations" in p for p in paginate_calls)

    def test_content_includes_policy_and_invitations(self, connector):
        c, client, fx = self._setup(connector)
        ev = c._pull_ac_3_1_20(client)
        parsed = json.loads(ev.content.decode("utf-8"))
        assert parsed["cross_tenant_access_policy"] == fx["cross_tenant_access_policy"]
        assert parsed["b2b_invitations"] == fx["b2b_invitations"]

    def test_metadata_counts(self, connector):
        c, client, _ = self._setup(connector)
        ev = c._pull_ac_3_1_20(client)
        assert ev.metadata["invitation_count"] == 1


# ──────────────────────────────────────────────────────────────────────
# G. pull() orchestrator (Pass E.3c)
# ──────────────────────────────────────────────────────────────────────

def _build_all_succeed_client(fxs):
    """Build a MagicMock client whose dispatch covers all five controls."""
    client = MagicMock()
    client.__enter__.return_value = client
    client.__exit__.return_value = None

    def paginate_side_effect(path):
        # Order matters — most specific paths first.
        if "/users/user-id-1/authentication/methods" in path:
            return iter(fxs["ia_3_5_3"]["user_id_1_methods"])
        if "/users/user-id-2/authentication/methods" in path:
            return iter(fxs["ia_3_5_3"]["user_id_2_methods"])
        if "/groups/group-id-1/members" in path:
            return iter(fxs["ac_3_1_1"]["group_id_1_members"])
        if "/groups/group-id-2/members" in path:
            return iter(fxs["ac_3_1_1"]["group_id_2_members"])
        # IA.L2-3.5.3 only $select=id; AC.L2-3.1.1 selects more fields.
        # Both match "/users?" — return the same user list shape (id-only
        # works for both code paths).
        if "/users?" in path:
            return iter(fxs["ac_3_1_1"]["users"])
        if "/groups?" in path:
            return iter(fxs["ac_3_1_1"]["groups"])
        if "/identity/conditionalAccess/policies" in path:
            return iter(fxs["ia_3_5_3"]["conditional_access_policies"])
        if "/roleManagement/directory/roleAssignments" in path:
            return iter(fxs["ac_3_1_5"]["role_assignments"])
        if "/roleManagement/directory/roleDefinitions" in path:
            return iter(fxs["ac_3_1_5"]["role_definitions"])
        if "/auditLogs/signIns" in path:
            return iter(fxs["au_3_3_1"]["sign_ins"])
        if "/auditLogs/directoryAudits" in path:
            return iter(fxs["au_3_3_1"]["directory_audits"])
        if "/invitations" in path:
            return iter(fxs["ac_3_1_20"]["b2b_invitations"])
        raise KeyError(f"unmatched paginate: {path}")

    def get_side_effect(path):
        if "crossTenantAccessPolicy" in path:
            return fxs["ac_3_1_20"]["cross_tenant_access_policy"]
        raise KeyError(f"unmatched get: {path}")

    client.paginate.side_effect = paginate_side_effect
    client.get.side_effect = get_side_effect
    return client


class TestPullOrchestrator:
    """The pull() method composing five _pull_<control>() helpers."""

    def _setup_all_succeed(self, connector):
        connector._now = lambda: FIXED_NOW
        fxs = {k: load_fixture(k) for k in
               ["ac_3_1_1", "ia_3_5_3", "ac_3_1_5", "au_3_3_1", "ac_3_1_20"]}
        client = _build_all_succeed_client(fxs)
        connector._build_client = lambda: client
        return connector

    def test_all_five_controls_yield_evidence(self, connector):
        c = self._setup_all_succeed(connector)
        items = list(c.pull())
        assert len(items) == 5
        control_ids = [item.control_ids[0] for item in items]
        assert control_ids == [
            "AC.L2-3.1.1", "IA.L2-3.5.3", "AC.L2-3.1.5",
            "AU.L2-3.3.1", "AC.L2-3.1.20",
        ]

    def test_no_errors_when_all_succeed(self, connector):
        c = self._setup_all_succeed(connector)
        list(c.pull())
        assert c.get_pull_errors() == []

    def test_one_control_failure_isolated(self, connector):
        c = connector
        c._now = lambda: FIXED_NOW

        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None

        fxs = {k: load_fixture(k) for k in
               ["ac_3_1_1", "ia_3_5_3", "ac_3_1_5", "au_3_3_1", "ac_3_1_20"]}

        def paginate_side_effect(path):
            if "/roleManagement" in path:
                raise RuntimeError("simulated graph failure")
            # Re-use the all-succeed dispatch otherwise.
            if "/users/user-id-1/authentication/methods" in path:
                return iter(fxs["ia_3_5_3"]["user_id_1_methods"])
            if "/users/user-id-2/authentication/methods" in path:
                return iter(fxs["ia_3_5_3"]["user_id_2_methods"])
            if "/groups/group-id-1/members" in path:
                return iter(fxs["ac_3_1_1"]["group_id_1_members"])
            if "/groups/group-id-2/members" in path:
                return iter(fxs["ac_3_1_1"]["group_id_2_members"])
            if "/users?" in path:
                return iter(fxs["ac_3_1_1"]["users"])
            if "/groups?" in path:
                return iter(fxs["ac_3_1_1"]["groups"])
            if "/identity/conditionalAccess/policies" in path:
                return iter(fxs["ia_3_5_3"]["conditional_access_policies"])
            if "/auditLogs/signIns" in path:
                return iter(fxs["au_3_3_1"]["sign_ins"])
            if "/auditLogs/directoryAudits" in path:
                return iter(fxs["au_3_3_1"]["directory_audits"])
            if "/invitations" in path:
                return iter(fxs["ac_3_1_20"]["b2b_invitations"])
            raise KeyError(f"unmatched: {path}")

        def get_side_effect(path):
            if "crossTenantAccessPolicy" in path:
                return fxs["ac_3_1_20"]["cross_tenant_access_policy"]
            raise KeyError(f"unmatched: {path}")

        client.paginate.side_effect = paginate_side_effect
        client.get.side_effect = get_side_effect
        c._build_client = lambda: client

        items = list(c.pull())
        # Four controls succeed, one fails.
        assert len(items) == 4
        control_ids = [item.control_ids[0] for item in items]
        assert "AC.L2-3.1.5" not in control_ids

        errors = c.get_pull_errors()
        assert len(errors) == 1
        assert "AC.L2-3.1.5" in errors[0]
        assert "simulated graph failure" in errors[0]
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
        assert len(errors) == 5
        for cid in ["AC.L2-3.1.1", "IA.L2-3.5.3", "AC.L2-3.1.5",
                    "AU.L2-3.3.1", "AC.L2-3.1.20"]:
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
        assert len(c.get_pull_errors()) == 5

        list(c.pull())
        assert len(c.get_pull_errors()) == 5  # not 10

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
# H. Pull-time secret hygiene (Pass E.3c regression bar)
# ──────────────────────────────────────────────────────────────────────

class TestPullSecretHygiene:
    """Pass E.3c regression: client_secret never reaches logs/repr/errors
    during a real pull cycle, including total-failure paths.
    """

    UNIQUE_SECRET = "TEST_SECRET_E3C_DO_NOT_LEAK_a1b2c3d4e5"

    @pytest.fixture
    def hygiene_connector(self):
        creds = {**VALID_CREDS, "client_secret": self.UNIQUE_SECRET}
        return EntraIdConnector(config={}, credentials=creds)

    def test_secret_not_in_pull_errors_on_total_failure(self, hygiene_connector, caplog):
        c = hygiene_connector
        c._now = lambda: FIXED_NOW
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None
        client.paginate.side_effect = RuntimeError("broken")
        client.get.side_effect = RuntimeError("broken")
        c._build_client = lambda: client

        with caplog.at_level(logging.DEBUG):
            list(c.pull())

        for err in c.get_pull_errors():
            assert self.UNIQUE_SECRET not in err

        for record in caplog.records:
            assert self.UNIQUE_SECRET not in record.getMessage()
            assert self.UNIQUE_SECRET not in str(record.args)
            if record.exc_info:
                assert self.UNIQUE_SECRET not in str(record.exc_info)
