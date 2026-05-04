"""Live verification harness for EntraIdConnector against a real Entra tenant.

Bypasses the connector framework's runner, storage, and DB layers. Directly
instantiates EntraIdConnector, calls test_connection(), and calls a subset of
the _pull_<control>() methods to capture real Microsoft Graph response shapes
for comparison against hand-built fixtures.

Read-only against Graph. No DB writes. No platform storage. The only file
produced is a markdown report of the run.

Gates:
  - ENTRA_LIVE_TEST=1 must be set (prevents accidental runs).
  - ENTRA_TEST_TENANT_ID, ENTRA_TEST_CLIENT_ID, ENTRA_TEST_CLIENT_SECRET
    must be set.

Usage (PowerShell):
    $env:ENTRA_LIVE_TEST="1"
    $env:ENTRA_TEST_TENANT_ID="<tenant guid>"
    $env:ENTRA_TEST_CLIENT_ID="<client guid>"
    $env:ENTRA_TEST_CLIENT_SECRET="<secret value>"
    python scripts/verify_entra_id.py [--full]

The --full flag enables all five controls (requires the additional
UserAuthenticationMethod.Read.All and AuditLog.Read.All permissions to
also be granted). Default mode runs the subset-of-three.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.connectors.connectors_builtin.entra_id import EntraIdConnector  # noqa: E402


REDACTED = "<redacted>"
PII_KEYS = {
    "userPrincipalName",
    "displayName",
    "mail",
    "givenName",
    "surname",
    "invitedUserEmailAddress",
    "inviteRedeemUrl",
    "principalDisplayName",
    "preferredLanguage",
    "mobilePhone",
    "businessPhones",
    "jobTitle",
}

# Collections where the top-level `id` field is tenant-specific (PII-adjacent).
# In role_definitions and role_assignments the `id` is Microsoft-public for
# built-in roles (e.g. 62e90394-... = Global Administrator) — leave those alone.
TENANT_SPECIFIC_ID_COLLECTIONS = {"users", "groups", "b2b_invitations", "group_memberships"}


def redact(obj, in_tenant_collection: bool = False):
    """Recursively replace PII values with <redacted>. Returns a copy.

    in_tenant_collection: when True, also redact `id` field at the top level
    (used when redacting a single row from a tenant-specific collection).
    """
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in PII_KEYS and v is not None:
                out[k] = REDACTED
            elif k == "id" and in_tenant_collection and v is not None:
                out[k] = "<redacted-tenant-id>"
            else:
                out[k] = redact(v, in_tenant_collection=False)
        return out
    if isinstance(obj, list):
        return [redact(item, in_tenant_collection=in_tenant_collection) for item in obj]
    return obj


def gate_check():
    """Refuse to run unless gates pass."""
    if os.environ.get("ENTRA_LIVE_TEST") != "1":
        print("ERROR: ENTRA_LIVE_TEST=1 is not set.")
        print("This script makes real network calls to Microsoft Graph.")
        print("Set ENTRA_LIVE_TEST=1 and re-run.")
        sys.exit(1)
    missing = [
        k for k in (
            "ENTRA_TEST_TENANT_ID",
            "ENTRA_TEST_CLIENT_ID",
            "ENTRA_TEST_CLIENT_SECRET",
        ) if not os.environ.get(k)
    ]
    if missing:
        print(f"ERROR: missing env vars: {missing}")
        sys.exit(1)


def load_fixture(name):
    path = ROOT / "tests" / "connectors" / "fixtures" / "entra" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def compare_shape(real_content: bytes, fixture_data: dict, control_id: str) -> list[str]:
    """Return a list of human-readable shape differences."""
    deltas: list[str] = []
    real_parsed = json.loads(real_content.decode("utf-8"))

    if control_id == "AC.L2-3.1.1":
        if real_parsed.get("users"):
            real_keys = set(real_parsed["users"][0].keys())
            fixture_keys = (
                set(fixture_data["users"][0].keys())
                if fixture_data.get("users") else set()
            )
            new_keys = real_keys - fixture_keys
            missing_keys = fixture_keys - real_keys
            if new_keys:
                deltas.append(
                    f"users[0] has {len(new_keys)} keys not in fixture: "
                    f"{sorted(new_keys)}"
                )
            if missing_keys:
                deltas.append(
                    f"users[0] missing fixture keys: {sorted(missing_keys)}"
                )
        if real_parsed.get("groups"):
            real_keys = set(real_parsed["groups"][0].keys())
            fixture_keys = (
                set(fixture_data["groups"][0].keys())
                if fixture_data.get("groups") else set()
            )
            new_keys = real_keys - fixture_keys
            if new_keys:
                deltas.append(
                    f"groups[0] has {len(new_keys)} keys not in fixture: "
                    f"{sorted(new_keys)}"
                )

    elif control_id == "AC.L2-3.1.5":
        for collection in ("role_assignments", "role_definitions"):
            if real_parsed.get(collection):
                real_keys = set(real_parsed[collection][0].keys())
                fixture_keys = (
                    set(fixture_data[collection][0].keys())
                    if fixture_data.get(collection) else set()
                )
                new_keys = real_keys - fixture_keys
                if new_keys:
                    deltas.append(
                        f"{collection}[0] has {len(new_keys)} keys not in "
                        f"fixture: {sorted(new_keys)}"
                    )

    elif control_id == "AC.L2-3.1.20":
        real_policy = real_parsed.get("cross_tenant_access_policy", {})
        fixture_policy = fixture_data.get("cross_tenant_access_policy", {})
        real_keys = set(real_policy.keys()) if isinstance(real_policy, dict) else set()
        fixture_keys = set(fixture_policy.keys()) if isinstance(fixture_policy, dict) else set()
        new_keys = real_keys - fixture_keys
        if new_keys:
            deltas.append(
                f"cross_tenant_access_policy has {len(new_keys)} keys not in "
                f"fixture: {sorted(new_keys)}"
            )
        if real_parsed.get("b2b_invitations"):
            real_keys = set(real_parsed["b2b_invitations"][0].keys())
            fixture_keys = (
                set(fixture_data["b2b_invitations"][0].keys())
                if fixture_data.get("b2b_invitations") else set()
            )
            new_keys = real_keys - fixture_keys
            if new_keys:
                deltas.append(
                    f"b2b_invitations[0] has {len(new_keys)} keys not in "
                    f"fixture: {sorted(new_keys)}"
                )

    return deltas


def run_one_control(connector, client, name, method_name, control_id, fixture_name):
    """Run one _pull_<control>() method and return a result dict."""
    method = getattr(connector, method_name)
    try:
        ev = method(client)
    except Exception as e:
        return {
            "control_id": control_id,
            "name": name,
            "ok": False,
            "error": f"{type(e).__name__}: {e}",
        }
    if ev is None:
        return {
            "control_id": control_id,
            "name": name,
            "ok": True,
            "rows": 0,
            "metadata": {},
            "deltas": [],
            "first_row_redacted": None,
        }
    parsed = json.loads(ev.content.decode("utf-8"))

    # Find the largest list-valued collection in the parsed content for sampling.
    first_row = None
    largest_collection = None
    largest_size = 0
    for k, v in parsed.items():
        if isinstance(v, list) and len(v) > largest_size:
            largest_size = len(v)
            largest_collection = k
    if largest_collection and parsed[largest_collection]:
        is_tenant_specific = largest_collection in TENANT_SPECIFIC_ID_COLLECTIONS
        first_row = redact(parsed[largest_collection][0],
                           in_tenant_collection=is_tenant_specific)

    fixture = load_fixture(fixture_name)
    deltas = compare_shape(ev.content, fixture, control_id)

    return {
        "control_id": control_id,
        "name": name,
        "ok": True,
        "metadata": ev.metadata,
        "filename": ev.filename,
        "deltas": deltas,
        "first_row_collection": largest_collection,
        "first_row_redacted": first_row,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true",
                        help="Run all five controls (requires IA and AU permissions).")
    args = parser.parse_args()

    gate_check()

    started_at = datetime.now(timezone.utc)
    timestamp_str = started_at.strftime("%Y%m%d_%H%M%S")

    connector = EntraIdConnector(
        config={"lookback_hours": 24},
        credentials={
            "tenant_id": os.environ["ENTRA_TEST_TENANT_ID"],
            "client_id": os.environ["ENTRA_TEST_CLIENT_ID"],
            "client_secret": os.environ["ENTRA_TEST_CLIENT_SECRET"],
            "cloud_environment": "commercial",
        },
    )

    results: list[dict] = []
    print(f"=== Pass E.4 live verification - {started_at.isoformat()} ===")
    print(f"Mode: {'FULL (all 5 controls)' if args.full else 'SUBSET-OF-THREE'}")
    print()

    print("--- test_connection() ---")
    ok, msg = connector.test_connection()
    print(f"  ok: {ok}")
    print(f"  msg: {msg}")
    test_result = {"ok": ok, "msg": msg}
    print()

    if not ok:
        print("test_connection failed. Skipping pull controls.")
    else:
        controls = [
            ("Account management",   "_pull_ac_3_1_1",  "AC.L2-3.1.1",  "ac_3_1_1"),
            ("Least privilege",      "_pull_ac_3_1_5",  "AC.L2-3.1.5",  "ac_3_1_5"),
            ("External connections", "_pull_ac_3_1_20", "AC.L2-3.1.20", "ac_3_1_20"),
        ]
        if args.full:
            controls.extend([
                ("MFA",        "_pull_ia_3_5_3",  "IA.L2-3.5.3",  "ia_3_5_3"),
                ("Audit logs", "_pull_au_3_3_1",  "AU.L2-3.3.1",  "au_3_3_1"),
            ])

        with connector._build_client() as client:
            for name, method_name, control_id, fixture_name in controls:
                print(f"--- {control_id} ({name}) ---")
                result = run_one_control(connector, client, name, method_name,
                                         control_id, fixture_name)
                results.append(result)
                if not result["ok"]:
                    print(f"  FAILED: {result['error']}")
                else:
                    print(f"  metadata: {result.get('metadata', {})}")
                    if result.get("deltas"):
                        print(f"  shape deltas:")
                        for d in result["deltas"]:
                            print(f"    - {d}")
                    else:
                        print(f"  shape deltas: none")
                    if result.get("first_row_redacted"):
                        print(f"  first row of {result['first_row_collection']} (redacted):")
                        print("    " + json.dumps(result["first_row_redacted"],
                                                  indent=2, sort_keys=True).replace("\n", "\n    "))
                print()

    finished_at = datetime.now(timezone.utc)

    print("=== Summary ===")
    print(f"  test_connection ok: {test_result['ok']}")
    print(f"  controls run: {len(results)}")
    print(f"  controls succeeded: {sum(1 for r in results if r['ok'])}")
    print(f"  controls with shape deltas: {sum(1 for r in results if r.get('deltas'))}")
    print(f"  duration_seconds: {(finished_at - started_at).total_seconds():.1f}")

    # Markdown report
    report_path = ROOT / "notes" / f"phase5_2_entra_e4_run_{timestamp_str}.md"
    report_path.parent.mkdir(exist_ok=True)
    lines = [
        f"# Pass E.4 live verification run - {started_at.isoformat()}",
        "",
        f"- **Mode:** {'FULL (5 controls)' if args.full else 'SUBSET-OF-THREE'}",
        f"- **Duration:** {(finished_at - started_at).total_seconds():.1f}s",
        f"- **Tenant:** redacted (env-supplied)",
        "",
        "## test_connection()",
        f"- ok: `{test_result['ok']}`",
        f"- msg: `{test_result['msg']}`",
        "",
        "## Per-control results",
        "",
    ]
    for r in results:
        lines.append(f"### {r['control_id']} - {r['name']}")
        if not r["ok"]:
            lines.append(f"- **FAILED:** `{r['error']}`")
        else:
            lines.append(f"- metadata: `{r.get('metadata', {})}`")
            lines.append(f"- shape deltas: {r.get('deltas') or 'none'}")
            if r.get("first_row_redacted"):
                lines.append(f"- first row of `{r['first_row_collection']}` (redacted):")
                lines.append("  ```json")
                for line in json.dumps(r["first_row_redacted"], indent=2, sort_keys=True).split("\n"):
                    lines.append(f"  {line}")
                lines.append("  ```")
        lines.append("")
    lines.append("## Summary")
    lines.append(f"- controls run: {len(results)}")
    lines.append(f"- controls succeeded: {sum(1 for r in results if r['ok'])}")
    lines.append(f"- controls with shape deltas: {sum(1 for r in results if r.get('deltas'))}")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written to: {report_path}")


if __name__ == "__main__":
    main()
