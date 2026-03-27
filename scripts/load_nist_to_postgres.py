"""
Load all 110 NIST 800-171 Rev 2 controls and 246 assessment objectives
into the Postgres database.

Safe to re-run (uses upsert logic — deletes existing then re-inserts).

Usage:
  cd D:\cmmc-platform
  python scripts\load_nist_to_postgres.py

Requires: Postgres running on localhost:5432, tables already created via init_db.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from configs.settings import DATABASE_URL
from data.nist.controls_full import NIST_800_171_CONTROLS, validate_controls
from data.nist.objectives_full import ASSESSMENT_OBJECTIVES, validate_objectives


def load_controls(session):
    """Load all 110 controls into the controls table."""
    print("\n--- Loading controls ---")

    # Clear existing controls (cascade will handle FK refs if configured)
    # Use a careful approach: delete objectives first, then controls
    existing = session.execute(text("SELECT COUNT(*) FROM controls")).scalar()
    print(f"Existing controls in DB: {existing}")

    if existing > 0:
        print("Clearing existing objectives...")
        session.execute(text("DELETE FROM assessment_objectives"))
        print("Clearing existing controls...")
        session.execute(text("DELETE FROM controls"))
        session.commit()

    # Insert all controls
    insert_sql = text("""
        INSERT INTO controls (id, family, family_abbrev, title, description, discussion, points, poam_eligible)
        VALUES (:id, :family, :family_id, :title, :description, :discussion, :points, :poam_eligible)
        ON CONFLICT (id) DO UPDATE SET
            family = EXCLUDED.family,
            family_abbrev = EXCLUDED.family_abbrev,
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            discussion = EXCLUDED.discussion,
            points = EXCLUDED.points,
            poam_eligible = EXCLUDED.poam_eligible
    """)

    for ctrl in NIST_800_171_CONTROLS:
        session.execute(insert_sql, {
            "id": ctrl["id"],
            "family": ctrl["family"],
            "family_id": ctrl["family_id"],
            "title": ctrl["title"],
            "description": ctrl["description"],
            "discussion": ctrl["discussion"],
            "points": ctrl["points"],
            "poam_eligible": ctrl["poam_eligible"],
        })

    session.commit()
    count = session.execute(text("SELECT COUNT(*) FROM controls")).scalar()
    print(f"Controls loaded: {count}")
    return count


def load_objectives(session):
    """Load all assessment objectives into the assessment_objectives table."""
    print("\n--- Loading assessment objectives ---")

    existing = session.execute(
        text("SELECT COUNT(*) FROM assessment_objectives")
    ).scalar()
    print(f"Existing objectives in DB: {existing}")

    if existing > 0:
        print("Clearing existing objectives...")
        session.execute(text("DELETE FROM assessment_objectives"))
        session.commit()

    insert_sql = text("""
        INSERT INTO assessment_objectives
            (id, control_id, description, examine, interview, test)
        VALUES
            (:id, :control_id, :description, :examine, :interview, :test)
        ON CONFLICT (id) DO UPDATE SET
            control_id = EXCLUDED.control_id,
            description = EXCLUDED.description,
            examine = EXCLUDED.examine,
            interview = EXCLUDED.interview,
            test = EXCLUDED.test
    """)

    loaded = 0
    errors = 0
    for obj in ASSESSMENT_OBJECTIVES:
        try:
            session.execute(insert_sql, {
                "id": obj["id"],
                "control_id": obj["control_id"],
                "description": obj["description"],
                "examine": obj["examine"],
                "interview": obj["interview"],
                "test": obj["test"],
            })
            loaded += 1
        except Exception as e:
            print(f"  ERROR loading {obj['id']}: {e}")
            errors += 1
            session.rollback()

    session.commit()
    count = session.execute(
        text("SELECT COUNT(*) FROM assessment_objectives")
    ).scalar()
    print(f"Objectives loaded: {count} (errors: {errors})")
    return count


def verify_data(session):
    """Quick verification queries."""
    print("\n--- Verification ---")

    # Control counts by family
    rows = session.execute(text("""
        SELECT family, COUNT(*), SUM(points)
        FROM controls
        GROUP BY family
        ORDER BY family
    """)).fetchall()

    print(f"\n{'Family':<42} {'Controls':>8} {'Points':>8}")
    print("-" * 60)
    total_controls = 0
    total_points = 0
    for family, count, points in rows:
        print(f"{family:<42} {count:>8} {points:>8}")
        total_controls += count
        total_points += points
    print("-" * 60)
    print(f"{'TOTAL':<42} {total_controls:>8} {total_points:>8}")

    # Objectives per control (sample)
    print(f"\nSample: objectives for AC.L2-3.1.1:")
    objs = session.execute(text("""
        SELECT id, LEFT(description, 60) as desc_preview
        FROM assessment_objectives
        WHERE control_id = 'AC.L2-3.1.1'
        ORDER BY id
    """)).fetchall()
    for obj_id, desc in objs:
        print(f"  {obj_id}: {desc}...")

    # Check the SSP control is not POA&M eligible
    ssp = session.execute(text("""
        SELECT id, title, poam_eligible
        FROM controls
        WHERE id = 'CA.L2-3.12.4'
    """)).fetchone()
    print(f"\nSSP control: {ssp[0]} — POA&M eligible: {ssp[2]}")
    assert ssp[2] in ("no", False), "CRITICAL: SSP must not be POA&M eligible!"

    # SPRS score range
    print(f"\nSPRS Score Range: {110 - total_points} to 110")
    print(f"5-pt controls: {session.execute(text('SELECT COUNT(*) FROM controls WHERE points = 5')).scalar()}")
    print(f"3-pt controls: {session.execute(text('SELECT COUNT(*) FROM controls WHERE points = 3')).scalar()}")
    print(f"1-pt controls: {session.execute(text('SELECT COUNT(*) FROM controls WHERE points = 1')).scalar()}")


def main():
    print("=" * 60)
    print("NIST 800-171 Rev 2 — Full Data Load to Postgres")
    print("=" * 60)

    # Validate source data first
    print("\nValidating source data...")
    validate_controls()
    validate_objectives()

    # Connect to Postgres
    print(f"\nConnecting to: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        controls_count = load_controls(session)
        objectives_count = load_objectives(session)
        verify_data(session)

        print("\n" + "=" * 60)
        print(f"LOAD COMPLETE")
        print(f"  Controls:   {controls_count}")
        print(f"  Objectives: {objectives_count}")
        print("=" * 60)

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
