"""
Migration: Add frameworks table + framework_id to controls.

Path: scripts/add_frameworks_table.py

Run from project root (with venv activated):
    python scripts/add_frameworks_table.py

What it does (idempotent — safe to run twice):
  1. Creates the `frameworks` table if it doesn't exist
  2. Inserts the NIST 800-171 Rev 2 / CMMC Level 2 framework seed row
  3. Adds `framework_id` column to `controls` if it doesn't exist
  4. Backfills all existing controls with the NIST 800-171 Rev 2 framework_id
  5. Prints a verification summary

No existing data is modified beyond setting framework_id on controls rows.
All existing queries continue to work — framework_id is nullable.
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import inspect, text
from src.db.session import engine, get_session

# ── Stable seed ID for the canonical NIST 800-171 Rev 2 framework row.
# Hardcoded (not random) so this migration is idempotent and other scripts
# can reference it without a DB lookup.
NIST_171_R2_FRAMEWORK_ID = "nist80171r2_fw000001"


# ── Step 1: Create frameworks table ──────────────────────────────────────────

CREATE_FRAMEWORKS_TABLE = """
CREATE TABLE IF NOT EXISTS frameworks (
    id            VARCHAR(20)  PRIMARY KEY,
    name          VARCHAR(255) NOT NULL,
    version       VARCHAR(100) NOT NULL,
    control_count INTEGER      NOT NULL DEFAULT 0,
    description   TEXT,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
"""

# ── Step 2: Add framework_id FK column to controls ───────────────────────────

ADD_FRAMEWORK_ID_COLUMN = """
ALTER TABLE controls
    ADD COLUMN IF NOT EXISTS framework_id VARCHAR(20)
        REFERENCES frameworks(id) ON DELETE SET NULL;
"""

ADD_FRAMEWORK_ID_INDEX = """
CREATE INDEX IF NOT EXISTS ix_controls_framework
    ON controls (framework_id);
"""

# ── Step 3: Seed the canonical framework row ─────────────────────────────────

SEED_FRAMEWORK = """
INSERT INTO frameworks (id, name, version, control_count, description)
VALUES (
    :id,
    'CMMC Level 2',
    'NIST 800-171 Rev 2',
    110,
    'Cybersecurity Maturity Model Certification Level 2 — '
    'based on NIST SP 800-171 Revision 2 (110 security requirements '
    'across 14 control families). Required for DoD contractors '
    'handling Controlled Unclassified Information (CUI).'
)
ON CONFLICT (id) DO NOTHING;
"""

# ── Step 4: Backfill existing controls ───────────────────────────────────────

BACKFILL_CONTROLS = """
UPDATE controls
SET    framework_id = :framework_id
WHERE  framework_id IS NULL;
"""


def run_migration():
    print("=" * 60)
    print("Migration: add_frameworks_table")
    print("=" * 60)

    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    with engine.begin() as conn:

        # ── 1. Create frameworks table ────────────────────────────────────
        if "frameworks" in existing_tables:
            print("  [SKIP] frameworks table already exists")
        else:
            conn.execute(text(CREATE_FRAMEWORKS_TABLE))
            print("  [OK]   Created frameworks table")

        # ── 2. Add framework_id column to controls ────────────────────────
        existing_cols = {
            col["name"]
            for col in inspector.get_columns("controls")
        }
        if "framework_id" in existing_cols:
            print("  [SKIP] controls.framework_id already exists")
        else:
            conn.execute(text(ADD_FRAMEWORK_ID_COLUMN))
            conn.execute(text(ADD_FRAMEWORK_ID_INDEX))
            print("  [OK]   Added controls.framework_id (nullable FK)")

        # ── 3. Seed NIST 800-171 Rev 2 framework row ─────────────────────
        conn.execute(text(SEED_FRAMEWORK), {"id": NIST_171_R2_FRAMEWORK_ID})
        print(f"  [OK]   Seeded framework row (id={NIST_171_R2_FRAMEWORK_ID})")

        # ── 4. Backfill existing controls ─────────────────────────────────
        result = conn.execute(
            text(BACKFILL_CONTROLS),
            {"framework_id": NIST_171_R2_FRAMEWORK_ID},
        )
        print(f"  [OK]   Backfilled {result.rowcount} control(s) -> framework_id")

    # ── 5. Verify ─────────────────────────────────────────────────────────
    print("\n--- Verification ---")
    with engine.connect() as conn:
        fw_count = conn.execute(
            text("SELECT COUNT(*) FROM frameworks")
        ).scalar()
        print(f"  frameworks rows:           {fw_count}")

        ctrl_total = conn.execute(
            text("SELECT COUNT(*) FROM controls")
        ).scalar()
        ctrl_linked = conn.execute(
            text("SELECT COUNT(*) FROM controls WHERE framework_id IS NOT NULL")
        ).scalar()
        ctrl_unlinked = ctrl_total - ctrl_linked
        print(f"  controls total:            {ctrl_total}")
        print(f"  controls with framework_id: {ctrl_linked}")
        if ctrl_unlinked:
            print(f"  WARNING: {ctrl_unlinked} control(s) still have NULL framework_id")
        else:
            print(f"  controls without:          0  (all linked)")

        fw_row = conn.execute(
            text("SELECT id, name, version, control_count FROM frameworks LIMIT 1")
        ).fetchone()
        if fw_row:
            print(f"\n  Framework: '{fw_row.name}' / '{fw_row.version}'")
            print(f"  ID:         {fw_row.id}")
            print(f"  control_count (stored): {fw_row.control_count}")

    print("\nMigration complete.")
    print(
        "\nNext: update src/db/models.py to add the Framework model "
        "and framework_id FK on Control (already done if you ran this "
        "alongside the model update)."
    )


if __name__ == "__main__":
    run_migration()
