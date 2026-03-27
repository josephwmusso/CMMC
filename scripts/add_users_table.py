"""
Migration: Add users table for JWT authentication.
Run once from project root: python scripts/add_users_table.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from src.db.session import engine

CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id              VARCHAR PRIMARY KEY,
    email           VARCHAR UNIQUE NOT NULL,
    org_id          VARCHAR NOT NULL REFERENCES organizations(id),
    full_name       VARCHAR NOT NULL DEFAULT '',
    hashed_password VARCHAR NOT NULL,
    is_admin        BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at   TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_email  ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(org_id);
"""

CREATE_AUDIT_INDEX = """
CREATE INDEX IF NOT EXISTS idx_audit_log_id ON audit_log(id DESC);
"""

if __name__ == "__main__":
    with engine.connect() as conn:
        conn.execute(text(CREATE_USERS))
        conn.execute(text(CREATE_AUDIT_INDEX))
        conn.commit()
    print("Migration complete: users table + audit_log index created.")
