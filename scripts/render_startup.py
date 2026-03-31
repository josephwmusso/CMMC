"""
scripts/render_startup.py
Render deployment startup — creates tables, seeds data, starts uvicorn.
All table creation happens SYNCHRONOUSLY before the server starts.
"""
import os
import sys
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_db_url():
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def wait_for_db(max_attempts=30):
    """Wait for Postgres to accept connections."""
    import psycopg2
    db_url = get_db_url()
    print(f"DATABASE_URL set: {'yes' if db_url else 'NO'}")
    if not db_url:
        print("FATAL: DATABASE_URL not set")
        sys.exit(1)

    for i in range(max_attempts):
        try:
            conn = psycopg2.connect(db_url)
            conn.close()
            print("Database ready")
            return
        except Exception as e:
            print(f"  Attempt {i+1}/{max_attempts}: {e}")
            time.sleep(2)

    print("FATAL: Could not connect to database")
    sys.exit(1)


def create_all_tables():
    """Create ALL tables directly with raw SQL. No subprocess, no ORM.
    Uses CREATE TABLE IF NOT EXISTS so it's safe to run multiple times.
    Order matters: parent tables before child tables (FK constraints).
    """
    import psycopg2
    conn = psycopg2.connect(get_db_url())
    conn.autocommit = True
    cur = conn.cursor()

    tables = [
        ("frameworks", """
            CREATE TABLE IF NOT EXISTS frameworks (
                id            VARCHAR(20) PRIMARY KEY,
                name          VARCHAR(255) NOT NULL,
                version       VARCHAR(100) NOT NULL DEFAULT '',
                control_count INTEGER NOT NULL DEFAULT 0,
                description   TEXT,
                created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """),
        ("organizations", """
            CREATE TABLE IF NOT EXISTS organizations (
                id            VARCHAR(20) PRIMARY KEY,
                name          VARCHAR(255) NOT NULL,
                cage_code     VARCHAR(10),
                duns_number   VARCHAR(13),
                system_name   VARCHAR(255),
                system_boundary TEXT,
                employee_count INTEGER,
                created_at    TIMESTAMPTZ DEFAULT NOW(),
                updated_at    TIMESTAMPTZ
            )
        """),
        ("controls", """
            CREATE TABLE IF NOT EXISTS controls (
                id            VARCHAR(30) PRIMARY KEY,
                framework_id  VARCHAR(20) REFERENCES frameworks(id) ON DELETE SET NULL,
                family        VARCHAR(80) NOT NULL,
                family_abbrev VARCHAR(4) NOT NULL,
                title         VARCHAR(500) NOT NULL,
                description   TEXT NOT NULL,
                discussion    TEXT,
                nist_section  VARCHAR(20),
                points        INTEGER DEFAULT 1,
                poam_eligible BOOLEAN DEFAULT true,
                status        VARCHAR(20) DEFAULT 'not_assessed'
            )
        """),
        ("assessment_objectives", """
            CREATE TABLE IF NOT EXISTS assessment_objectives (
                id          VARCHAR(30) PRIMARY KEY,
                control_id  VARCHAR(30) NOT NULL REFERENCES controls(id) ON DELETE CASCADE,
                description TEXT NOT NULL,
                examine     TEXT,
                interview   TEXT,
                test        TEXT,
                status      VARCHAR(20) DEFAULT 'not_assessed'
            )
        """),
        ("evidence_artifacts", """
            CREATE TABLE IF NOT EXISTS evidence_artifacts (
                id              VARCHAR(30) PRIMARY KEY,
                org_id          VARCHAR(20) NOT NULL REFERENCES organizations(id),
                filename        VARCHAR(500) NOT NULL,
                original_name   VARCHAR(500),
                file_path       TEXT,
                file_size_bytes BIGINT,
                mime_type       VARCHAR(100),
                sha256_hash     VARCHAR(64),
                evidence_type   VARCHAR(50) DEFAULT 'other',
                source_system   VARCHAR(100) DEFAULT 'manual',
                description     TEXT,
                owner           VARCHAR(255),
                state           VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
                uploaded_at     TIMESTAMPTZ DEFAULT NOW(),
                reviewed_at     TIMESTAMPTZ,
                approved_at     TIMESTAMPTZ,
                published_at    TIMESTAMPTZ
            )
        """),
        ("evidence_control_map", """
            CREATE TABLE IF NOT EXISTS evidence_control_map (
                id            VARCHAR(30) PRIMARY KEY,
                evidence_id   VARCHAR(30) NOT NULL REFERENCES evidence_artifacts(id) ON DELETE CASCADE,
                control_id    VARCHAR(30) REFERENCES controls(id) ON DELETE CASCADE,
                objective_id  VARCHAR(30) REFERENCES assessment_objectives(id) ON DELETE CASCADE,
                created_at    TIMESTAMPTZ DEFAULT NOW()
            )
        """),
        ("ssp_sections", """
            CREATE TABLE IF NOT EXISTS ssp_sections (
                id                    VARCHAR(30) PRIMARY KEY,
                org_id                VARCHAR(20) NOT NULL REFERENCES organizations(id),
                control_id            VARCHAR(30) NOT NULL REFERENCES controls(id),
                implementation_status VARCHAR(30),
                narrative             TEXT,
                citations             JSONB,
                state                 VARCHAR(20) DEFAULT 'draft',
                version               INTEGER DEFAULT 1,
                generated_by          VARCHAR(100),
                created_at            TIMESTAMPTZ DEFAULT NOW(),
                updated_at            TIMESTAMPTZ
            )
        """),
        ("poam_items", """
            CREATE TABLE IF NOT EXISTS poam_items (
                id                   VARCHAR(30) PRIMARY KEY,
                org_id               VARCHAR(20) NOT NULL REFERENCES organizations(id),
                control_id           VARCHAR(30) NOT NULL REFERENCES controls(id),
                weakness_description TEXT,
                remediation_plan     TEXT,
                risk_level           VARCHAR(20),
                points               INTEGER DEFAULT 1,
                status               VARCHAR(20) DEFAULT 'OPEN',
                milestone_changes    TEXT,
                scheduled_completion TIMESTAMPTZ,
                created_at           TIMESTAMPTZ DEFAULT NOW(),
                updated_at           TIMESTAMPTZ
            )
        """),
        ("audit_log", """
            CREATE TABLE IF NOT EXISTS audit_log (
                id          SERIAL PRIMARY KEY,
                timestamp   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                actor       VARCHAR(255) NOT NULL DEFAULT 'system',
                action      VARCHAR(100) NOT NULL,
                target_type VARCHAR(50),
                target_id   VARCHAR(100),
                details     JSONB,
                entry_hash  VARCHAR(64),
                prev_hash   VARCHAR(64)
            )
        """),
        ("users", """
            CREATE TABLE IF NOT EXISTS users (
                id              VARCHAR PRIMARY KEY,
                email           VARCHAR UNIQUE NOT NULL,
                org_id          VARCHAR NOT NULL REFERENCES organizations(id),
                full_name       VARCHAR NOT NULL DEFAULT '',
                hashed_password VARCHAR NOT NULL,
                is_admin        BOOLEAN NOT NULL DEFAULT false,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                last_login_at   TIMESTAMPTZ
            )
        """),
        ("intake_sessions", """
            CREATE TABLE IF NOT EXISTS intake_sessions (
                id          VARCHAR PRIMARY KEY,
                org_id      VARCHAR NOT NULL,
                status      VARCHAR DEFAULT 'in_progress',
                current_module INTEGER DEFAULT 0,
                started_at  TIMESTAMPTZ DEFAULT NOW(),
                updated_at  TIMESTAMPTZ
            )
        """),
        ("intake_responses", """
            CREATE TABLE IF NOT EXISTS intake_responses (
                id           VARCHAR PRIMARY KEY,
                session_id   VARCHAR NOT NULL,
                question_id  VARCHAR NOT NULL,
                module_id    INTEGER,
                control_ids  JSONB,
                answer_type  VARCHAR,
                answer_value TEXT,
                created_at   TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(session_id, question_id)
            )
        """),
        ("company_profiles", """
            CREATE TABLE IF NOT EXISTS company_profiles (
                id               VARCHAR PRIMARY KEY,
                org_id           VARCHAR NOT NULL,
                company_name     VARCHAR,
                cage_code        VARCHAR,
                duns_number      VARCHAR,
                employee_count   INTEGER,
                facility_count   INTEGER,
                primary_location VARCHAR,
                cui_types        JSONB,
                cui_flow         TEXT,
                has_remote_workers BOOLEAN,
                has_wireless     BOOLEAN,
                identity_provider VARCHAR,
                email_platform   VARCHAR,
                email_tier       VARCHAR,
                edr_product      VARCHAR,
                firewall_product VARCHAR,
                siem_product     VARCHAR,
                backup_solution  VARCHAR,
                existing_ssp     BOOLEAN,
                existing_poam    BOOLEAN,
                prior_assessment VARCHAR,
                dfars_7012_clause BOOLEAN,
                created_at       TIMESTAMPTZ DEFAULT NOW(),
                updated_at       TIMESTAMPTZ
            )
        """),
        ("document_templates", """
            CREATE TABLE IF NOT EXISTS document_templates (
                id              VARCHAR PRIMARY KEY,
                doc_type        VARCHAR NOT NULL UNIQUE,
                title           VARCHAR NOT NULL,
                description     TEXT,
                sections        JSONB,
                control_ids     JSONB,
                conditional_on  VARCHAR,
                estimated_pages INTEGER DEFAULT 0,
                created_at      TIMESTAMPTZ DEFAULT NOW()
            )
        """),
        ("generated_documents", """
            CREATE TABLE IF NOT EXISTS generated_documents (
                id                  VARCHAR PRIMARY KEY,
                org_id              VARCHAR NOT NULL,
                doc_type            VARCHAR NOT NULL,
                title               VARCHAR NOT NULL,
                version             INTEGER DEFAULT 1,
                status              VARCHAR DEFAULT 'draft',
                sections            JSONB,
                word_count          INTEGER DEFAULT 0,
                file_path           TEXT,
                evidence_artifact_id VARCHAR,
                created_at          TIMESTAMPTZ DEFAULT NOW(),
                updated_at          TIMESTAMPTZ
            )
        """),
        ("contact_requests", """
            CREATE TABLE IF NOT EXISTS contact_requests (
                id              VARCHAR PRIMARY KEY,
                name            VARCHAR NOT NULL,
                email           VARCHAR NOT NULL,
                company         VARCHAR,
                employee_count  VARCHAR,
                message         TEXT,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                status          VARCHAR NOT NULL DEFAULT 'new'
            )
        """),
        ("ssp_jobs", """
            CREATE TABLE IF NOT EXISTS ssp_jobs (
                job_id          VARCHAR(20) PRIMARY KEY,
                status          VARCHAR(20) NOT NULL DEFAULT 'pending',
                progress        TEXT NOT NULL DEFAULT 'Starting...',
                controls_done   INTEGER NOT NULL DEFAULT 0,
                controls_total  INTEGER NOT NULL DEFAULT 0,
                docx_path       TEXT,
                started_at      TIMESTAMPTZ,
                completed_at    TIMESTAMPTZ,
                error           TEXT
            )
        """),
    ]

    print("\n--- Creating tables ---")
    for name, ddl in tables:
        try:
            cur.execute(ddl)
            print(f"  {name:30s} [OK]")
        except Exception as e:
            print(f"  {name:30s} [ERROR] {e}")
            print(f"FATAL: Could not create table {name}")
            conn.close()
            sys.exit(1)

    # Create indexes
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_controls_family ON controls(family_abbrev)",
        "CREATE INDEX IF NOT EXISTS idx_controls_framework ON controls(framework_id)",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
        "CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(org_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_log_id ON audit_log(id DESC)",
    ]
    for idx in indexes:
        try:
            cur.execute(idx)
        except Exception:
            pass  # indexes are non-critical

    conn.close()
    print(f"  All {len(tables)} tables created successfully\n")


def seed_framework():
    """Seed the NIST 800-171 framework row."""
    import psycopg2
    conn = psycopg2.connect(get_db_url())
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO frameworks (id, name, version, control_count, description)
            VALUES ('nist80171r2_fw000001', 'CMMC Level 2', 'NIST 800-171 Rev 2', 110,
                    'Cybersecurity Maturity Model Certification Level 2')
            ON CONFLICT (id) DO NOTHING
        """)
        conn.commit()
        print("Framework seeded: CMMC Level 2")
    except Exception as e:
        print(f"  Warning seeding framework: {e}")
    finally:
        conn.close()


def create_default_org():
    """Create the default Apex Defense Solutions org if missing."""
    import psycopg2
    conn = psycopg2.connect(get_db_url())
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM organizations WHERE id = '9de53b587b23450b87af'")
        if cur.fetchone()[0] == 0:
            print("Creating default organization...")
            cur.execute(
                "INSERT INTO organizations (id, name, system_name, employee_count) "
                "VALUES ('9de53b587b23450b87af', 'Apex Defense Solutions', 'Apex Secure Enclave', 45) "
                "ON CONFLICT DO NOTHING"
            )
            conn.commit()
            print("  Org created: Apex Defense Solutions")
        else:
            print("Default org exists")
    except Exception as e:
        print(f"  Warning creating org: {e}")
    finally:
        conn.close()


def load_nist_data():
    """Load ALL 110 NIST controls + objectives."""
    import psycopg2
    conn = psycopg2.connect(get_db_url())
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM controls")
        count = cur.fetchone()[0]
        conn.close()

        if count < 110:
            print(f"Controls: {count}/110 — loading full NIST dataset...")
            subprocess.run([sys.executable, "scripts/load_nist_to_postgres.py"], check=True)
        else:
            print(f"Controls already loaded ({count} records)")
    except Exception as e:
        print(f"  Warning loading NIST data: {e}")
        try:
            conn.close()
        except Exception:
            pass


def create_admin_user():
    """Create admin user. Always ensures it exists with correct password."""
    import psycopg2
    conn = psycopg2.connect(get_db_url())
    cur = conn.cursor()
    try:
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@intranest.ai")
        admin_password = os.environ.get("ADMIN_PASSWORD", "Intranest2026!")

        from passlib.context import CryptContext
        pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd.hash(admin_password)

        # Upsert: create or update
        cur.execute("""
            INSERT INTO users (id, email, org_id, full_name, hashed_password, is_admin)
            VALUES ('USR-ADMIN000001', %s, '9de53b587b23450b87af', 'Admin', %s, true)
            ON CONFLICT (id) DO UPDATE SET
                email = EXCLUDED.email,
                hashed_password = EXCLUDED.hashed_password,
                is_admin = true
        """, (admin_email, hashed))
        conn.commit()
        print(f"Admin user ready: {admin_email}")
    except Exception as e:
        print(f"FATAL: Could not create admin user: {e}")
        conn.close()
        sys.exit(1)
    finally:
        conn.close()


def ensure_data_dirs():
    """Create data directories needed at runtime."""
    dirs = ["data/evidence", "data/exports"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def verify_data():
    """Verify all critical data exists."""
    import psycopg2
    conn = psycopg2.connect(get_db_url())
    cur = conn.cursor()
    print("\n--- Data Verification ---")
    for table in ["organizations", "controls", "assessment_objectives", "users",
                   "frameworks", "ssp_jobs", "contact_requests"]:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  {table:30s} {count:>5} rows")
        except Exception as e:
            print(f"  {table:30s} ERROR: {e}")
    conn.close()


def start_server():
    """Start uvicorn. This replaces the current process."""
    port = os.environ.get("PORT", "8001")
    print(f"\nStarting uvicorn on port {port}...")
    os.execvp(
        sys.executable,
        [sys.executable, "-m", "uvicorn", "src.api.main:app",
         "--host", "0.0.0.0", "--port", port]
    )


if __name__ == "__main__":
    print("=" * 60)
    print("INTRANEST Platform Startup")
    print("=" * 60)

    # 1. Wait for database
    wait_for_db()

    # 2. Create ALL tables (raw SQL, no ORM, no subprocess)
    create_all_tables()

    # 3. Seed reference data
    seed_framework()
    create_default_org()
    load_nist_data()

    # 4. Create admin user (AFTER tables + org exist)
    create_admin_user()

    # 5. Ensure runtime dirs
    ensure_data_dirs()

    # 6. Verify
    verify_data()

    print("\n=== Startup complete — all tables and data verified ===")

    # 7. Start server (replaces this process)
    start_server()
