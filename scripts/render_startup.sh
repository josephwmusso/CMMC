#!/bin/bash
set -e

echo "=== CMMC Platform Startup ==="

# Wait for database
echo "Waiting for database..."
for i in {1..30}; do
    python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.close()
    print('Database ready')
    exit(0)
except:
    exit(1)
" && break
    echo "  Attempt $i/30 — waiting 2s..."
    sleep 2
done

# Run migrations
echo "Running migrations..."
python scripts/init_db.py
python scripts/init_questionnaire_db.py
python scripts/init_document_engine_db.py

# Load NIST data (only if controls table is empty)
python -c "
import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM controls')
count = cur.fetchone()[0]
conn.close()
if count == 0:
    print('Loading NIST controls...')
    exit(0)
else:
    print(f'Controls already loaded ({count} records)')
    exit(1)
" && python scripts/load_nist_to_postgres.py || true

echo "Starting server..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8001}
