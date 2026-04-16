"""
scripts/reset_demo_data.py

Resets the demo org to a clean post-onboarding state — as if the admin
just completed onboarding but hasn't done intake, generated docs, or
created evidence yet. Useful for demo prep and end-to-end testing.

What it does (all in one transaction):
  * Deletes every org-specific row for the target org across:
      evidence_control_map, evidence_artifacts, ssp_sections, ssp_jobs,
      poam_items, intake_responses, intake_documents, intake_sessions,
      generated_documents, company_profiles.
  * Truncates audit_log and re-seeds the canonical GENESIS entry
    (audit_log has no org_id column — it's a single global chain).
  * Resets users.onboarding_complete = FALSE for admin@intranest.ai so
    the demo starts fresh at the wizard (unless --keep-onboarding).

What it does NOT touch:
  * Reference/seed data: controls, assessment_objectives, frameworks,
    document_templates.
  * The organizations row itself — only its data.
  * The admin user (kept).

Usage (local dev):
    python scripts/reset_demo_data.py                        # reset demo org
    python scripts/reset_demo_data.py --org-id <other>        # different org
    python scripts/reset_demo_data.py --keep-onboarding       # don't re-trigger wizard
    python scripts/reset_demo_data.py --production            # requires typing org name

Never run without --production in a shared environment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional

# Make 'src' / 'configs' importable when this script is run directly.
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Optional colourised output
try:
    from colorama import init as _colorama_init, Fore, Style
    _colorama_init()
    def _c(colour: str, s: str) -> str:  # noqa: E306
        return f"{colour}{s}{Style.RESET_ALL}"
except Exception:  # pragma: no cover
    class _Fake:
        RESET_ALL = CYAN = GREEN = YELLOW = RED = MAGENTA = ""
    Fore = Style = _Fake()  # type: ignore
    def _c(_colour: str, s: str) -> str:  # noqa: E306
        return s


DEMO_ORG_ID_DEFAULT = "9de53b587b23450b87af"
ADMIN_EMAIL = "admin@intranest.ai"


# ── DB connection ───────────────────────────────────────────────────────────

def _build_engine(database_url: Optional[str]):
    """Use the same URL the app reads at runtime."""
    from sqlalchemy import create_engine

    if database_url:
        url = database_url
    else:
        # Mirror the app's import order so a misconfigured .env gives the
        # same answer in both places.
        try:
            from configs.settings import DATABASE_URL as url  # type: ignore
        except Exception:
            url = "postgresql://cmmc:localdev@localhost:5432/cmmc"
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return create_engine(url)


# ── Deletion phases ─────────────────────────────────────────────────────────

def _exec_count(conn, sql: str, params: dict) -> int:
    """Execute a DELETE/UPDATE and return rowcount."""
    from sqlalchemy import text

    res = conn.execute(text(sql), params)
    return res.rowcount or 0


def _delete_org_data(conn, org_id: str) -> dict[str, int]:
    """Returns a dict of {phase_label: rows_deleted} — FK-safe order."""
    counts: dict[str, int] = {}

    # Phase 1 — scans + evidence links + artifacts.
    # scan_findings CASCADE-delete with scan_imports, but deleting
    # scan_imports first releases its FK to evidence_artifacts so the
    # artifact delete that follows doesn't hit an integrity error.
    # baseline_deviations.scan_finding_id FKs into scan_findings, so we
    # drop baseline rows first. The shared catalog (baselines,
    # baseline_items) is deliberately preserved.
    try:
        counts["baseline_deviations"] = _exec_count(
            conn, "DELETE FROM baseline_deviations WHERE org_id = :oid", {"oid": org_id}
        )
        counts["org_baselines"] = _exec_count(
            conn, "DELETE FROM org_baselines WHERE org_id = :oid", {"oid": org_id}
        )
    except Exception:
        counts["baseline_deviations"] = 0
        counts["org_baselines"] = 0

    try:
        counts["scan_findings"] = _exec_count(
            conn, "DELETE FROM scan_findings WHERE org_id = :oid", {"oid": org_id}
        )
        counts["scan_imports"] = _exec_count(
            conn, "DELETE FROM scan_imports WHERE org_id = :oid", {"oid": org_id}
        )
    except Exception:
        # scan tables absent on older DBs — ignore.
        counts["scan_findings"] = 0
        counts["scan_imports"] = 0

    counts["evidence_control_map"] = _exec_count(
        conn,
        """DELETE FROM evidence_control_map
           WHERE evidence_id IN (SELECT id FROM evidence_artifacts WHERE org_id = :oid)""",
        {"oid": org_id},
    )
    counts["evidence_artifacts"] = _exec_count(
        conn,
        "DELETE FROM evidence_artifacts WHERE org_id = :oid",
        {"oid": org_id},
    )

    # Phase 2 — SSP
    # resolutions → claims → observations → ssp_sections. FK CASCADE
    # from claims/observations already drops resolutions, but the
    # explicit DELETE keeps the order obvious and survives a schema
    # where ON DELETE CASCADE might be dropped later.
    try:
        counts["assessment_snapshots"] = _exec_count(
            conn, "DELETE FROM assessment_snapshots WHERE org_id = :oid", {"oid": org_id}
        )
    except Exception:
        counts["assessment_snapshots"] = 0
    try:
        counts["freshness_thresholds"] = _exec_count(
            conn, "DELETE FROM freshness_thresholds WHERE org_id = :oid", {"oid": org_id}
        )
    except Exception:
        counts["freshness_thresholds"] = 0
    try:
        counts["resolutions"] = _exec_count(
            conn, "DELETE FROM resolutions WHERE org_id = :oid", {"oid": org_id}
        )
    except Exception:
        counts["resolutions"] = 0
    try:
        counts["claims"] = _exec_count(
            conn, "DELETE FROM claims WHERE org_id = :oid", {"oid": org_id}
        )
    except Exception:
        counts["claims"] = 0
    try:
        counts["observations"] = _exec_count(
            conn, "DELETE FROM observations WHERE org_id = :oid", {"oid": org_id}
        )
    except Exception:
        counts["observations"] = 0
    counts["ssp_sections"] = _exec_count(
        conn, "DELETE FROM ssp_sections WHERE org_id = :oid", {"oid": org_id}
    )
    counts["ssp_jobs"] = _exec_count(
        conn, "DELETE FROM ssp_jobs WHERE org_id = :oid", {"oid": org_id}
    )

    # Phase 3 — POA&M
    counts["poam_items"] = _exec_count(
        conn, "DELETE FROM poam_items WHERE org_id = :oid", {"oid": org_id}
    )

    # Phase 4 — intake (responses + documents → sessions, FK order matters)
    counts["intake_responses"] = _exec_count(
        conn, "DELETE FROM intake_responses WHERE org_id = :oid", {"oid": org_id}
    )
    counts["intake_documents"] = _exec_count(
        conn, "DELETE FROM intake_documents WHERE org_id = :oid", {"oid": org_id}
    )
    counts["intake_sessions"] = _exec_count(
        conn, "DELETE FROM intake_sessions WHERE org_id = :oid", {"oid": org_id}
    )

    # Phase 5 — generated_documents
    counts["generated_documents"] = _exec_count(
        conn, "DELETE FROM generated_documents WHERE org_id = :oid", {"oid": org_id}
    )

    # Phase 6 — company_profiles
    counts["company_profiles"] = _exec_count(
        conn, "DELETE FROM company_profiles WHERE org_id = :oid", {"oid": org_id}
    )

    # Phase 6b — contradictions (2.9A table; included so demos start clean)
    try:
        counts["intake_contradictions"] = _exec_count(
            conn, "DELETE FROM intake_contradictions WHERE org_id = :oid", {"oid": org_id}
        )
    except Exception:
        # Table absent on very old DBs — ignore.
        counts["intake_contradictions"] = 0

    return counts


def _reset_audit_log(conn) -> None:
    """Wipe audit_log entirely and re-seed the canonical GENESIS row.

    Uses src.evidence.state_machine._compute_entry_hash so the single global
    chain stays verifiable end-to-end after the reset.
    """
    from sqlalchemy import text
    from src.evidence.state_machine import _compute_entry_hash

    # TRUNCATE resets the SERIAL sequence so the new genesis row is id=1.
    conn.execute(text("TRUNCATE audit_log RESTART IDENTITY"))

    now = datetime.now(timezone.utc)
    timestamp_iso = now.isoformat()
    details = {"message": "Audit chain genesis"}
    entry_hash = _compute_entry_hash(
        actor="SYSTEM",
        actor_type="system",
        action="GENESIS",
        target_type="system",
        target_id="system",
        details=details,
        prev_hash="GENESIS",
        timestamp=timestamp_iso,
    )
    conn.execute(text("""
        INSERT INTO audit_log
            (timestamp, actor, actor_type, action, target_type, target_id,
             details, prev_hash, entry_hash)
        VALUES
            (:ts, 'SYSTEM', 'system', 'GENESIS', 'system', 'system',
             CAST(:details AS json), 'GENESIS', :entry_hash)
    """), {
        "ts": now,
        "details": json.dumps(details),
        "entry_hash": entry_hash,
    })


def _reset_admin_onboarding(conn) -> int:
    from sqlalchemy import text

    res = conn.execute(
        text("UPDATE users SET onboarding_complete = FALSE WHERE email = :email"),
        {"email": ADMIN_EMAIL},
    )
    return res.rowcount or 0


def _verify_org_exists(conn, org_id: str) -> Optional[str]:
    from sqlalchemy import text

    row = conn.execute(
        text("SELECT name FROM organizations WHERE id = :oid"),
        {"oid": org_id},
    ).fetchone()
    return row[0] if row else None


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reset the demo org to a clean post-onboarding state.",
    )
    parser.add_argument(
        "--org-id",
        default=DEMO_ORG_ID_DEFAULT,
        help=f"Target organization id (default: {DEMO_ORG_ID_DEFAULT})",
    )
    parser.add_argument(
        "--database-url",
        help="Override DATABASE_URL / configs.settings.DATABASE_URL.",
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Require typing the org name to confirm. Use this on shared envs.",
    )
    parser.add_argument(
        "--keep-onboarding",
        action="store_true",
        help="Skip resetting users.onboarding_complete for admin.",
    )
    args = parser.parse_args()

    engine = _build_engine(args.database_url)

    # Preflight — make sure the org exists before we start wiping things.
    with engine.connect() as conn:
        org_name = _verify_org_exists(conn, args.org_id)
    if not org_name:
        print(_c(Fore.RED, f"ERROR: organization {args.org_id} not found. Aborting."))
        sys.exit(1)

    print(_c(Fore.CYAN, "=" * 60))
    print(_c(Fore.CYAN, f"  Reset demo data for: {org_name} ({args.org_id})"))
    print(_c(Fore.CYAN, "=" * 60))

    if args.production:
        typed = input(
            f"\nThis will wipe ALL operational data for '{org_name}'. "
            f"Type the org name to confirm: "
        ).strip()
        if typed != org_name:
            print(_c(Fore.RED, "Name did not match. Aborting."))
            sys.exit(1)

    # Single transaction for all phases — rollback on any error.
    try:
        with engine.begin() as conn:
            print()
            counts = _delete_org_data(conn, args.org_id)

            phase_order = [
                ("scan_findings",        1),
                ("scan_imports",         1),
                ("evidence_control_map", 1),
                ("evidence_artifacts",   1),
                ("ssp_sections",         2),
                ("ssp_jobs",             2),
                ("poam_items",           3),
                ("intake_responses",     4),
                ("intake_documents",     4),
                ("intake_sessions",      4),
                ("generated_documents",  5),
                ("company_profiles",     6),
                ("intake_contradictions", 6),
            ]
            for table, phase in phase_order:
                n = counts.get(table, 0)
                prefix = _c(Fore.GREEN, f"  [Phase {phase}]")
                print(f"{prefix} Deleted {_c(Fore.YELLOW, str(n))} rows from {table}")

            # Phase 7 — audit log
            _reset_audit_log(conn)
            print(_c(Fore.GREEN, "  [Phase 7]") + " Truncated audit_log and re-seeded GENESIS")

            # Phase 8 — onboarding reset
            if args.keep_onboarding:
                print(_c(Fore.MAGENTA, "  [Phase 8]") + " Skipped onboarding reset (--keep-onboarding)")
            else:
                n = _reset_admin_onboarding(conn)
                print(
                    _c(Fore.GREEN, "  [Phase 8]") +
                    f" Reset onboarding_complete=FALSE for {ADMIN_EMAIL} ({n} row)"
                )

    except Exception as exc:
        print()
        print(_c(Fore.RED, f"FAILED — rolled back everything: {exc}"))
        raise

    print()
    print(_c(Fore.CYAN, "=" * 60))
    print(_c(Fore.GREEN, f"Reset complete. Org {args.org_id} is ready for a fresh demo."))
    print(_c(Fore.CYAN, "=" * 60))


if __name__ == "__main__":
    main()
