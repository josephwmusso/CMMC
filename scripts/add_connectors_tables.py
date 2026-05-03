"""
scripts/add_connectors_tables.py

Adds the ``connectors`` and ``connector_runs`` tables for the Phase 5.1
Connector Framework. Idempotent — safe to run repeatedly on local,
staging, and Render.

Tables:
  - connectors:      one row per configured external integration per org
                     (M365, Entra ID, CrowdStrike, etc). Holds an encrypted
                     credentials blob plus a JSON config map.
  - connector_runs:  one row per execution of a connector. Captures who
                     triggered it (cron / manual / api), how many evidence
                     artifacts it produced, and a summary JSON for the UI.

Usage (local):
    python scripts/add_connectors_tables.py

Usage (remote):
    python scripts/add_connectors_tables.py --database-url "<full-pg-url>"

On Render, these tables are also created automatically via the same
DDL in render_startup.py's TABLES_DDL block — this standalone script
exists for local dev and one-off fixes.
"""
from __future__ import annotations

import argparse
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


CONNECTORS_DDL = """
    CREATE TABLE IF NOT EXISTS connectors (
        id                    VARCHAR(20) PRIMARY KEY,
        org_id                VARCHAR(20) NOT NULL,
        type                  VARCHAR(50) NOT NULL,
        name                  VARCHAR(255) NOT NULL,
        status                VARCHAR(20) NOT NULL DEFAULT 'INACTIVE',
        credentials_encrypted TEXT,
        config                JSON,
        last_run_at           TIMESTAMPTZ,
        last_status           VARCHAR(20),
        created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        created_by            VARCHAR(20)
    );
    CREATE INDEX IF NOT EXISTS connectors_org_type_idx
        ON connectors(org_id, type);
    CREATE UNIQUE INDEX IF NOT EXISTS connectors_org_type_name_uniq
        ON connectors(org_id, type, name);
"""

CONNECTOR_RUNS_DDL = """
    CREATE TABLE IF NOT EXISTS connector_runs (
        id                          VARCHAR(20) PRIMARY KEY,
        connector_id                VARCHAR(20) NOT NULL,
        org_id                      VARCHAR(20) NOT NULL,
        triggered_by                VARCHAR(50) NOT NULL,
        triggered_by_user_id        VARCHAR(20),
        started_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        finished_at                 TIMESTAMPTZ,
        status                      VARCHAR(20) NOT NULL DEFAULT 'RUNNING',
        evidence_artifacts_created  INT NOT NULL DEFAULT 0,
        error_message               TEXT,
        summary                     JSON
    );
    CREATE INDEX IF NOT EXISTS connector_runs_connector_started_idx
        ON connector_runs(connector_id, started_at DESC);
    CREATE INDEX IF NOT EXISTS connector_runs_org_started_idx
        ON connector_runs(org_id, started_at DESC);
"""


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
        cur.execute(CONNECTORS_DDL)
        print("  connectors table + indexes ensured")

        cur.execute(CONNECTOR_RUNS_DDL)
        print("  connector_runs table + indexes ensured")

        # Verify both tables landed
        cur.execute(
            "SELECT to_regclass('public.connectors'), to_regclass('public.connector_runs')"
        )
        connectors_oid, runs_oid = cur.fetchone()
        if connectors_oid is None:
            raise RuntimeError("connectors table missing after DDL")
        if runs_oid is None:
            raise RuntimeError("connector_runs table missing after DDL")
        print(f"  Confirmed: connectors={connectors_oid}, connector_runs={runs_oid}")

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
