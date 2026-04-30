"""
Read-only inventory of stale test data on Render production Postgres.

Usage:
    DATABASE_URL=<render-external-url> python scripts/inspect_stale_data.py

Prints counts only — runs ZERO mutating SQL. Outputs a report for human
review before any cleanup script is run. Phase 1 of the cleanup plan.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text


PRESERVED_APEX_ID = "9de53b587b23450b87af"


def _scalar(conn, sql: str, **params) -> int:
    return conn.execute(text(sql), params).scalar() or 0


def _rows(conn, sql: str, **params):
    return conn.execute(text(sql), params).fetchall()


def main() -> int:
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        print("ABORT: DATABASE_URL not set.", file=sys.stderr)
        return 2
    if "localhost" in db_url or "127.0.0.1" in db_url:
        print("ABORT: DATABASE_URL points at localhost — refusing to run.", file=sys.stderr)
        return 2

    print(f"DATABASE_URL host: {db_url.split('@')[-1].split('/')[0].split('?')[0]}")
    print(f"Run timestamp:     {datetime.now(timezone.utc).isoformat()}")
    print()

    engine = create_engine(db_url, pool_pre_ping=True)
    with engine.connect() as conn:
        # ── Resolve preserved orgs ───────────────────────────────────────
        intranest_row = conn.execute(text("""
            SELECT u.id, u.email, u.org_id, o.name
            FROM users u
            LEFT JOIN organizations o ON u.org_id = o.id
            WHERE u.email = 'admin@intranest.ai'
        """)).fetchone()

        preserved_ids = [PRESERVED_APEX_ID]
        if intranest_row is not None:
            admin_org_id = intranest_row[2]
            admin_org_name = intranest_row[3]
            print(f"admin@intranest.ai is in org: {admin_org_name!r} ({admin_org_id})")
            if admin_org_id not in preserved_ids:
                preserved_ids.append(admin_org_id)
        else:
            print("WARNING: admin@intranest.ai not found.")

        print(f"Preserved org_ids ({len(preserved_ids)}): {preserved_ids}")
        print()
        print("STALE DATA INVENTORY (Render production)")
        print("=" * 60)

        # ── Organizations matching test patterns ─────────────────────────
        print("\nOrganizations matching test patterns:")
        playwright_orgs = _rows(conn, """
            SELECT id, name FROM organizations
            WHERE name LIKE 'Playwright Test Corp%'
            ORDER BY name
        """)
        print(f"  Playwright Test Corp <suffix>:        {len(playwright_orgs)} rows")
        for r in playwright_orgs:
            print(f"    - {r[1]!r}  (id={r[0]})")

        test_company = _rows(conn, """
            SELECT id, name FROM organizations
            WHERE name = 'Test Company' AND id <> ALL(:preserved)
        """, preserved=preserved_ids)
        print(f"  Test Company:                          {len(test_company)} rows")
        for r in test_company:
            print(f"    - {r[1]!r}  (id={r[0]})")

        test_corp_prefix = _rows(conn, """
            SELECT id, name FROM organizations
            WHERE name LIKE 'Test Corp%' AND id <> ALL(:preserved)
        """, preserved=preserved_ids)
        print(f"  Test Corp%:                            {len(test_corp_prefix)} rows")
        for r in test_corp_prefix:
            print(f"    - {r[1]!r}  (id={r[0]})")

        test_org_exact = _rows(conn, """
            SELECT id, name FROM organizations
            WHERE name = 'Test Org' AND id <> ALL(:preserved)
        """, preserved=preserved_ids)
        print(f"  Test Org:                              {len(test_org_exact)} rows")

        other_test = _rows(conn, """
            SELECT id, name FROM organizations
            WHERE name ILIKE '%test%'
              AND name NOT LIKE 'Playwright Test Corp%'
              AND name <> 'Test Company'
              AND name NOT LIKE 'Test Corp%'
              AND name <> 'Test Org'
              AND id <> ALL(:preserved)
            ORDER BY name
        """, preserved=preserved_ids)
        print(f"  Other org names matching '%test%':     {len(other_test)} rows")
        for row in other_test:
            print(f"    - {row[1]!r}  (id={row[0]})")

        all_test_org_ids = (
            [r[0] for r in playwright_orgs]
            + [r[0] for r in test_company]
            + [r[0] for r in test_corp_prefix]
            + [r[0] for r in test_org_exact]
            + [r[0] for r in other_test]
        )
        all_test_org_ids = [oid for oid in all_test_org_ids if oid not in preserved_ids]

        # ── Informational: orgs not matching test patterns ───────────────
        print("\nOrgs NOT matching test patterns (informational — not flagged for delete):")
        non_test = _rows(conn, """
            SELECT o.id, o.name,
                   (SELECT COUNT(*) FROM users u WHERE u.org_id = o.id) AS user_count
            FROM organizations o
            WHERE o.id <> ALL(:preserved)
              AND o.name NOT LIKE 'Playwright Test Corp%'
              AND o.name <> 'Test Company'
              AND o.name NOT LIKE 'Test Corp%'
              AND o.name <> 'Test Org'
              AND o.name NOT ILIKE '%test%'
            ORDER BY o.name
        """, preserved=preserved_ids)
        for row in non_test:
            users_in_org = _rows(conn, """
                SELECT email FROM users WHERE org_id = :oid ORDER BY email
            """, oid=row[0])
            emails = ", ".join(u[0] for u in users_in_org) or "(no users)"
            print(f"    - {row[1]!r}  (id={row[0]}, {row[2]} users: {emails})")

        # ── Users ────────────────────────────────────────────────────────
        if all_test_org_ids:
            users_in_test_orgs = _scalar(conn, """
                SELECT COUNT(*) FROM users WHERE org_id = ANY(:ids)
            """, ids=all_test_org_ids)
        else:
            users_in_test_orgs = 0
        print(f"\nUsers belonging to those orgs:                  {users_in_test_orgs} rows")

        deactivated = _scalar(conn, "SELECT COUNT(*) FROM users WHERE deactivated_at IS NOT NULL")
        deactivated_rows = _rows(conn, """
            SELECT email, org_id, deactivated_at FROM users
            WHERE deactivated_at IS NOT NULL ORDER BY email
        """)
        print(f"Users with deactivated_at IS NOT NULL:          {deactivated} rows")
        for r in deactivated_rows:
            print(f"    - {r[0]!r}  (org={r[1]}, deactivated={r[2]})")

        print("Users matching email patterns:")
        ex_com = _scalar(conn, "SELECT COUNT(*) FROM users WHERE email LIKE '%@example.com'")
        print(f"  %@example.com:                                 {ex_com} rows")

        mailinator = _scalar(conn, "SELECT COUNT(*) FROM users WHERE email LIKE '%@mailinator.example'")
        print(f"  %@mailinator.example:                          {mailinator} rows")

        pw_intra = _scalar(conn, """
            SELECT COUNT(*) FROM users WHERE email LIKE 'playwright-test-%@intranest.ai'
        """)
        print(f"  playwright-test-*@intranest.ai:                {pw_intra} rows")

        test_intra = _scalar(conn, "SELECT COUNT(*) FROM users WHERE email = 'test@intranest.ai'")
        print(f"  test@intranest.ai:                             {test_intra} rows")

        other_test_emails = _rows(conn, """
            SELECT id, email, org_id FROM users
            WHERE email ILIKE '%test%'
              AND email NOT LIKE 'playwright-test-%@intranest.ai'
              AND email <> 'test@intranest.ai'
              AND email NOT LIKE '%@example.com'
              AND email NOT LIKE '%@mailinator.example'
            ORDER BY email
        """)
        print(f"  Other emails matching '%test%':                {len(other_test_emails)} rows")
        for row in other_test_emails:
            print(f"    - {row[1]!r}  (id={row[0]}, org={row[2]})")

        # ── Invites ──────────────────────────────────────────────────────
        print("\nInvites:")
        try:
            expired = _scalar(conn, "SELECT COUNT(*) FROM invites WHERE expires_at < NOW()")
            print(f"  Expired invites (expires_at < NOW()):          {expired} rows")
            used = _scalar(conn, "SELECT COUNT(*) FROM invites WHERE used_at IS NOT NULL")
            print(f"  Used invites (used_at IS NOT NULL):            {used} rows")
            if all_test_org_ids:
                test_org_invites = _scalar(conn, """
                    SELECT COUNT(*) FROM invites WHERE org_id = ANY(:ids)
                """, ids=all_test_org_ids)
            else:
                test_org_invites = 0
            print(f"  Invites belonging to test orgs above:          {test_org_invites} rows")
            total_invites = _scalar(conn, "SELECT COUNT(*) FROM invites")
            print(f"  Total invites currently in the table:          {total_invites} rows")
        except Exception as e:
            print(f"  (invites table inspection failed: {e})")

        # ── Contact requests ─────────────────────────────────────────────
        print("\nContact requests (contact_requests table):")
        try:
            test_contacts = _scalar(conn, """
                SELECT COUNT(*) FROM contact_requests
                WHERE name ILIKE '%test%'
                   OR email ILIKE '%test%'
                   OR email LIKE '%@example.com'
            """)
            print(f"  Submissions matching test patterns:            {test_contacts} rows")
            sample = _rows(conn, """
                SELECT name, email FROM contact_requests
                WHERE name ILIKE '%test%'
                   OR email ILIKE '%test%'
                   OR email LIKE '%@example.com'
                ORDER BY created_at DESC LIMIT 20
            """)
            for row in sample:
                print(f"    - {row[0]!r}  <{row[1]}>")
            total_contacts = _scalar(conn, "SELECT COUNT(*) FROM contact_requests")
            print(f"  Total contact_requests in table:               {total_contacts} rows")
        except Exception as e:
            print(f"  (contact_requests inspection failed: {e})")

        # ── Per-org cascading data ───────────────────────────────────────
        print("\nPer-org cascading data (totals across all flagged test orgs):")
        cascade_tables = [
            ("intake_sessions",      "SELECT COUNT(*) FROM intake_sessions WHERE org_id = ANY(:ids)"),
            ("intake_responses",     "SELECT COUNT(*) FROM intake_responses WHERE session_id IN (SELECT id FROM intake_sessions WHERE org_id = ANY(:ids))"),
            ("intake_documents",     "SELECT COUNT(*) FROM intake_documents WHERE session_id IN (SELECT id FROM intake_sessions WHERE org_id = ANY(:ids))"),
            ("company_profiles",     "SELECT COUNT(*) FROM company_profiles WHERE org_id = ANY(:ids)"),
            ("evidence_artifacts",   "SELECT COUNT(*) FROM evidence_artifacts WHERE org_id = ANY(:ids)"),
            ("evidence_control_map", "SELECT COUNT(*) FROM evidence_control_map WHERE evidence_id IN (SELECT id FROM evidence_artifacts WHERE org_id = ANY(:ids))"),
            ("ssp_sections",         "SELECT COUNT(*) FROM ssp_sections WHERE org_id = ANY(:ids)"),
            ("ssp_jobs",             "SELECT COUNT(*) FROM ssp_jobs WHERE org_id = ANY(:ids)"),
            ("poam_items",           "SELECT COUNT(*) FROM poam_items WHERE org_id = ANY(:ids)"),
            ("generated_documents",  "SELECT COUNT(*) FROM generated_documents WHERE org_id = ANY(:ids)"),
        ]
        for table, sql in cascade_tables:
            try:
                if all_test_org_ids:
                    cnt = _scalar(conn, sql, ids=all_test_org_ids)
                else:
                    cnt = 0
                print(f"  {table:25s} {cnt}")
            except Exception as e:
                print(f"  {table:25s} (n/a — {str(e)[:80]})")

        # ── audit_log informational ──────────────────────────────────────
        print("\naudit_log: NOT TOUCHED (append-only, hash-chained)")
        try:
            audit_total = _scalar(conn, "SELECT COUNT(*) FROM audit_log")
            print(f"  total audit_log rows (preserved as-is):        {audit_total}")
        except Exception as e:
            print(f"  (audit_log inspection failed: {e})")

        # ── Final flagged summary ────────────────────────────────────────
        print()
        print("PRESERVED")
        print(f"  Apex Defense Solutions:  {PRESERVED_APEX_ID}")
        for oid in preserved_ids:
            if oid != PRESERVED_APEX_ID:
                row = conn.execute(text("SELECT name FROM organizations WHERE id = :id"), {"id": oid}).fetchone()
                print(f"  Other preserved:         {oid}  {row[0] if row else '?'!r}")
        print()
        print("Test orgs flagged for deletion:")
        for oid in all_test_org_ids:
            row = conn.execute(text("SELECT name FROM organizations WHERE id = :id"), {"id": oid}).fetchone()
            user_emails = _rows(conn, "SELECT email FROM users WHERE org_id = :id", id=oid)
            emails = ", ".join(u[0] for u in user_emails) or "(no users)"
            print(f"  - {oid}  {row[0] if row else '?'!r}")
            print(f"      users: {emails}")
        print()
        print(f"Total test orgs flagged: {len(all_test_org_ids)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
