"""Microsoft 365 (GCC High) connector — Pass F.3b (4 of 5 controls live).

Pulls evidence from Microsoft Graph using the OAuth2 client-credentials flow
for Application API permissions. Supports commercial Microsoft Graph as well
as GCC High and DoD national clouds.

Pass F.3b adds AC.L2-3.1.3 sensitivity-label completion and the new
SC.L2-3.13.8 (Data in Transit) control. Live state:
  MP.L2-3.8.1 — Media Protection (digital): SharePoint sharing posture +
                retention labels + Intune device compliance (license-conditional).
  MP.L2-3.8.2 — Media Access (digital): SharePoint sharing posture +
                Conditional Access policies (CA reuse from Pass E IA.L2-3.5.3
                domain). coverage_scope=partial; per-site sharingCapability is
                not in Graph v1.0 (empirically confirmed by Microsoft's schema
                parser during F.3a live verification).
  AC.L2-3.1.3 — Control CUI Flow (partial): Conditional Access + sensitivity
                labels. coverage_scope=partial; dlp_policies and label_policies
                permanently deferred (PowerShell-only, no Graph endpoint —
                hypothetical Phase 5.4 shim out of Pass F scope entirely).
  SC.L2-3.13.8 — Data in Transit (aggregate): Microsoft Secure Score (TLS-
                relevant control breakdown) + Conditional Access (TLS/app-
                protection) + sensitivity labels with encryption settings.
                coverage_scope=partial; exchange_online_tls deferred to
                Phase 5.4 PowerShell shim. evidence_directness="aggregate"
                because the headline signal is Microsoft's score; raw_config
                sub-components live in metadata.

Outstanding sub-passes:
  F.3c — AU.L2-3.3.1 (via /security/auditLog/queries async helper from F.1.5)
  F.3d — eager-import this module from src/connectors/__init__.py so the
         connector becomes visible on /api/connectors/types

Conventions established by F.3a/b (load-bearing for SSP narrative downstream):

  metadata["media_scope"]: closed-set string literal {"digital", "paper"}.
    F.3a/b set only "digital" — paper-media controls are out of scope for
    automated pulls (paper destruction is a physical-process control).
    Future SSP renderer reads this key to render the paper-media exclusion
    narrative for MP family controls.

  metadata["intune_status"]: closed-set string literal {"ok",
    "license_not_detected", "service_unavailable"}. Captures Intune-sub-
    component health on MP.L2-3.8.1's PulledEvidence. The two non-"ok"
    values reflect distinct Microsoft signals:
      - "license_not_detected": 403 + Forbidden_LicensingError. Tenant has
        Intune at the directory level but a per-feature license is missing.
      - "service_unavailable":  400 + BadRequest + "not applicable to
        target tenant". Intune isn't provisioned on the tenant at all.
    Either non-"ok" value flags the parent PulledEvidence degraded=True.

  metadata["sharepoint_status"]: closed-set string literal {"ok",
    "service_unavailable"}. SharePoint Online unavailability is signaled
    by 400 + BadRequest + "does not have a SPO license." (no separate
    licensing-signal path observed for SPO yet — F.3a only sees the 400
    shape). Used by both MP.L2-3.8.1 and MP.L2-3.8.2.

  metadata["sensitivity_label_status"]: closed-set string literal {"ok",
    "service_unavailable", "license_not_detected"}. Captures Purview /
    Information Protection sub-component health. Used by AC.L2-3.1.3 and
    SC.L2-3.13.8. F.3b sees only the "service_unavailable" path against
    the unprovisioned trial; the licensing_signal path is anticipated for
    tenants with Purview-but-no-Premium and validated by F.4.

  metadata["secure_score_status"]: closed-set string literal {"ok",
    "service_unavailable", "license_not_detected"}. Captures Microsoft
    Secure Score (Microsoft 365 Defender) sub-component health on
    SC.L2-3.13.8's PulledEvidence.

Until F.3d, this module is registered (via @register at class-def) but is
NOT eager-imported from src.connectors. /api/connectors/types does not show
m365_gcc_high. This invisibility is enforced by a static-source-check test
in tests/connectors/test_m365_gcc_high_registration.py.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Iterator

from src.connectors.base import BaseConnector, PulledEvidence
from src.connectors.registry import register
from src.connectors._msgraph import (
    MsGraphClient,
    MsGraphError,
    MsGraphAuthError,
    MsGraphCapabilityError,
    MsGraphPermissionError,
    format_pull_error,
)

log = logging.getLogger(__name__)


def _label_has_encryption(label: dict) -> bool:
    """Return True if a sensitivity-label dict carries encryption settings.

    Defensive both-shape match. Per Phase 1.f of F.3b discovery, the
    /beta/security/informationProtection/sensitivityLabels response uses
    one of two shapes for encryption configuration:

      Shape A — top-level protectionSettings:
          {"protectionSettings": {"encryptContent": true, ...}, ...}

      Shape B — actionSettings array with @odata.type discriminator:
          {"actionSettings": [
              {"@odata.type": "#microsoft.graph.security.encryptContent", ...},
              ...
          ], ...}

    Both shapes appear in beta documentation and may evolve. We match
    either rather than assume one. F.4 against a Purview-provisioned
    tenant validates which shape Microsoft actually returns; until then,
    the defensive filter is correct in expectation.

    Returns False on malformed inputs (non-dict, missing keys, non-iterable
    actionSettings) — never raises.
    """
    if not isinstance(label, dict):
        return False

    # Shape A
    ps = label.get("protectionSettings")
    if isinstance(ps, dict) and ps.get("encryptContent") is True:
        return True

    # Shape B
    actions = label.get("actionSettings")
    if isinstance(actions, list):
        for action in actions:
            if not isinstance(action, dict):
                continue
            odata_type = action.get("@odata.type")
            if isinstance(odata_type, str) and "encrypt" in odata_type.lower():
                return True

    return False


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
        """Pull evidence from Microsoft Graph for the supported controls.

        F.3a ships three of five controls live: MP.L2-3.8.1, MP.L2-3.8.2,
        AC.L2-3.1.3 (partial). F.3b adds SC.L2-3.13.8 and completes
        AC.L2-3.1.3; F.3c adds AU.L2-3.3.1 via the async-query helper.

        Per-control errors are caught and accumulated on self._pull_errors
        (surfaced via get_pull_errors() per the Pass E.3b contract). One
        failing control does NOT abort the others.

        Errors during MsGraphClient construction or token acquisition kill
        the entire pull (caught at the runner's outer scope, run -> FAILED).
        Errors inside individual _pull_<control>() methods are isolated.
        """
        # Reset accumulator at start of each pull. Per-run-fresh-instance
        # guarantee makes this belt-and-suspenders, but the discipline
        # protects against future runner refactors that reuse instances.
        self._pull_errors = []

        # Tuple shape: (control_id, endpoint_summary, method).
        # endpoint_summary is the diagnostic string used in format_pull_error
        # output — not a real URL.
        controls = [
            (
                "MP.L2-3.8.1",
                "/admin/sharepoint/settings,/security/labels/retentionLabels,"
                "/deviceManagement/deviceCompliancePolicies",
                self._pull_mp_3_8_1,
            ),
            (
                "MP.L2-3.8.2",
                "/admin/sharepoint/settings,/identity/conditionalAccess/policies",
                self._pull_mp_3_8_2,
            ),
            (
                "AC.L2-3.1.3",
                "/identity/conditionalAccess/policies,"
                "/beta/security/informationProtection/sensitivityLabels (partial)",
                self._pull_ac_3_1_3,
            ),
            (
                "SC.L2-3.13.8",
                "/security/secureScores,/security/secureScoreControlProfiles,"
                "/identity/conditionalAccess/policies,"
                "/beta/security/informationProtection/sensitivityLabels (partial)",
                self._pull_sc_3_13_8,
            ),
        ]

        with self._build_client() as client:
            for control_id, endpoint_summary, fn in controls:
                try:
                    ev = fn(client)
                    if ev is not None:
                        yield ev
                except Exception as e:  # noqa: BLE001
                    self._pull_errors.append(
                        format_pull_error(control_id, endpoint_summary, e)
                    )
                    log.warning(
                        "control pull failed; isolating and continuing",
                        extra={
                            "control_id": control_id,
                            "endpoint_summary": endpoint_summary,
                            "error_class": type(e).__name__,
                            "error": str(e),
                        },
                    )
                    continue

    def get_pull_errors(self) -> list[str]:
        """Return per-control errors accumulated during pull().

        Per the Pass E.3b contract, the runner calls this once after pull()
        exhausts and extends summary.errors[] with the result. Returns a
        copy (not the live list) so caller mutations don't affect connector
        state.
        """
        return list(self._pull_errors)

    # ----- Per-control pull helpers ---------------------------------------

    def _pull_mp_3_8_1(self, client: MsGraphClient) -> PulledEvidence | None:
        """MP.L2-3.8.1 — Media Protection (digital).

        Three Graph endpoints compose this evidence:
          /admin/sharepoint/settings              (singleton, GET)
          /security/labels/retentionLabels        (paginated)
          /deviceManagement/deviceCompliancePolicies (paginated, license-cond.)

        Capability-gap handling: each endpoint can independently fail with
        either a 400 (service unprovisioned — MsGraphCapabilityError) or
        a 403 (per-feature license missing — MsGraphPermissionError with
        licensing_signal=True). Both classes of failure degrade the
        sub-component without aborting the control. Non-licensing 403s
        and other exceptions propagate to the orchestrator's per-control
        isolator (whole-control failure).

        Sub-component status keys are closed sets:
          sharepoint_status: {"ok", "service_unavailable"}
          intune_status:     {"ok", "license_not_detected", "service_unavailable"}
        """
        # SharePoint settings — capability-gap-conditional.
        sharepoint_settings: dict | None = None
        sharepoint_status: str = "ok"
        sharepoint_degradation_reason: str | None = None
        try:
            sharepoint_settings = client.get("/admin/sharepoint/settings")
        except MsGraphCapabilityError as exc:
            sharepoint_status = "service_unavailable"
            sharepoint_degradation_reason = (
                f"SharePoint Online unavailable on tenant: {exc}"
            )
            log.warning(
                "SharePoint unavailable; emitting degraded evidence for MP.L2-3.8.1",
                extra={
                    "tenant_id": self._tenant_id,
                    "endpoint": "/admin/sharepoint/settings",
                },
            )

        retention_labels = list(
            client.paginate("/security/labels/retentionLabels")
        )

        # Intune call — both license-conditional (403) and capability-gap (400).
        intune_policies: list[dict] = []
        intune_status: str = "ok"
        intune_degradation_reason: str | None = None
        try:
            intune_policies = list(
                client.paginate("/deviceManagement/deviceCompliancePolicies")
            )
        except MsGraphCapabilityError as exc:
            intune_status = "service_unavailable"
            intune_degradation_reason = (
                f"Intune service unavailable on tenant: {exc}"
            )
            log.warning(
                "Intune service unavailable; emitting degraded evidence for MP.L2-3.8.1",
                extra={
                    "tenant_id": self._tenant_id,
                    "endpoint": "/deviceManagement/deviceCompliancePolicies",
                },
            )
        except MsGraphPermissionError as exc:
            if exc.licensing_signal:
                intune_status = "license_not_detected"
                intune_degradation_reason = (
                    "Intune license not detected on tenant"
                )
                log.warning(
                    "Intune license not detected; emitting degraded evidence "
                    "for MP.L2-3.8.1",
                    extra={
                        "tenant_id": self._tenant_id,
                        "endpoint": "/deviceManagement/deviceCompliancePolicies",
                        "missing_permission": exc.missing_permission,
                    },
                )
            else:
                # Non-licensing 403 — propagate so the orchestrator records
                # this as a control failure, not a sub-component degradation.
                raise

        utc_iso = self._now().isoformat()
        content = json.dumps({
            "sharepoint_settings": sharepoint_settings,
            "sharepoint_status": sharepoint_status,
            "retention_labels": retention_labels,
            "intune_compliance_policies": intune_policies,
            "intune_status": intune_status,
            "fetched_at": utc_iso,
        }, sort_keys=True).encode("utf-8")

        # Compose the parent degradation_reason from any non-"ok" sub-components.
        degradation_reasons = [
            r for r in (sharepoint_degradation_reason, intune_degradation_reason)
            if r is not None
        ]
        degraded = bool(degradation_reasons)
        combined_reason = " | ".join(degradation_reasons) if degradation_reasons else None

        return PulledEvidence(
            filename=f"m365_mp_3_8_1_{utc_iso}.json",
            content=content,
            mime_type="application/json",
            description=(
                "Digital media protection: tenant SharePoint sharing posture, "
                "retention labels, and Intune device compliance policies."
            ),
            control_ids=["MP.L2-3.8.1"],
            metadata={
                "media_scope": "digital",
                "endpoints": [
                    "/admin/sharepoint/settings",
                    "/security/labels/retentionLabels",
                    "/deviceManagement/deviceCompliancePolicies",
                ],
                "retention_label_count": len(retention_labels),
                "intune_policy_count": len(intune_policies),
                "sharepoint_status": sharepoint_status,
                "intune_status": intune_status,
            },
            degraded=degraded,
            degradation_reason=combined_reason,
        )

    def _pull_mp_3_8_2(self, client: MsGraphClient) -> PulledEvidence | None:
        """MP.L2-3.8.2 — Media Access (digital).

        Two Graph endpoints compose this evidence:
          /admin/sharepoint/settings              (singleton, GET — called
                                                   independently from MP.L2-3.8.1
                                                   per the per-control isolation
                                                   contract)
          /identity/conditionalAccess/policies    (paginated; same endpoint
                                                   Pass E IA.L2-3.5.3 hits — dedup
                                                   deferred to Phase 5.6)

        Coverage scope is "partial": per-site sharingCapability is NOT
        exposed by Graph v1.0 (lives in the SharePoint admin REST API,
        outside Graph's auth surface). Tenant-wide sharing posture from
        /admin/sharepoint/settings is real coverage at the tenant scope;
        the partial flag is honest about the per-site gap, not the whole
        control.

        Capability-gap handling: when SharePoint is unprovisioned (400 +
        BadRequest), the SharePoint sub-component degrades but the CA
        component still yields. CA always works on a working tenant
        (Conditional Access is an Entra ID Premium feature, not a
        SharePoint feature).
        """
        # SharePoint settings — capability-gap-conditional.
        sharepoint_settings: dict | None = None
        sharepoint_status: str = "ok"
        sharepoint_degradation_reason: str | None = None
        try:
            sharepoint_settings = client.get("/admin/sharepoint/settings")
        except MsGraphCapabilityError as exc:
            sharepoint_status = "service_unavailable"
            sharepoint_degradation_reason = (
                f"SharePoint Online unavailable on tenant: {exc}"
            )
            log.warning(
                "SharePoint unavailable; emitting degraded evidence for MP.L2-3.8.2",
                extra={
                    "tenant_id": self._tenant_id,
                    "endpoint": "/admin/sharepoint/settings",
                },
            )

        ca_policies = list(
            client.paginate("/identity/conditionalAccess/policies")
        )

        utc_iso = self._now().isoformat()
        content = json.dumps({
            "sharepoint_settings": sharepoint_settings,
            "sharepoint_status": sharepoint_status,
            "conditional_access_policies": ca_policies,
            "fetched_at": utc_iso,
        }, sort_keys=True).encode("utf-8")

        return PulledEvidence(
            filename=f"m365_mp_3_8_2_{utc_iso}.json",
            content=content,
            mime_type="application/json",
            description=(
                "Digital media access: tenant SharePoint sharing posture and "
                "Conditional Access policies. Per-site sharing capability is "
                "not exposed by Microsoft Graph v1.0 — see missing_sources."
            ),
            control_ids=["MP.L2-3.8.2"],
            metadata={
                "media_scope": "digital",
                "endpoints": [
                    "/admin/sharepoint/settings",
                    "/identity/conditionalAccess/policies",
                ],
                "ca_policy_count": len(ca_policies),
                "sharepoint_status": sharepoint_status,
            },
            coverage_scope="partial",
            missing_sources=["per_site_sharing"],
            degraded=(sharepoint_status != "ok"),
            degradation_reason=sharepoint_degradation_reason,
        )

    def _pull_ac_3_1_3(self, client: MsGraphClient) -> PulledEvidence | None:
        """AC.L2-3.1.3 — Control CUI Flow (partial).

        Two Graph endpoints compose this evidence:
          /identity/conditionalAccess/policies                    (paginated)
          /beta/security/informationProtection/sensitivityLabels  (paginated, beta)

        Conditional Access policies enforce CUI-flow restrictions through
        session controls, cloud-app filters, and location restrictions.
        Sensitivity labels classify data so flow controls can target CUI
        specifically. Together they constitute Graph-observable CUI-flow
        evidence.

        coverage_scope="partial". missing_sources after F.3b:
          - dlp_policies:    permanently deferred (no Graph endpoint;
                             enumeration is PowerShell-only via
                             Get-DlpCompliancePolicy)
          - label_policies:  permanently deferred (no Graph endpoint;
                             enumeration is PowerShell-only via
                             Get-LabelPolicy)
        Both DLP and label-policy enumeration would land in a hypothetical
        Phase 5.4 PowerShell shim, out of Pass F scope entirely.

        Capability-gap handling on sensitivity labels: when Purview is
        unprovisioned (400 + BadRequest), the sub-component degrades but
        CA still yields. CA is core Entra and works on tenants without
        Purview.
        """
        ca_policies = list(
            client.paginate("/identity/conditionalAccess/policies")
        )

        # Sensitivity labels — capability-gap-conditional (Purview /
        # Information Protection licensing).
        sensitivity_labels: list[dict] = []
        sensitivity_label_status: str = "ok"
        sensitivity_label_degradation_reason: str | None = None
        try:
            sensitivity_labels = list(
                client.paginate(
                    "/beta/security/informationProtection/sensitivityLabels"
                )
            )
        except MsGraphCapabilityError as exc:
            sensitivity_label_status = "service_unavailable"
            sensitivity_label_degradation_reason = (
                f"Purview / Information Protection unavailable on tenant: {exc}"
            )
            log.warning(
                "Sensitivity labels unavailable; emitting degraded evidence "
                "for AC.L2-3.1.3",
                extra={
                    "tenant_id": self._tenant_id,
                    "endpoint": "/beta/security/informationProtection/sensitivityLabels",
                },
            )
        except MsGraphPermissionError as exc:
            if exc.licensing_signal:
                sensitivity_label_status = "license_not_detected"
                sensitivity_label_degradation_reason = (
                    "Purview / Information Protection license not detected"
                )
                log.warning(
                    "Purview license not detected; emitting degraded evidence "
                    "for AC.L2-3.1.3",
                    extra={
                        "tenant_id": self._tenant_id,
                        "endpoint": "/beta/security/informationProtection/sensitivityLabels",
                    },
                )
            else:
                raise

        utc_iso = self._now().isoformat()
        content = json.dumps({
            "conditional_access_policies": ca_policies,
            "sensitivity_labels": sensitivity_labels,
            "sensitivity_label_status": sensitivity_label_status,
            "fetched_at": utc_iso,
        }, sort_keys=True).encode("utf-8")

        return PulledEvidence(
            filename=f"m365_ac_3_1_3_{utc_iso}.json",
            content=content,
            mime_type="application/json",
            description=(
                "CUI-flow controls (partial): Conditional Access policies "
                "and sensitivity labels. DLP policies and label policies "
                "require PowerShell shim (out of Pass F scope) — see "
                "missing_sources."
            ),
            control_ids=["AC.L2-3.1.3"],
            metadata={
                "endpoints": [
                    "/identity/conditionalAccess/policies",
                    "/beta/security/informationProtection/sensitivityLabels",
                ],
                "ca_policy_count": len(ca_policies),
                "sensitivity_label_count": len(sensitivity_labels),
                "sensitivity_label_status": sensitivity_label_status,
            },
            coverage_scope="partial",
            missing_sources=[
                "dlp_policies",
                "label_policies",
            ],
            degraded=(sensitivity_label_status != "ok"),
            degradation_reason=sensitivity_label_degradation_reason,
        )

    def _pull_sc_3_13_8(self, client: MsGraphClient) -> PulledEvidence | None:
        """SC.L2-3.13.8 — Data in Transit (mixed-directness).

        Four Graph endpoints compose this evidence; the headline signal is
        Microsoft's Secure Score (aggregate by definition), so the parent
        PulledEvidence carries evidence_directness="aggregate". The CA-
        filter and label-encryption sub-components are raw_config but live
        in metadata as supporting evidence.

          /security/secureScores               (paginated, aggregate)
          /security/secureScoreControlProfiles (paginated, profile metadata
                                                for filtering scores)
          /identity/conditionalAccess/policies (paginated, REUSE — filtered
                                                for TLS / app-protection)
          /beta/security/informationProtection/sensitivityLabels
                                               (paginated, REUSE — filtered
                                                for encryption-bearing labels)

        coverage_scope="partial", missing_sources=["exchange_online_tls"].
        Exchange Online transport rules require PowerShell (Get-TransportRule
        + Get-TlsReceiveDomainSecureList), out of Pass F scope.

        Capability-gap handling: Secure Score and sensitivity labels are
        each independently capability-gap-conditional. CA always works on
        a working tenant. Both capability-gapped sub-components flag the
        parent degraded=True with combined reason.

        TLS-relevance filter on control profiles is conservative; F.4
        against a Defender-provisioned tenant validates the discriminator.
        """
        # Secure Score — aggregate, capability-gap-conditional.
        secure_scores: list[dict] = []
        secure_score_status: str = "ok"
        secure_score_degradation_reason: str | None = None
        try:
            secure_scores = list(client.paginate("/security/secureScores"))
        except MsGraphCapabilityError as exc:
            secure_score_status = "service_unavailable"
            secure_score_degradation_reason = (
                f"Microsoft Secure Score unavailable on tenant: {exc}"
            )
            log.warning(
                "Secure Score unavailable; emitting degraded evidence "
                "for SC.L2-3.13.8",
                extra={
                    "tenant_id": self._tenant_id,
                    "endpoint": "/security/secureScores",
                },
            )
        except MsGraphPermissionError as exc:
            if exc.licensing_signal:
                secure_score_status = "license_not_detected"
                secure_score_degradation_reason = (
                    "Microsoft Secure Score license (Defender) not detected"
                )
                log.warning(
                    "Defender license not detected; emitting degraded "
                    "Secure Score evidence for SC.L2-3.13.8",
                    extra={"tenant_id": self._tenant_id},
                )
            else:
                raise

        # Control profiles — separately capability-gap-conditional. Often
        # available even when Secure Score data is empty (profile metadata
        # is largely tenant-independent).
        control_profiles: list[dict] = []
        try:
            control_profiles = list(
                client.paginate("/security/secureScoreControlProfiles")
            )
        except MsGraphCapabilityError as exc:
            log.warning(
                "Secure Score control profiles unavailable; continuing without",
                extra={
                    "tenant_id": self._tenant_id,
                    "endpoint": "/security/secureScoreControlProfiles",
                },
            )
        except MsGraphPermissionError as exc:
            if exc.licensing_signal:
                log.warning(
                    "Defender license not detected for control profiles; "
                    "continuing without",
                    extra={"tenant_id": self._tenant_id},
                )
            else:
                raise

        # CA — always works on a working tenant.
        ca_policies = list(
            client.paginate("/identity/conditionalAccess/policies")
        )

        # Sensitivity labels — capability-gap-conditional.
        sensitivity_labels: list[dict] = []
        sensitivity_label_status: str = "ok"
        sensitivity_label_degradation_reason: str | None = None
        try:
            sensitivity_labels = list(
                client.paginate(
                    "/beta/security/informationProtection/sensitivityLabels"
                )
            )
        except MsGraphCapabilityError as exc:
            sensitivity_label_status = "service_unavailable"
            sensitivity_label_degradation_reason = (
                f"Purview / Information Protection unavailable on tenant: {exc}"
            )
            log.warning(
                "Sensitivity labels unavailable; emitting degraded evidence "
                "for SC.L2-3.13.8",
                extra={
                    "tenant_id": self._tenant_id,
                    "endpoint": "/beta/security/informationProtection/sensitivityLabels",
                },
            )
        except MsGraphPermissionError as exc:
            if exc.licensing_signal:
                sensitivity_label_status = "license_not_detected"
                sensitivity_label_degradation_reason = (
                    "Purview / Information Protection license not detected"
                )
                log.warning(
                    "Purview license not detected for SC.L2-3.13.8",
                    extra={"tenant_id": self._tenant_id},
                )
            else:
                raise

        # TLS-relevance filter on control profiles. Conservative — minimizes
        # false positives on the trial. F.4 against a Defender-provisioned
        # tenant validates the discriminator. Service set anchors data-in-
        # transit-relevant services; controlCategory or title-substring
        # broadens within those services.
        TLS_RELEVANT_SERVICES = {"Exchange", "SharePoint", "OneDrive"}
        TLS_KEYWORDS = ("tls", "encrypt", "transport")

        def _profile_is_tls_relevant(profile: dict) -> bool:
            service = profile.get("service") or ""
            if service not in TLS_RELEVANT_SERVICES:
                return False
            if profile.get("controlCategory") == "Data":
                return True
            title = (profile.get("title") or "").lower()
            return any(kw in title for kw in TLS_KEYWORDS)

        tls_relevant_profiles = [
            p for p in control_profiles if _profile_is_tls_relevant(p)
        ]

        # Encryption-bearing labels for SC.L2-3.13.8 (data IN TRANSIT being
        # encrypted via label policy). The shape uncertainty (per Phase 1.f:
        # protectionSettings.encryptContent vs actionSettings[].@odata.type)
        # is handled by a defensive both-shape match. F.4 against a Purview-
        # provisioned tenant disambiguates.
        encryption_labels = [
            l for l in sensitivity_labels if _label_has_encryption(l)
        ]

        utc_iso = self._now().isoformat()
        content = json.dumps({
            "secure_scores": secure_scores,
            "secure_score_control_profiles_full": control_profiles,
            "secure_score_control_profiles_tls_relevant": tls_relevant_profiles,
            "conditional_access_policies": ca_policies,
            "sensitivity_labels_with_encryption": encryption_labels,
            "secure_score_status": secure_score_status,
            "sensitivity_label_status": sensitivity_label_status,
            "fetched_at": utc_iso,
        }, sort_keys=True).encode("utf-8")

        # Compose parent degradation_reason from any non-"ok" sub-components.
        degradation_reasons = [
            r for r in (
                secure_score_degradation_reason,
                sensitivity_label_degradation_reason,
            )
            if r is not None
        ]
        degraded = bool(degradation_reasons)
        combined_reason = " | ".join(degradation_reasons) if degradation_reasons else None

        return PulledEvidence(
            filename=f"m365_sc_3_13_8_{utc_iso}.json",
            content=content,
            mime_type="application/json",
            description=(
                "Data in transit (aggregate): Microsoft Secure Score with "
                "TLS-relevant control breakdown, plus supporting raw_config "
                "from Conditional Access (TLS / app-protection slice) and "
                "encryption-bearing sensitivity labels. Exchange Online "
                "transport rules require PowerShell shim (out of Pass F "
                "scope) — see missing_sources."
            ),
            control_ids=["SC.L2-3.13.8"],
            metadata={
                "endpoints": [
                    "/security/secureScores",
                    "/security/secureScoreControlProfiles",
                    "/identity/conditionalAccess/policies",
                    "/beta/security/informationProtection/sensitivityLabels",
                ],
                "secure_score_count": len(secure_scores),
                "control_profile_count": len(control_profiles),
                "tls_relevant_profile_count": len(tls_relevant_profiles),
                "ca_policy_count": len(ca_policies),
                "sensitivity_label_count": len(sensitivity_labels),
                "encryption_label_count": len(encryption_labels),
                "secure_score_status": secure_score_status,
                "sensitivity_label_status": sensitivity_label_status,
            },
            coverage_scope="partial",
            missing_sources=["exchange_online_tls"],
            evidence_directness="aggregate",
            degraded=degraded,
            degradation_reason=combined_reason,
        )
