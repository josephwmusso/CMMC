"""
scripts/init_questionnaire_db.py
Database migration: adds tables for the guided intake questionnaire engine.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.db.session import get_session


MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS intake_sessions (
    id              VARCHAR(30) PRIMARY KEY,
    org_id          VARCHAR(30) NOT NULL REFERENCES organizations(id),
    started_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMP,
    current_module  INTEGER NOT NULL DEFAULT 0,
    status          VARCHAR(20) NOT NULL DEFAULT 'in_progress',
    modules_completed   INTEGER NOT NULL DEFAULT 0,
    total_questions     INTEGER NOT NULL DEFAULT 0,
    answered_questions  INTEGER NOT NULL DEFAULT 0,
    gap_count           INTEGER NOT NULL DEFAULT 0,
    estimated_sprs      INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_intake_sessions_org
    ON intake_sessions(org_id);

CREATE TABLE IF NOT EXISTS intake_responses (
    id              VARCHAR(30) PRIMARY KEY,
    session_id      VARCHAR(30) NOT NULL REFERENCES intake_sessions(id) ON DELETE CASCADE,
    org_id          VARCHAR(30) NOT NULL,
    module_id       INTEGER NOT NULL,
    question_id     VARCHAR(50) NOT NULL,
    control_ids     JSON NOT NULL DEFAULT '[]',
    answer_type     VARCHAR(20) NOT NULL,
    answer_value    TEXT,
    answer_details  JSON,
    creates_gap     BOOLEAN NOT NULL DEFAULT FALSE,
    gap_severity    VARCHAR(20),
    evidence_action VARCHAR(30),
    answered_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(session_id, question_id)
);

CREATE INDEX IF NOT EXISTS idx_intake_responses_session
    ON intake_responses(session_id);
CREATE INDEX IF NOT EXISTS idx_intake_responses_module
    ON intake_responses(session_id, module_id);

CREATE TABLE IF NOT EXISTS intake_documents (
    id              VARCHAR(30) PRIMARY KEY,
    session_id      VARCHAR(30) NOT NULL REFERENCES intake_sessions(id) ON DELETE CASCADE,
    org_id          VARCHAR(30) NOT NULL,
    doc_type        VARCHAR(50) NOT NULL,
    title           VARCHAR(200) NOT NULL,
    file_path       VARCHAR(500),
    generated_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    status          VARCHAR(20) NOT NULL DEFAULT 'draft',
    control_ids     JSON NOT NULL DEFAULT '[]',
    word_count      INTEGER,
    sha256_hash     VARCHAR(64)
);

CREATE INDEX IF NOT EXISTS idx_intake_documents_session
    ON intake_documents(session_id);

CREATE TABLE IF NOT EXISTS company_profiles (
    id              VARCHAR(30) PRIMARY KEY,
    org_id          VARCHAR(30) NOT NULL UNIQUE REFERENCES organizations(id),
    session_id      VARCHAR(30) REFERENCES intake_sessions(id),
    company_name        VARCHAR(200),
    cage_code           VARCHAR(10),
    duns_number         VARCHAR(15),
    employee_count      INTEGER,
    facility_count      INTEGER,
    primary_location    VARCHAR(200),
    cui_types           JSON DEFAULT '[]',
    cui_flow            VARCHAR(50),
    has_remote_workers  BOOLEAN DEFAULT FALSE,
    has_wireless        BOOLEAN DEFAULT FALSE,
    identity_provider       VARCHAR(100),
    email_platform          VARCHAR(100),
    email_tier              VARCHAR(50),
    edr_product             VARCHAR(100),
    firewall_product        VARCHAR(100),
    siem_product            VARCHAR(100),
    backup_solution         VARCHAR(100),
    existing_ssp        BOOLEAN DEFAULT FALSE,
    existing_poam       BOOLEAN DEFAULT FALSE,
    prior_assessment    BOOLEAN DEFAULT FALSE,
    dfars_7012_clause   BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
"""


def run_migration():
    print("Running questionnaire DB migration...")

    with get_session() as session:
        statements = [s.strip() for s in MIGRATION_SQL.split(";") if s.strip()]
        for stmt in statements:
            try:
                session.execute(text(stmt))
            except Exception as e:
                if "already exists" in str(e).lower():
                    continue
                print(f"  Warning: {e}")
        session.commit()

    # Verify tables exist
    with get_session() as session:
        for table in ["intake_sessions", "intake_responses", "intake_documents", "company_profiles"]:
            result = session.execute(
                text(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = :t"),
                {"t": table}
            ).scalar()
            status = "OK" if result else "MISSING"
            print(f"  [{status}] {table}")

    print("\nMigration complete.")


if __name__ == "__main__":
    run_migration()
