"""
Backfill file_content for existing generated documents.

Reads DOCX files from disk and stores bytes in Postgres so downloads work
without regenerating. One-time local utility — do NOT commit to git.

Usage:
    python scripts/backfill_doc_content.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

# Match the project's dev default (see configs/settings.py)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cmmc:localdev@localhost:5432/cmmc",
)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT id, title, file_path
        FROM generated_documents
        WHERE file_content IS NULL
    """)).fetchall()

    if not rows:
        print("All documents already have file_content. Nothing to backfill.")
        sys.exit(0)

    print(f"Found {len(rows)} documents without file_content")

    backfilled = 0
    for doc_id, title, file_path in rows:
        # generated_documents has no `filename` column — derive from file_path.
        derived_name = os.path.basename(file_path) if file_path else None

        paths_to_try = []
        if file_path:
            paths_to_try.append(file_path)
        if derived_name:
            paths_to_try.append(os.path.join("data", "exports", derived_name))

        found = False
        for path in paths_to_try:
            if path and os.path.exists(path):
                with open(path, "rb") as f:
                    content = f.read()
                conn.execute(
                    text("UPDATE generated_documents SET file_content = :content WHERE id = :id"),
                    {"content": content, "id": doc_id},
                )
                label = derived_name or title or doc_id
                print(f"  OK  {label} ({len(content)} bytes)")
                backfilled += 1
                found = True
                break

        if not found:
            label = derived_name or title or doc_id
            print(f"  --  {label} — file not found on disk, skipping (regenerate to restore)")

    conn.commit()
    print(f"\nBackfilled {backfilled}/{len(rows)} documents")

    if backfilled < len(rows):
        print("For missing files, run:")
        print("  curl -X POST http://localhost:8001/api/documents/generate-all")
