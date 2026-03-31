"""
scripts/render_startup.py
Render deployment startup — runs migrations, seeds data, starts uvicorn.
"""
import os
import sys
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def wait_for_db(max_attempts=30):
    """Wait for Postgres to accept connections."""
    import psycopg2
    db_url = os.environ.get("DATABASE_URL", "")
    print(f"DATABASE_URL set: {'yes' if db_url else 'NO'}")
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        return False

    for i in range(max_attempts):
        try:
            conn = psycopg2.connect(db_url)
            conn.close()
            print("Database ready")
            return True
        except Exception as e:
            print(f"  Attempt {i+1}/{max_attempts}: {e}")
            time.sleep(2)
    return False


def run_migrations():
    """Run all migration scripts."""
    scripts = [
        "scripts/init_db.py",
        "scripts/add_frameworks_table.py",
        "scripts/add_users_table.py",
        "scripts/init_questionnaire_db.py",
        "scripts/init_document_engine_db.py",
        "scripts/init_contact_db.py",
    ]
    for script in scripts:
        print(f"Running {script}...")
        try:
            subprocess.run([sys.executable, script], check=True)
        except subprocess.CalledProcessError as e:
            print(f"  Warning: {script} exited with code {e.returncode} (may be OK)")


def _get_conn():
    import psycopg2
    return psycopg2.connect(os.environ["DATABASE_URL"])


def create_default_org():
    """Create the default Apex Defense Solutions org if missing."""
    conn = _get_conn()
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
    """Load ALL 110 NIST controls + objectives. Always ensures full set."""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM controls")
        count = cur.fetchone()[0]
        conn.close()

        if count < 110:
            print(f"Controls: {count}/110 — loading full NIST dataset...")
            # Force reload by running the load script
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
    conn = _get_conn()
    cur = conn.cursor()
    try:
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@intranest.ai")
        admin_password = os.environ.get("ADMIN_PASSWORD", "Intranest2026!")

        # Check if admin exists
        cur.execute("SELECT id FROM users WHERE email = %s", (admin_email,))
        existing = cur.fetchone()

        from passlib.context import CryptContext
        pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd.hash(admin_password)

        if existing:
            # Update password to match env var (in case it changed)
            cur.execute(
                "UPDATE users SET hashed_password = %s, is_admin = true WHERE email = %s",
                (hashed, admin_email)
            )
            conn.commit()
            print(f"Admin user updated: {admin_email}")
        else:
            cur.execute(
                "INSERT INTO users (id, email, org_id, full_name, hashed_password, is_admin) "
                "VALUES ('USR-ADMIN000001', %s, '9de53b587b23450b87af', 'Admin', %s, true) "
                "ON CONFLICT (id) DO UPDATE SET hashed_password = EXCLUDED.hashed_password, is_admin = true",
                (admin_email, hashed)
            )
            conn.commit()
            print(f"Admin user created: {admin_email}")
    except Exception as e:
        print(f"  Warning creating admin: {e}")
    finally:
        conn.close()


def create_ssp_jobs_table():
    """Ensure ssp_jobs table exists (used by SSP generation tracking)."""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ssp_jobs (
                job_id VARCHAR(20) PRIMARY KEY,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                progress TEXT NOT NULL DEFAULT 'Starting...',
                controls_done INTEGER NOT NULL DEFAULT 0,
                controls_total INTEGER NOT NULL DEFAULT 0,
                docx_path TEXT,
                started_at TIMESTAMPTZ,
                completed_at TIMESTAMPTZ,
                error TEXT
            )
        """)
        conn.commit()
        print("ssp_jobs table ready")
    except Exception as e:
        print(f"  Warning creating ssp_jobs: {e}")
    finally:
        conn.close()


def ensure_data_dirs():
    """Create data directories needed at runtime."""
    dirs = ["data/evidence", "data/exports"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"  Data dir ready: {d}")


def verify_data():
    """Quick verification of critical data."""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        checks = [
            ("organizations", "SELECT COUNT(*) FROM organizations"),
            ("controls", "SELECT COUNT(*) FROM controls"),
            ("assessment_objectives", "SELECT COUNT(*) FROM assessment_objectives"),
            ("users", "SELECT COUNT(*) FROM users"),
        ]
        print("\n--- Data Verification ---")
        for name, sql in checks:
            try:
                cur.execute(sql)
                count = cur.fetchone()[0]
                status = "OK" if count > 0 else "EMPTY"
                print(f"  {name:30s} {count:>5} [{status}]")
            except Exception as e:
                print(f"  {name:30s} ERROR: {e}")
    finally:
        conn.close()


def start_server():
    """Start uvicorn."""
    port = os.environ.get("PORT", "8001")
    print(f"\nStarting server on port {port}...")
    os.execvp(
        sys.executable,
        [sys.executable, "-m", "uvicorn", "src.api.main:app",
         "--host", "0.0.0.0", "--port", port]
    )


if __name__ == "__main__":
    print("=" * 60)
    print("INTRANEST Platform Startup")
    print("=" * 60)

    if not wait_for_db():
        print("FATAL: Could not connect to database")
        sys.exit(1)

    run_migrations()
    create_default_org()
    load_nist_data()
    create_admin_user()
    create_ssp_jobs_table()
    ensure_data_dirs()
    verify_data()

    print("\n=== Startup complete ===")
    start_server()
