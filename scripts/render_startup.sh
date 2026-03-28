#!/bin/bash
set -e

echo "=== CMMC Platform Startup ==="
echo "DATABASE_URL is set: $([ -n "$DATABASE_URL" ] && echo 'yes' || echo 'NO')"

# Wait for database
echo "Waiting for database..."
for i in {1..30}; do
    python -c "
import psycopg2, os
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.close()
    print('Database ready')
    exit(0)
except Exception as e:
    print(f'  Not ready: {e}')
    exit(1)
" && break
    echo "  Attempt $i/30 — waiting 2s..."
    sleep 2
done

# Run migrations (each is idempotent — safe to re-run)
echo "Running migrations..."
python scripts/init_db.py || echo "  Warning: init_db.py had issues (may be OK if tables exist)"
python scripts/init_questionnaire_db.py || echo "  Warning: init_questionnaire_db.py had issues"
python scripts/init_document_engine_db.py || echo "  Warning: init_document_engine_db.py had issues"

# Load NIST data (only if controls table is empty)
python -c "
import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM controls')
count = cur.fetchone()[0]
conn.close()
if count == 0:
    print('Controls table empty — loading NIST data...')
    exit(0)
else:
    print(f'Controls already loaded ({count} records)')
    exit(1)
" && python scripts/load_nist_to_postgres.py || true

# Create default org if needed
python -c "
import psycopg2, os, hashlib
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute(\"SELECT COUNT(*) FROM organizations WHERE id = '9de53b587b23450b87af'\")
if cur.fetchone()[0] == 0:
    print('Creating default organization...')
    cur.execute(\"INSERT INTO organizations (id, name) VALUES ('9de53b587b23450b87af', 'Apex Defense Solutions') ON CONFLICT DO NOTHING\")
    conn.commit()
else:
    print('Default org exists')
conn.close()
" || echo "  Warning: org creation skipped"

echo "=== Startup complete — starting server ==="
exec uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8001}
