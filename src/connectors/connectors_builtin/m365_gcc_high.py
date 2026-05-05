"""Microsoft 365 (GCC High) connector — Pass F.2 skeleton.

Pulls evidence from Microsoft Graph using the OAuth2 client-credentials flow
for Application API permissions. Supports commercial Microsoft Graph as well
as GCC High and DoD national clouds.

Pass F.2 ships the class skeleton and test_connection() only. pull() raises
NotImplementedError; the per-control pulls land in F.3a/b/c:

  F.3a — MP.L2-3.8.1, MP.L2-3.8.2, AC.L2-3.1.3 (partial)
  F.3b — AC.L2-3.1.3 (complete) + SC.L2-3.13.8
  F.3c — AU.L2-3.3.1 (via /security/auditLog/queries async helper from F.1.5)
  F.3d — eager-import this module from src/connectors/__init__.py so the
         connector becomes visible on /api/connectors/types

Until F.3d, this module is registered (via @register at class-def) but is
NOT eager-imported from src.connectors. /api/connectors/types does not show
m365_gcc_high. This invisibility is enforced by a static-source-check test
in tests/connectors/test_m365_gcc_high_registration.py.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterator

from src.connectors.base import BaseConnector, PulledEvidence
from src.connectors.registry import register
from src.connectors._msgraph import (
    MsGraphClient,
    MsGraphError,
    MsGraphAuthError,
    MsGraphPermissionError,
)

log = logging.getLogger(__name__)


@register
class M365GccHighConnector(BaseConnector):
    """Microsoft 365 (GCC High) connector — client-credentials flow.

    Same four-field credentials_schema as EntraIdConnector. The two
    connectors are distinct types because their Graph endpoints, control
    coverage, and required app permissions diverge — even though the
    auth surface is identical.
    """

    type_name = "m365_gcc_high"
    display_name = "Microsoft 365 (GCC High)"
    supported_controls = [
        "AC.L2-3.1.3",   # Information flow control (DLP, conditional access)
        "SC.L2-3.13.8",  # Cryptographic protection in transit (Exchange TLS)
        "MP.L2-3.8.1",   # Sensitivity labels (information at rest)
        "MP.L2-3.8.2",   # Label policies and label-application activity
        "AU.L2-3.3.1",   # Unified audit log (async query)
    ]

    credentials_schema = [
        {
            "name": "tenant_id",
            "label": "Tenant ID",
            "type": "text",
            "required": True,
            "placeholder": "00000000-0000-0000-0000-000000000000",
            "help": (
                "Your Microsoft 365 tenant ID (GUID). Find it in Entra admin "
                "center → Identity → Overview → 'Tenant ID'. "
                "Same tenant your Entra connector uses if you've already "
                "configured one."
            ),
        },
        {
            "name": "client_id",
            "label": "Application (Client) ID",
            "type": "text",
            "required": True,
            "placeholder": "00000000-0000-0000-0000-000000000000",
            "help": (
                "The app registration's Application (client) ID. Create a "
                "dedicated app for this connector under Entra → App "
                "registrations → New registration. Copy the Application "
                "(client) ID from the Overview page."
            ),
        },
        {
            "name": "client_secret",
            "label": "Client Secret",
            "type": "password",
            "required": True,
            "placeholder": "Secret value (not the secret ID)",
            "help": (
                "The secret VALUE created under Certificates & secrets "
                "→ New client secret. Copy immediately — Entra "
                "hides it after the page refreshes. Default expiry is 6 "
                "months; you'll need to rotate."
            ),
        },
        {
            "name": "cloud_environment",
            "label": "Cloud Environment",
            "type": "select",
            "required": True,
            "options": [
                {"value": "commercial", "label": "Commercial (most customers)"},
                {"value": "gcc_high",   "label": "GCC High (US Government)"},
                {"value": "dod",        "label": "DoD"},
            ],
            "help": (
                "DoD-adjacent contractors typically use GCC High. The "
                "connector type is named 'm365_gcc_high' for the most common "
                "customer, but the same code path serves commercial and DoD "
                "tenants. If unsure, ask your IT admin which Microsoft 365 "
                "tenant tier you're on."
            ),
        },
    ]

    setup_component = None  # Schema-driven form is sufficient

    def __init__(self, config: dict, credentials: dict):
        """Construct the connector. Does NOT acquire a token — that happens
        lazily on the first call to test_connection() or pull().
        """
        super().__init__(config, credentials)

        # Required credentials. Missing keys → KeyError, which the runner
        # catches and converts to a FAILED run with a useful message.
        # Don't validate format here — MSAL/Graph rejects malformed inputs
        # and the AADSTS code maps to a humanized message in _msgraph/auth.py.
        self._tenant_id = credentials["tenant_id"].strip()
        self._client_id = credentials["client_id"].strip()
        # Don't mutate the secret. The frontend ConnectorSetupForm trims on
        # submit; if a secret arrives with whitespace, that's the form's bug.
        self._client_secret = credentials["client_secret"]
        self._cloud_env = credentials.get("cloud_environment", "commercial")

        self._lookback_hours = self._clamp_lookback_hours(
            config.get("lookback_hours", 24)
        )

        # Per-control errors accumulated during pull(). F.3a will populate
        # this; F.2's stubbed pull() never reaches accumulation.
        self._pull_errors: list[str] = []

    @staticmethod
    def _clamp_lookback_hours(raw_value) -> int:
        """Clamp lookback_hours to [1, 168] (one hour to one week).

        Out-of-range or non-integer values are clamped with a warning rather
        than rejected. The customer might set lookback_hours via direct DB
        write before any UI exists for it; we don't want a typo to crash
        every pull. Behavior copied verbatim from EntraIdConnector — F.3c's
        AU.L2-3.3.1 audit-log window depends on it.

        Returns the clamped integer.
        """
        DEFAULT = 24
        MIN_HOURS = 1
        MAX_HOURS = 168  # 7 days

        # Coerce to int. Accept int, float, str-of-int. Reject everything else.
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            log.warning(
                "lookback_hours is not coercible to int; using default",
                extra={"raw_value": repr(raw_value), "default": DEFAULT},
            )
            return DEFAULT

        if value < MIN_HOURS:
            log.warning(
                "lookback_hours below minimum; clamping",
                extra={"requested": value, "clamped_to": MIN_HOURS},
            )
            return MIN_HOURS

        if value > MAX_HOURS:
            log.warning(
                "lookback_hours above maximum; clamping",
                extra={"requested": value, "clamped_to": MAX_HOURS},
            )
            return MAX_HOURS

        return value

    def _now(self) -> datetime:
        """Inject point for current time. Tests monkeypatch this on the
        instance to get deterministic timestamps in PulledEvidence content
        and audit log time windows.

        Returns timezone-aware UTC datetime.
        """
        return datetime.now(timezone.utc)

    def _build_client(self) -> MsGraphClient:
        """Construct a fresh MsGraphClient. Caller must close() or use as a
        context manager. Token acquisition is lazy — happens on first
        Graph call.
        """
        return MsGraphClient(
            tenant_id=self._tenant_id,
            client_id=self._client_id,
            client_secret=self._client_secret,
            cloud_env=self._cloud_env,
            log_context={
                "connector_type": self.type_name,
                "tenant_id": self._tenant_id,
                # Do NOT include client_id or client_secret in log_context.
            },
        )

    def test_connection(self) -> tuple[bool, str]:
        """Verify credentials and basic Graph connectivity.

        Acquires a token via client_credentials, then makes one canary call
        to /organization to confirm:
          1. The tenant exists.
          2. The client_id is registered in this tenant.
          3. The client_secret is valid.
          4. Directory.Read.All has been granted (the canary requires it).
          5. The cloud_environment matches the tenant's actual cloud.

        Returns:
            (True, "Authenticated to {tenant displayName}") on success.
            (False, "<humanized error>") on any failure. NEVER raises.
        """
        try:
            with self._build_client() as client:
                result = client.get(
                    "/organization?$select=id,displayName,tenantType"
                )
                orgs = result.get("value", [])
                if not orgs:
                    return (False,
                            "Authenticated, but /organization returned no "
                            "rows. This is unusual — verify the tenant "
                            "is active.")
                org = orgs[0]
                display_name = org.get("displayName", "<unknown tenant>")
                tenant_type = org.get("tenantType", "")
                return (True, f"Authenticated to {display_name} ({tenant_type})")

        except MsGraphAuthError as e:
            # AADSTS codes already humanized in _msgraph/auth.py
            return (False, str(e))

        except MsGraphPermissionError as e:
            # Most likely cause on a fresh app registration: admin consent
            # not granted or Directory.Read.All not added to API permissions.
            if e.missing_permission:
                return (False,
                        f"Connected, but missing permission: {e.missing_permission}. "
                        f"Grant it in Entra → App registrations → "
                        f"API permissions, then click 'Grant admin consent'.")
            return (False, f"Connected, but Graph returned 403: {e}")

        except MsGraphError as e:
            return (False, f"Microsoft Graph error: {e}")

        except Exception as e:  # noqa: BLE001
            # Last-resort catch — BaseConnector contract requires no raises
            # from test_connection(). Log without secrets and return failure.
            log.exception("m365_gcc_high test_connection unexpected error",
                          extra={"tenant_id": self._tenant_id})
            return (False, f"Unexpected error: {type(e).__name__}: {e}")

    def pull(self) -> Iterator[PulledEvidence]:
        """Pull evidence — NOT IMPLEMENTED in Pass F.2.

        F.3a/b/c land the per-control pulls; F.3d makes the connector
        visible on /api/connectors/types by adding the eager-import to
        src/connectors/__init__.py. The NotImplementedError message
        embeds the full Pass F roadmap so anyone hitting this stub by
        accident sees the next steps without having to chase down docs.
        """
        raise NotImplementedError(
            "M365GccHighConnector.pull() is not yet implemented. "
            "F.3a will land MP.L2-3.8.1, MP.L2-3.8.2, AC.L2-3.1.3 (partial). "
            "F.3b will complete AC.L2-3.1.3 and add SC.L2-3.13.8. "
            "F.3c will add AU.L2-3.3.1 via async query. "
            "F.3d will eager-import in src/connectors/__init__.py."
        )

    def get_pull_errors(self) -> list[str]:
        """Return per-control errors accumulated during pull().

        Per the Pass E.3b contract, the runner calls this once after pull()
        exhausts and extends summary.errors[] with the result. F.2's pull()
        raises before any accumulation, so this returns an empty list in F.2.
        F.3a wires actual accumulation.
        """
        return list(self._pull_errors)
