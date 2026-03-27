"""
Migration: Add ssp_jobs table so job state survives API restarts.
Run: python scripts/add_ssp_jobs_table.py
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from src.db.session import engine

SQL = """
CREATE TABLE IF NOT EXISTS ssp_jobs (
    id               VARCHAR PRIMARY KEY,
    org_id           VARCHAR NOT NULL,
    status           VARCHAR NOT NULL DEFAULT 'pending',
    progress         VARCHAR,
    controls_done    INTEGER NOT NULL DEFAULT 0,
    controls_total   INTEGER NOT NULL DEFAULT 0,
    docx_path        VARCHAR,
    error            TEXT,
    started_at       TIMESTAMPTZ,
    completed_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_ssp_jobs_org_id ON ssp_jobs(org_id);
"""

if __name__ == "__main__":
    with engine.connect() as conn:
        conn.execute(text(SQL))
        conn.commit()
    print("Migration complete: ssp_jobs table created.")
