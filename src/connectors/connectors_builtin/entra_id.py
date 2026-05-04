"""Microsoft Entra ID connector.

Pulls evidence from Microsoft Graph using the OAuth2 client-credentials flow
for Application API permissions. Supports commercial Microsoft Graph as well
as GCC High and DoD national clouds.

Pass E.2 ships the class skeleton and test_connection() only.
Pass E.3 will implement pull() across five CMMC controls:
  AC.L2-3.1.1, IA.L2-3.5.3, AC.L2-3.1.5, AU.L2-3.3.1, AC.L2-3.1.20
"""

from __future__ import annotations

import logging
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
class EntraIdConnector(BaseConnector):
    """Microsoft Entra ID connector — client-credentials flow."""

    type_name = "entra_id"
    display_name = "Microsoft Entra ID"
    supported_controls = [
        "AC.L2-3.1.1",   # Account management
        "IA.L2-3.5.3",   # MFA
        "AC.L2-3.1.5",   # Least privilege
        "AU.L2-3.3.1",   # Audit logs
        "AC.L2-3.1.20",  # External connections
    ]

    credentials_schema = [
        {
            "name": "tenant_id",
            "label": "Tenant ID",
            "type": "text",
            "required": True,
            "placeholder": "00000000-0000-0000-0000-000000000000",
            "help": (
                "Your Entra tenant ID (GUID). Find it in Entra admin center "
                "→ Identity → Overview → 'Tenant ID'."
            ),
        },
        {
            "name": "client_id",
            "label": "Application (Client) ID",
            "type": "text",
            "required": True,
            "placeholder": "00000000-0000-0000-0000-000000000000",
            "help": (
                "The app registration's Application (client) ID. After "
                "creating the app registration in Entra → App registrations, "
                "copy this from the Overview page."
            ),
        },
        {
            "name": "client_secret",
            "label": "Client Secret",
            "type": "password",
            "required": True,
            "placeholder": "Secret value (not the secret ID)",
            "help": (
                "The secret VALUE created under Certificates & secrets → New "
                "client secret. Copy immediately — Entra hides it after the "
                "page refreshes. Default expiry is 6 months; you'll need to "
                "rotate."
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
                "DoD-adjacent contractors typically use GCC High. If unsure, "
                "ask your IT admin which Microsoft 365 tenant tier you're on."
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

    @staticmethod
    def _clamp_lookback_hours(raw_value) -> int:
        """Clamp lookback_hours to [1, 168] (one hour to one week).

        Out-of-range or non-integer values are clamped with a warning rather
        than rejected. The customer might set lookback_hours via direct DB
        write before any UI exists for it; we don't want a typo to crash
        every pull. Per discovery §10 Q11.

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
                            "rows. This is unusual — verify the tenant is "
                            "active.")
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
                        f"Grant it in Entra → App registrations → API permissions, "
                        f"then click 'Grant admin consent'.")
            return (False, f"Connected, but Graph returned 403: {e}")

        except MsGraphError as e:
            return (False, f"Microsoft Graph error: {e}")

        except Exception as e:  # noqa: BLE001
            # Last-resort catch — BaseConnector contract requires no raises
            # from test_connection(). Log without secrets and return failure.
            log.exception("entra_id test_connection unexpected error",
                          extra={"tenant_id": self._tenant_id})
            return (False, f"Unexpected error: {type(e).__name__}: {e}")

    def pull(self) -> Iterator[PulledEvidence]:
        """Pull evidence from Microsoft Graph for five CMMC controls.

        NOT YET IMPLEMENTED — Pass E.3.
        """
        raise NotImplementedError(
            "EntraIdConnector.pull() is not yet implemented. "
            "Pass E.2 ships the skeleton and test_connection() only. "
            "Pass E.3 implements pull() across five controls."
        )
        # The following yield is unreachable but makes Python recognize this
        # as a generator function, matching the BaseConnector type signature.
        yield  # pragma: no cover
