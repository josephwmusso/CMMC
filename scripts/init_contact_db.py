"""
Migration: Create contact_requests table.
Run once: python scripts/init_contact_db.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from src.db.session import engine

CREATE_CONTACT_REQUESTS = """
CREATE TABLE IF NOT EXISTS contact_requests (
    id              VARCHAR PRIMARY KEY,
    name            VARCHAR NOT NULL,
    email           VARCHAR NOT NULL,
    company         VARCHAR,
    employee_count  VARCHAR,
    message         TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status          VARCHAR NOT NULL DEFAULT 'new'
);
"""

if __name__ == "__main__":
    with engine.connect() as conn:
        conn.execute(text(CREATE_CONTACT_REQUESTS))
        conn.commit()
    print("Migration complete: contact_requests table created.")
