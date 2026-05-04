"""Microsoft Entra ID connector.

Pulls evidence from Microsoft Graph using the OAuth2 client-credentials flow
for Application API permissions. Supports commercial Microsoft Graph as well
as GCC High and DoD national clouds.

Pass E.2 ships the class skeleton and test_connection() only.
Pass E.3 will implement pull() across five CMMC controls:
  AC.L2-3.1.1, IA.L2-3.5.3, AC.L2-3.1.5, AU.L2-3.3.1, AC.L2-3.1.20
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Iterator

from src.connectors.base import BaseConnector, PulledEvidence
from src.connectors.registry import register
from src.connectors._msgraph import (
    MsGraphClient,
    MsGraphError,
    MsGraphAuthError,
    MsGraphPermissionError,
    format_pull_error,
)

log = logging.getLogger(__name__)


@register
class EntraIdConnector(BaseConnector):
    """Microsoft Entra ID connector -- client-credentials flow."""

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
                "-> Identity -> Overview -> 'Tenant ID'."
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
                "creating the app registration in Entra -> App registrations, "
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
                "The secret VALUE created under Certificates & secrets -> New "
                "client secret. Copy immediately -- Entra hides it after the "
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
        """Construct the connector. Does NOT acquire a token -- that happens
        lazily on the first call to test_connection() or pull().
        """
        super().__init__(config, credentials)

        # Required credentials. Missing keys -> KeyError, which the runner
        # catches and converts to a FAILED run with a useful message.
        # Don't validate format here -- MSAL/Graph rejects malformed inputs
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

        # Per-control errors accumulated during pull(), surfaced via
        # get_pull_errors() per the Pass E.3b contract.
        self._pull_errors: list[str] = []

    @staticmethod
    def _clamp_lookback_hours(raw_value) -> int:
        """Clamp lookback_hours to [1, 168] (one hour to one week).

        Out-of-range or non-integer values are clamped with a warning rather
        than rejected. The customer might set lookback_hours via direct DB
        write before any UI exists for it; we don't want a typo to crash
        every pull. Per discovery section 10 Q11.

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
        context manager. Token acquisition is lazy -- happens on first
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
                            "rows. This is unusual -- verify the tenant is "
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
                        f"Grant it in Entra -> App registrations -> API permissions, "
                        f"then click 'Grant admin consent'.")
            return (False, f"Connected, but Graph returned 403: {e}")

        except MsGraphError as e:
            return (False, f"Microsoft Graph error: {e}")

        except Exception as e:  # noqa: BLE001
            # Last-resort catch -- BaseConnector contract requires no raises
            # from test_connection(). Log without secrets and return failure.
            log.exception("entra_id test_connection unexpected error",
                          extra={"tenant_id": self._tenant_id})
            return (False, f"Unexpected error: {type(e).__name__}: {e}")

    def pull(self) -> Iterator[PulledEvidence]:
        """Pull evidence from Microsoft Graph for five CMMC controls.

        Per-control errors are caught and accumulated on self._pull_errors
        (surfaced via get_pull_errors() per the Pass E.3b contract). One
        failing control does NOT abort the others.

        Errors during MsGraphClient construction or token acquisition kill
        the entire pull (caught at the runner's outer scope, run -> FAILED).
        Errors inside individual _pull_<control>() methods are isolated.
        """
        # Reset accumulator at start of each pull. Per-run-fresh-instance
        # guarantee makes this belt-and-suspenders, but the discipline
        # protects against future runner refactors.
        self._pull_errors = []

        # Tuple shape: (control_id, endpoint_summary, method).
        # endpoint_summary is the string used in format_pull_error for
        # diagnostic output -- not a real URL.
        controls = [
            ("AC.L2-3.1.1",  "/users,/groups",                              self._pull_ac_3_1_1),
            ("IA.L2-3.5.3",  "/conditionalAccess,/authentication/methods",  self._pull_ia_3_5_3),
            ("AC.L2-3.1.5",  "/roleManagement",                             self._pull_ac_3_1_5),
            ("AU.L2-3.3.1",  "/auditLogs",                                  self._pull_au_3_3_1),
            ("AC.L2-3.1.20", "/crossTenantAccessPolicy,/invitations",       self._pull_ac_3_1_20),
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

    def _pull_ac_3_1_1(self, client: MsGraphClient) -> PulledEvidence | None:
        """AC.L2-3.1.1 -- users, groups, group memberships."""
        users = list(client.paginate(
            "/users?$select=id,displayName,userPrincipalName,userType,accountEnabled"
        ))
        groups = list(client.paginate(
            "/groups?$select=id,displayName,groupTypes,securityEnabled,mailEnabled"
        ))

        # Per-group membership fetch. A single group's membership failure
        # (e.g., a synced group with broken Graph state) shouldn't kill the
        # whole control. Track skipped groups for visibility but continue.
        memberships: list[dict] = []
        skipped_groups: list[str] = []
        for group in groups:
            gid = group["id"]
            try:
                members = list(client.paginate(
                    f"/groups/{gid}/members?$select=id"
                ))
                memberships.append({
                    "group_id": gid,
                    "members": [{"id": m["id"]} for m in members],
                })
            except Exception as e:  # noqa: BLE001
                log.warning(
                    "skipping group membership fetch",
                    extra={
                        "group_id": gid,
                        "error_class": type(e).__name__,
                        "error": str(e),
                    },
                )
                skipped_groups.append(gid)
                continue

        utc_iso = self._now().isoformat()
        content = json.dumps({
            "users": users,
            "groups": groups,
            "group_memberships": memberships,
            "skipped_groups": skipped_groups,
            "fetched_at": utc_iso,
        }, sort_keys=True).encode("utf-8")

        return PulledEvidence(
            filename=f"entra_users_groups_{utc_iso}.json",
            content=content,
            mime_type="application/json",
            description="Users, groups, and group memberships from Microsoft Entra ID.",
            control_ids=["AC.L2-3.1.1"],
            metadata={
                "endpoints": ["/users", "/groups", "/groups/{id}/members"],
                "user_count": len(users),
                "group_count": len(groups),
                "membership_count": sum(len(m["members"]) for m in memberships),
                "skipped_group_count": len(skipped_groups),
            },
        )

    def _pull_ia_3_5_3(self, client: MsGraphClient) -> PulledEvidence | None:
        """IA.L2-3.5.3 -- conditional access policies and per-user auth methods."""
        policies = list(client.paginate(
            "/identity/conditionalAccess/policies"
        ))

        # Per-user authentication methods. ~2 + N calls (N = user count).
        # For Apex (45 users), ~47 calls. Acceptable for Pass E; $batch
        # refactor is Pass I work.
        users = list(client.paginate("/users?$select=id"))
        user_auth_methods: list[dict] = []
        skipped_users: list[str] = []
        for user in users:
            uid = user["id"]
            try:
                methods = list(client.paginate(
                    f"/users/{uid}/authentication/methods"
                ))
                user_auth_methods.append({
                    "user_id": uid,
                    "methods": methods,
                })
            except Exception as e:  # noqa: BLE001
                log.warning(
                    "skipping user auth methods fetch",
                    extra={
                        "user_id": uid,
                        "error_class": type(e).__name__,
                        "error": str(e),
                    },
                )
                skipped_users.append(uid)
                continue

        utc_iso = self._now().isoformat()
        content = json.dumps({
            "conditional_access_policies": policies,
            "user_authentication_methods": user_auth_methods,
            "skipped_users": skipped_users,
            "fetched_at": utc_iso,
        }, sort_keys=True).encode("utf-8")

        return PulledEvidence(
            filename=f"entra_mfa_{utc_iso}.json",
            content=content,
            mime_type="application/json",
            description="Conditional access policies and per-user authentication methods.",
            control_ids=["IA.L2-3.5.3"],
            metadata={
                "endpoints": [
                    "/identity/conditionalAccess/policies",
                    "/users",
                    "/users/{id}/authentication/methods",
                ],
                "policy_count": len(policies),
                "users_examined": len(user_auth_methods),
                "skipped_user_count": len(skipped_users),
            },
        )

    def _pull_ac_3_1_5(self, client: MsGraphClient) -> PulledEvidence | None:
        """AC.L2-3.1.5 -- privileged role assignments."""
        role_assignments = list(client.paginate(
            "/roleManagement/directory/roleAssignments"
            "?$select=id,principalId,roleDefinitionId,directoryScopeId"
        ))
        role_definitions = list(client.paginate(
            "/roleManagement/directory/roleDefinitions"
            "?$select=id,displayName,isBuiltIn"
        ))

        utc_iso = self._now().isoformat()
        content = json.dumps({
            "role_assignments": role_assignments,
            "role_definitions": role_definitions,
            "fetched_at": utc_iso,
        }, sort_keys=True).encode("utf-8")

        # Roles observed = unique roleDefinitionIds in assignments.
        roles_observed = sorted({
            a.get("roleDefinitionId") for a in role_assignments
            if a.get("roleDefinitionId")
        })

        return PulledEvidence(
            filename=f"entra_role_assignments_{utc_iso}.json",
            content=content,
            mime_type="application/json",
            description="Privileged role assignments and role definitions from Entra ID.",
            control_ids=["AC.L2-3.1.5"],
            metadata={
                "endpoints": [
                    "/roleManagement/directory/roleAssignments",
                    "/roleManagement/directory/roleDefinitions",
                ],
                "assignment_count": len(role_assignments),
                "definition_count": len(role_definitions),
                "roles_observed": roles_observed,
            },
        )

    def _pull_au_3_3_1(self, client: MsGraphClient) -> PulledEvidence | None:
        """AU.L2-3.3.1 -- sign-in and directory audit logs for the lookback window."""
        now = self._now()
        window_end = now
        window_start = now - timedelta(hours=self._lookback_hours)

        # Microsoft Graph's $filter on createdDateTime requires ISO 8601 with
        # explicit Z. Python's .isoformat() emits +00:00 for UTC; we replace
        # to Z for Graph compatibility.
        start_iso = window_start.isoformat().replace("+00:00", "Z")

        sign_ins = list(client.paginate(
            f"/auditLogs/signIns?$filter=createdDateTime ge {start_iso}"
            f"&$top=1000"
        ))
        directory_audits = list(client.paginate(
            f"/auditLogs/directoryAudits?$filter=activityDateTime ge {start_iso}"
            f"&$top=1000"
        ))

        utc_iso = now.isoformat()
        content = json.dumps({
            "sign_ins": sign_ins,
            "directory_audits": directory_audits,
            "lookback_hours": self._lookback_hours,
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "fetched_at": utc_iso,
        }, sort_keys=True).encode("utf-8")

        return PulledEvidence(
            filename=f"entra_audit_logs_{self._lookback_hours}h_{utc_iso}.json",
            content=content,
            mime_type="application/json",
            description=(
                f"Sign-in and directory audit logs for the last "
                f"{self._lookback_hours}h."
            ),
            control_ids=["AU.L2-3.3.1"],
            metadata={
                "endpoints": ["/auditLogs/signIns", "/auditLogs/directoryAudits"],
                "sign_in_count": len(sign_ins),
                "audit_count": len(directory_audits),
                "lookback_hours": self._lookback_hours,
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
            },
        )

    def _pull_ac_3_1_20(self, client: MsGraphClient) -> PulledEvidence | None:
        """AC.L2-3.1.20 -- external collaboration settings and B2B invitations."""
        # /policies/crossTenantAccessPolicy/default returns a SINGLE OBJECT,
        # not a collection. Use client.get, not client.paginate.
        cross_tenant_policy = client.get(
            "/policies/crossTenantAccessPolicy/default"
        )

        # /invitations IS a collection -- paginate.
        invitations = list(client.paginate(
            "/invitations?$select=id,inviteRedeemUrl,invitedUserEmailAddress,"
            "status,invitedUserType"
        ))

        utc_iso = self._now().isoformat()
        content = json.dumps({
            "cross_tenant_access_policy": cross_tenant_policy,
            "b2b_invitations": invitations,
            "fetched_at": utc_iso,
        }, sort_keys=True).encode("utf-8")

        return PulledEvidence(
            filename=f"entra_external_collab_{utc_iso}.json",
            content=content,
            mime_type="application/json",
            description="Cross-tenant access policy and B2B invitation history.",
            control_ids=["AC.L2-3.1.20"],
            metadata={
                "endpoints": [
                    "/policies/crossTenantAccessPolicy/default",
                    "/invitations",
                ],
                "invitation_count": len(invitations),
            },
        )
