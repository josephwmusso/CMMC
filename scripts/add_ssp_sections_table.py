"""
scripts/add_ssp_sections_table.py

Adds the ssp_sections table to Postgres for persisting SSP narratives.
Safe to re-run (idempotent).

Run from D:\\cmmc-platform with venv activated:
    python scripts/add_ssp_sections_table.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from src.db.session import engine


MIGRATION_SQL = """
-- SSP Sections: stores generated narratives per control per org
CREATE TABLE IF NOT EXISTS ssp_sections (
    id              SERIAL PRIMARY KEY,
    control_id      VARCHAR(30) NOT NULL REFERENCES controls(id),
    org_id          VARCHAR(100) NOT NULL DEFAULT 'default-org',
    narrative       TEXT NOT NULL DEFAULT '',
    implementation_status VARCHAR(30) NOT NULL DEFAULT 'Not Implemented',
    evidence_refs   JSONB DEFAULT '[]'::jsonb,
    gaps            JSONB DEFAULT '[]'::jsonb,
    generated_by    VARCHAR(50) DEFAULT 'ssp_agent',
    version         INTEGER DEFAULT 1,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(control_id, org_id)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_ssp_sections_org ON ssp_sections(org_id);
CREATE INDEX IF NOT EXISTS idx_ssp_sections_status ON ssp_sections(implementation_status);
"""


def main():
    print("Adding ssp_sections table to Postgres...")
    with engine.begin() as conn:
        conn.execute(text(MIGRATION_SQL))
    print("Done. Table ssp_sections is ready.")

    # Verify
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'ssp_sections' ORDER BY ordinal_position"
        ))
        rows = result.fetchall()
        print(f"\nssp_sections columns ({len(rows)}):")
        for col_name, data_type in rows:
            print(f"  {col_name}: {data_type}")


if __name__ == "__main__":
    main()
