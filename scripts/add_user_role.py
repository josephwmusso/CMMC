"""
scripts/add_user_role.py

Adds the ``role`` enum column to the users table and backfills the
seeded admin to SUPERADMIN. Idempotent — safe to run repeatedly on
local, staging, and Render.

Usage (local):
    python scripts/add_user_role.py

Usage (remote):
    python scripts/add_user_role.py --database-url "<full-pg-url>"

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


ROLE_ENUM_NAME = "user_role"
ROLE_VALUES = ("SUPERADMIN", "ADMIN", "MEMBER", "VIEWER")
DEFAULT_ROLE = "MEMBER"
SUPERADMIN_EMAIL_DEFAULT = os.environ.get("ADMIN_EMAIL", "admin@intranest.ai")


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
    parser.add_argument("--superadmin-email", default=SUPERADMIN_EMAIL_DEFAULT,
                        help="Email of the user to upgrade to SUPERADMIN (default: admin@intranest.ai)")
    args = parser.parse_args()

    import psycopg2

    url = get_db_url(args)
    print(f"Connecting to: {url.split('@')[-1] if '@' in url else url}")
    conn = psycopg2.connect(url)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # 1. Create enum type if missing.
        cur.execute("SELECT 1 FROM pg_type WHERE typname = %s", (ROLE_ENUM_NAME,))
        if cur.fetchone() is None:
            values_sql = ", ".join(f"'{v}'" for v in ROLE_VALUES)
            cur.execute(f"CREATE TYPE {ROLE_ENUM_NAME} AS ENUM ({values_sql})")
            print(f"  Created enum type '{ROLE_ENUM_NAME}' with values {ROLE_VALUES}")
        else:
            print(f"  Enum type '{ROLE_ENUM_NAME}' already exists")

        # 2. Add column if missing.
        cur.execute(f"""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS role {ROLE_ENUM_NAME} DEFAULT '{DEFAULT_ROLE}'
        """)
        print(f"  users.role column ensured (default '{DEFAULT_ROLE}')")

        # 3. Mirror the existing is_admin boolean onto the enum where the
        # column is still at its default — a user flagged is_admin should
        # be at least ADMIN, and the designated email should be SUPERADMIN.
        cur.execute(f"""
            UPDATE users
            SET role = 'ADMIN'::{ROLE_ENUM_NAME}
            WHERE is_admin = TRUE AND role = '{DEFAULT_ROLE}'
        """)
        admins_bumped = cur.rowcount
        if admins_bumped:
            print(f"  Bumped {admins_bumped} is_admin=TRUE user(s) from MEMBER to ADMIN")

        cur.execute(f"""
            UPDATE users
            SET role = 'SUPERADMIN'::{ROLE_ENUM_NAME}
            WHERE email = %s
        """, (args.superadmin_email,))
        super_bumped = cur.rowcount
        if super_bumped:
            print(f"  Set {args.superadmin_email} to SUPERADMIN")
        else:
            print(f"  NOTE: no user found with email {args.superadmin_email}; "
                  f"seeder will create them as SUPERADMIN on next startup")

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
