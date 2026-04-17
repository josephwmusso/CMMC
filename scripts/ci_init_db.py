"""Initialize database for CI — tables + seeds, no uvicorn.

Usage: DATABASE_URL=... python scripts/ci_init_db.py
"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.render_startup import (
    TABLES_DDL,
    get_connection,
    wait_for_db,
    seed_framework,
    seed_organization,
    seed_admin_user,
    seed_controls,
    seed_objectives,
    seed_audit_genesis,
    seed_document_templates,
)


def main():
    wait_for_db(max_attempts=10)

    logger.info("Creating tables...")
    conn = get_connection()
    cur = conn.cursor()
    for name, ddl in TABLES_DDL:
        try:
            cur.execute(ddl)
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.warning(f"  {name}: {e}")
    conn.close()

    # Run idempotent ALTERs (same as render_startup.py's migration block)
    logger.info("Running migrations...")
    conn = get_connection()
    cur = conn.cursor()

    migration_sqls = [
        "ALTER TABLE invites ADD COLUMN IF NOT EXISTS invite_type VARCHAR(30) DEFAULT 'USER_TO_ORG'",
        "ALTER TABLE invites ADD COLUMN IF NOT EXISTS target_org_name VARCHAR(200)",
        "ALTER TABLE invites ALTER COLUMN org_id DROP NOT NULL",
        "ALTER TABLE baseline_items ADD COLUMN IF NOT EXISTS match_plugin_ids TEXT[]",
    ]
    for sql in migration_sqls:
        try:
            cur.execute(sql)
            conn.commit()
        except Exception:
            conn.rollback()

    # user_role enum
    try:
        cur.execute("""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
                    CREATE TYPE user_role AS ENUM ('SUPERADMIN', 'ADMIN', 'MEMBER', 'VIEWER');
                END IF;
            END$$;
        """)
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role user_role DEFAULT 'MEMBER'")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_complete BOOLEAN NOT NULL DEFAULT FALSE")
        conn.commit()
    except Exception:
        conn.rollback()

    conn.close()

    # Seeds
    logger.info("Seeding data...")
    conn = get_connection()
    cur = conn.cursor()
    try:
        seed_framework(cur)
        seed_organization(cur)
        seed_admin_user(cur)
        seed_controls(cur)
        seed_objectives(cur)
        seed_audit_genesis(cur)
        seed_document_templates(cur)
        try:
            from scripts.seeds.apex_company_profile import seed_apex_company_profile
            seed_apex_company_profile(cur)
        except Exception as e:
            logger.warning(f"Apex profile seed skipped: {e}")
        try:
            from src.baselines.seeds import seed_baselines
            seed_baselines(cur)
        except Exception as e:
            logger.warning(f"Baseline seed skipped: {e}")
        conn.commit()
        logger.info("Seeds complete")
    except Exception as e:
        conn.rollback()
        logger.error(f"Seeding failed: {e}")
        sys.exit(1)
    conn.close()

    logger.info("CI database initialization complete")


if __name__ == "__main__":
    main()
