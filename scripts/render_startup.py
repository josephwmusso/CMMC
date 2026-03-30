"""
scripts/render_startup.py
Render deployment startup — runs migrations then starts uvicorn.
Python script avoids bash CRLF issues on Windows→Linux deploys.
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
        "scripts/init_questionnaire_db.py",
        "scripts/init_document_engine_db.py",
    ]
    for script in scripts:
        print(f"Running {script}...")
        try:
            subprocess.run([sys.executable, script], check=True)
        except subprocess.CalledProcessError as e:
            print(f"  Warning: {script} exited with code {e.returncode} (may be OK)")


def load_nist_data():
    """Load NIST controls if table is empty."""
    import psycopg2
    db_url = os.environ["DATABASE_URL"]
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    try:
        cur.execute("SELECT COUNT(*) FROM controls")
        count = cur.fetchone()[0]
        if count == 0:
            print("Controls table empty — loading NIST data...")
            conn.close()
            subprocess.run([sys.executable, "scripts/load_nist_to_postgres.py"], check=True)
        else:
            print(f"Controls already loaded ({count} records)")
            conn.close()
    except Exception as e:
        print(f"  Warning: {e}")
        conn.close()


def create_default_org():
    """Create the default Apex Defense org if missing."""
    import psycopg2
    db_url = os.environ["DATABASE_URL"]
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM organizations WHERE id = '9de53b587b23450b87af'")
        if cur.fetchone()[0] == 0:
            print("Creating default organization...")
            cur.execute(
                "INSERT INTO organizations (id, name) VALUES ('9de53b587b23450b87af', 'Apex Defense Solutions') "
                "ON CONFLICT DO NOTHING"
            )
            conn.commit()
        else:
            print("Default org exists")
    except Exception as e:
        print(f"  Warning: {e}")
    finally:
        conn.close()


def ensure_data_dirs():
    """Create data directories needed at runtime."""
    dirs = ["data/evidence", "data/exports"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"  Data dir ready: {d}")


def start_server():
    """Start uvicorn."""
    port = os.environ.get("PORT", "8001")
    print(f"Starting server on port {port}...")
    os.execvp(
        sys.executable,
        [sys.executable, "-m", "uvicorn", "src.api.main:app",
         "--host", "0.0.0.0", "--port", port]
    )


if __name__ == "__main__":
    print("=== CMMC Platform Startup ===")

    if not wait_for_db():
        print("FATAL: Could not connect to database")
        sys.exit(1)

    run_migrations()
    load_nist_data()
    create_default_org()
    ensure_data_dirs()

    print("=== Startup complete ===")
    start_server()
