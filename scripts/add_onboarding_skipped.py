"""
scripts/add_onboarding_skipped.py

Adds the ``onboarding_skipped`` boolean column to the users table.
Idempotent — safe to run repeatedly on local, staging, and Render.

Distinguishes "completed via wizard" (skipped=FALSE) from "completed
via skip" (skipped=TRUE). NOT consulted by routing guards — the
ProtectedRoute only checks onboarding_complete. This column is
informational so product/marketing can later count the skip rate
or trigger nudges to users who skipped.

Default FALSE is correct for everyone existing (admin completed
via the wizard; grandfathered users predate both columns).

Usage (local):
    python scripts/add_onboarding_skipped.py

Usage (remote):
    python scripts/add_onboarding_skipped.py --database-url "<full-pg-url>"

On Render, this is applied automatically via the same ALTER in
render_startup.py's migration block — this standalone script exists
for local dev and one-off fixes.
"""
from __future__ import annotations

import argparse
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def get_db_url(args: argparse.Namespace) -> str:
    url = args.database_url or os.environ.get("DATABASE_URL", "")
    if not url:
        url = "postgresql://cmmc:localdev@localhost:5432/cmmc"
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url",
                        help="Postgres connection string (overrides DATABASE_URL env var)")
    args = parser.parse_args()

    import psycopg2

    url = get_db_url(args)
    print(f"Connecting to: {url.split('@')[-1] if '@' in url else url}")
    conn = psycopg2.connect(url)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        cur.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS onboarding_skipped BOOLEAN NOT NULL DEFAULT FALSE
        """)
        print("  users.onboarding_skipped BOOLEAN NOT NULL DEFAULT FALSE: OK")

        # Verify column landed
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'onboarding_skipped'
        """)
        row = cur.fetchone()
        if row:
            print(f"  Confirmed: column_name={row[0]}, data_type={row[1]}, "
                  f"nullable={row[2]}, default={row[3]}")
        else:
            print("  WARNING: column missing after ALTER (may need manual investigation)")

        conn.commit()
        print("Migration complete.")
    except Exception as exc:
        conn.rollback()
        print(f"FAILED — rolled back: {exc}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
