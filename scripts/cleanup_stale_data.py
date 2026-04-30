"""
Transactional cleanup of stale test data on Render production Postgres.

Usage:
    DATABASE_URL=<render-external-url> python scripts/cleanup_stale_data.py
    DATABASE_URL=<render-external-url> python scripts/cleanup_stale_data.py --commit

Default: dry-run. Runs every DELETE inside a single transaction and
ROLLs BACK at the end so nothing changes. Pass --commit to COMMIT instead.

Preserves:
  - Apex Defense Solutions (9de53b587b23450b87af) — admin@intranest.ai's
    home org (resolved at runtime; collapses to Apex if admin lives there)
  - Any other org admin@intranest.ai is in
  - audit_log (append-only, hash-chained — never touched)

Test orgs identified by:
  - name LIKE 'Playwright Test Corp %'
  - name = 'Test Company'
  - name LIKE 'Test Corp%'
  - name = 'Test Org'
  - name = 'Meridian Aerospace Components, LLC'  (verification harness fixtures)
  - id IN DUPLICATE_ORG_IDS                       (hardcoded duplicates)
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text


PRESERVED_APEX_ID = "9de53b587b23450b87af"

# Hardcoded duplicate org IDs — confirmed in inventory output 2026-04-30.
# These are orgs that share a name with a preserved org but are test
# artifacts (e.g. duplicate "IntraNest" created during invite-flow testing).
DUPLICATE_ORG_IDS = ["d92e417a08c3c646c7d2"]

COUNT_TABLES = [
    "organizations",
    "users",
    "invites",
    "evidence_artifacts",
    "evidence_control_map",
    "ssp_sections",
    "ssp_jobs",
    "poam_items",
    "generated_documents",
    "intake_sessions",
    "intake_responses",
    "intake_documents",
    "intake_contradictions",
    "company_profiles",
    "contact_requests",
    "scan_imports",
    "scan_findings",
    "baseline_deviations",
    "org_baselines",
    "claims",
    "observations",
    "resolutions",
    "affirmations",
    "assessment_snapshots",
    "export_records",
    "freshness_thresholds",
]


def _scalar(conn, sql: str, **params) -> int:
    return conn.execute(text(sql), params).scalar() or 0


def _rows(conn, sql: str, **params):
    return conn.execute(text(sql), params).fetchall()


def _table_counts(conn) -> dict[str, int]:
    out = {}
    for t in COUNT_TABLES:
        try:
            out[t] = _scalar(conn, f"SELECT COUNT(*) FROM {t}")
        except Exception:
            out[t] = -1
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true",
                        help="Actually COMMIT the transaction. Without this, ROLLBACK.")
    args = parser.parse_args()

    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        print("ABORT: DATABASE_URL not set.", file=sys.stderr)
        return 2
    if "localhost" in db_url or "127.0.0.1" in db_url:
        print("ABORT: DATABASE_URL points at localhost — refusing to run.", file=sys.stderr)
        return 2

    print(f"DATABASE_URL host: {db_url.split('@')[-1].split('/')[0].split('?')[0]}")
    print(f"Run timestamp:     {datetime.now(timezone.utc).isoformat()}")
    print(f"Mode:              {'COMMIT' if args.commit else 'DRY RUN (will rollback)'}")
    print()

    engine = create_engine(db_url, pool_pre_ping=True)
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # ── Resolve preserved org_ids ────────────────────────────────
            admin_row = conn.execute(text("""
                SELECT u.org_id, o.name
                FROM users u LEFT JOIN organizations o ON u.org_id = o.id
                WHERE u.email = 'admin@intranest.ai'
            """)).fetchone()
            if admin_row is None:
                print("ABORT: admin@intranest.ai not found — refusing to proceed.",
                      file=sys.stderr)
                trans.rollback()
                return 2

            preserved_ids = [PRESERVED_APEX_ID]
            if admin_row[0] not in preserved_ids:
                preserved_ids.append(admin_row[0])

            print(f"PRESERVED_ORG_IDS = {preserved_ids}")
            print(f"  - {PRESERVED_APEX_ID}: Apex Defense Solutions")
            for oid in preserved_ids[1:]:
                row = _rows(conn, "SELECT name FROM organizations WHERE id = :id", id=oid)
                print(f"  - {oid}: {row[0][0] if row else '?'}")
            print()

            # ── Snapshot BEFORE counts ───────────────────────────────────
            before = _table_counts(conn)

            # ── Identify test orgs ───────────────────────────────────────
            pattern_orgs = _rows(conn, """
                SELECT id, name FROM organizations
                WHERE (
                    name LIKE 'Playwright Test Corp %'
                    OR name = 'Test Company'
                    OR name LIKE 'Test Corp%'
                    OR name = 'Test Org'
                    OR name = 'Meridian Aerospace Components, LLC'
                    OR name ILIKE '%test%'
                )
                AND id <> ALL(:preserved)
                ORDER BY name
            """, preserved=preserved_ids)

            duplicate_orgs = _rows(conn, """
                SELECT id, name FROM organizations
                WHERE id = ANY(:dups) AND id <> ALL(:preserved)
            """, dups=DUPLICATE_ORG_IDS, preserved=preserved_ids)

            test_org_ids = list({r[0] for r in pattern_orgs} | {r[0] for r in duplicate_orgs})

            print(f"Test orgs flagged for deletion ({len(test_org_ids)}):")
            for r in pattern_orgs:
                print(f"  [pattern]   {r[0]}  {r[1]!r}")
            for r in duplicate_orgs:
                print(f"  [duplicate] {r[0]}  {r[1]!r}")
            print()

            # ── DELETE in FK-respecting order ────────────────────────────
            deleted = {}

            def _exec(label: str, sql: str, **params) -> int:
                result = conn.execute(text(sql), params)
                n = result.rowcount or 0
                deleted[label] = deleted.get(label, 0) + n
                print(f"  {label:32s} -{n}")
                return n

            print("Deleting per-org cascading data (FK-ordered)...")
            if test_org_ids:
                # Layer 1 — release evidence_artifacts FKs (scan_imports holds them)
                _exec("scan_findings", """
                    DELETE FROM scan_findings WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)
                _exec("baseline_deviations", """
                    DELETE FROM baseline_deviations WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)
                _exec("scan_imports", """
                    DELETE FROM scan_imports WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)
                _exec("org_baselines", """
                    DELETE FROM org_baselines WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)

                # Layer 2 — evidence_control_map then evidence_artifacts
                _exec("evidence_control_map", """
                    DELETE FROM evidence_control_map
                    WHERE evidence_id IN (
                        SELECT id FROM evidence_artifacts WHERE org_id = ANY(:ids)
                    )
                """, ids=test_org_ids)
                _exec("evidence_artifacts", """
                    DELETE FROM evidence_artifacts WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)

                # Layer 3 — SSP / POA&M / generated docs
                _exec("ssp_sections", """
                    DELETE FROM ssp_sections WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)
                _exec("ssp_jobs", """
                    DELETE FROM ssp_jobs WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)
                _exec("poam_items", """
                    DELETE FROM poam_items WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)
                _exec("generated_documents", """
                    DELETE FROM generated_documents WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)

                # Layer 4 — claims / observations / resolutions / contradictions
                _exec("claims", """
                    DELETE FROM claims WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)
                _exec("observations", """
                    DELETE FROM observations WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)
                _exec("resolutions", """
                    DELETE FROM resolutions WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)
                _exec("intake_contradictions", """
                    DELETE FROM intake_contradictions WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)

                # Layer 5 — intake (company_profiles + responses/documents
                # before sessions; CASCADE handles responses+documents but
                # explicit is clearer)
                _exec("company_profiles", """
                    DELETE FROM company_profiles WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)
                _exec("intake_responses", """
                    DELETE FROM intake_responses WHERE session_id IN (
                        SELECT id FROM intake_sessions WHERE org_id = ANY(:ids)
                    )
                """, ids=test_org_ids)
                _exec("intake_documents", """
                    DELETE FROM intake_documents WHERE session_id IN (
                        SELECT id FROM intake_sessions WHERE org_id = ANY(:ids)
                    )
                """, ids=test_org_ids)
                _exec("intake_sessions", """
                    DELETE FROM intake_sessions WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)

                # Layer 6 — remaining org-scoped tables
                _exec("affirmations", """
                    DELETE FROM affirmations WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)
                _exec("assessment_snapshots", """
                    DELETE FROM assessment_snapshots WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)
                _exec("export_records", """
                    DELETE FROM export_records WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)
                _exec("freshness_thresholds", """
                    DELETE FROM freshness_thresholds WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)

            print("\nDeleting invites...")
            if test_org_ids:
                _exec("invites (test orgs)", """
                    DELETE FROM invites WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)
            _exec("invites (used)", """
                DELETE FROM invites WHERE used_at IS NOT NULL
            """)
            _exec("invites (expired+unused)", """
                DELETE FROM invites WHERE expires_at < NOW() AND used_at IS NULL
            """)

            print("\nDeleting users...")
            if test_org_ids:
                _exec("users (test orgs)", """
                    DELETE FROM users WHERE org_id = ANY(:ids)
                """, ids=test_org_ids)
            _exec("users (deactivated @example.com in preserved)", """
                DELETE FROM users
                WHERE deactivated_at IS NOT NULL
                  AND email LIKE '%@example.com'
                  AND org_id = ANY(:preserved)
            """, preserved=preserved_ids)

            print("\nDeleting test orgs themselves...")
            if test_org_ids:
                _exec("organizations", """
                    DELETE FROM organizations WHERE id = ANY(:ids)
                """, ids=test_org_ids)

            print("\nDeleting test contact requests...")
            _exec("contact_requests", """
                DELETE FROM contact_requests
                WHERE name ILIKE '%test%'
                   OR email LIKE '%@example.com'
                   OR (email ILIKE '%test%' AND email NOT IN (
                       'joseph@intranest.ai',
                       'josephwmusso@gmail.com',
                       'admin@intranest.ai'
                   ))
            """)

            print("\naudit_log preserved (hash chain integrity)")

            # ── Snapshot AFTER counts (still inside txn) ─────────────────
            after = _table_counts(conn)

            print()
            print("BEFORE -> AFTER (rows deleted)")
            print("=" * 60)
            for t in COUNT_TABLES:
                b = before.get(t, -1)
                a = after.get(t, -1)
                if b < 0 or a < 0:
                    print(f"  {t:25s} (n/a)")
                else:
                    delta = b - a
                    print(f"  {t:25s} {b:6d} -> {a:6d}  ({delta:+d} deleted)" if delta != 0
                          else f"  {t:25s} {b:6d} -> {a:6d}  (unchanged)")
            print()

            total_deleted = sum(before[t] - after[t] for t in COUNT_TABLES
                                if before.get(t, -1) >= 0 and after.get(t, -1) >= 0)
            print(f"TOTAL ROWS DELETED: {total_deleted}")
            print()

            if args.commit:
                trans.commit()
                print("=" * 60)
                print(f"COMMITTED — {total_deleted} rows deleted.")
                print("=" * 60)
            else:
                trans.rollback()
                print("=" * 60)
                print("DRY RUN — NO CHANGES COMMITTED.")
                print("Re-run with --commit to apply these deletions.")
                print("=" * 60)

        except Exception as e:
            trans.rollback()
            print(f"\nERROR — transaction rolled back: {e}", file=sys.stderr)
            raise

    return 0


if __name__ == "__main__":
    sys.exit(main())
