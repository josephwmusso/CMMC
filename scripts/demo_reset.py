"""
Demo Reset Script — clears all generated data for a clean demo start.
Keeps: organizations, controls, assessment_objectives (reference data).
Clears: ssp_sections, poam_items, evidence_artifacts, evidence_control_map, audit_log.
Also deletes evidence files from data/evidence/{org_id}/.

Usage:
    python scripts/demo_reset.py              # interactive confirmation
    python scripts/demo_reset.py --force      # skip confirmation
    python scripts/demo_reset.py --keep-evidence  # keep evidence files, clear SSP/POA&M only
"""

import sys
import os
import shutil
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.db.session import get_session

ORG_ID = "9de53b587b23450b87af"
EVIDENCE_DIR = os.path.join("data", "evidence", ORG_ID)
EXPORTS_DIR = os.path.join("data", "exports")


def reset_demo(keep_evidence=False, force=False):
    """Reset all demo data to pristine state."""

    if not force:
        print("=" * 60)
        print("  CMMC PLATFORM — DEMO RESET")
        print("=" * 60)
        print()
        print("This will DELETE:")
        print("  - All SSP sections (ssp_sections)")
        print("  - All POA&M items (poam_items)")
        print("  - All audit log entries (audit_log)")
        if not keep_evidence:
            print("  - All evidence artifacts (evidence_artifacts)")
            print("  - All evidence-control mappings (evidence_control_map)")
            print(f"  - All evidence files in {EVIDENCE_DIR}/")
        print()
        print("This will KEEP:")
        print("  - Organizations (reference data)")
        print("  - Controls (110 NIST 800-171 controls)")
        print("  - Assessment objectives (246 objectives)")
        if keep_evidence:
            print("  - Evidence artifacts and files")
        print()
        confirm = input("Type 'RESET' to confirm: ").strip()
        if confirm != "RESET":
            print("Cancelled.")
            return False

    print()
    print("Resetting demo data...")

    with get_session() as session:
        # Order matters — foreign key dependencies

        # 1. Clear evidence-control mappings
        if not keep_evidence:
            result = session.execute(text(
                "DELETE FROM evidence_control_map WHERE evidence_id IN "
                "(SELECT id FROM evidence_artifacts WHERE org_id = :org_id)"
            ), {"org_id": ORG_ID})
            print(f"  Deleted {result.rowcount} evidence-control mappings")

        # 2. Clear audit log (no org_id column — clear all)
        result = session.execute(text("DELETE FROM audit_log"))
        print(f"  Deleted {result.rowcount} audit log entries")

        # 3. Clear POA&M items
        result = session.execute(text(
            "DELETE FROM poam_items WHERE org_id = :org_id"
        ), {"org_id": ORG_ID})
        print(f"  Deleted {result.rowcount} POA&M items")

        # 4. Clear SSP sections
        result = session.execute(text(
            "DELETE FROM ssp_sections WHERE org_id = :org_id"
        ), {"org_id": ORG_ID})
        print(f"  Deleted {result.rowcount} SSP sections")

        # 5. Clear evidence artifacts
        if not keep_evidence:
            result = session.execute(text(
                "DELETE FROM evidence_artifacts WHERE org_id = :org_id"
            ), {"org_id": ORG_ID})
            print(f"  Deleted {result.rowcount} evidence artifacts")

        session.commit()
        print("  Database cleared.")

    # 6. Delete evidence files from disk
    if not keep_evidence and os.path.exists(EVIDENCE_DIR):
        file_count = sum(1 for f in os.listdir(EVIDENCE_DIR) if os.path.isfile(os.path.join(EVIDENCE_DIR, f)))
        shutil.rmtree(EVIDENCE_DIR)
        os.makedirs(EVIDENCE_DIR, exist_ok=True)
        print(f"  Deleted {file_count} evidence files from {EVIDENCE_DIR}/")

    # 7. Verify clean state
    print()
    print("Verifying clean state...")
    with get_session() as session:
        counts = {}
        for table in ["ssp_sections", "poam_items", "audit_log"]:
            row = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            counts[table] = row
            status = "OK" if row == 0 else f"WARNING: {row} rows remain"
            print(f"  {table}: {status}")

        if not keep_evidence:
            for table in ["evidence_artifacts", "evidence_control_map"]:
                row = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                counts[table] = row
                status = "OK" if row == 0 else f"WARNING: {row} rows remain"
                print(f"  {table}: {status}")

        # Show what's still there (reference data)
        controls = session.execute(text("SELECT COUNT(*) FROM controls")).scalar()
        objectives = session.execute(text("SELECT COUNT(*) FROM assessment_objectives")).scalar()
        print(f"  controls: {controls} (kept)")
        print(f"  assessment_objectives: {objectives} (kept)")

    # 8. Show expected SPRS score after reset
    print()
    print("Post-reset state:")
    print("  SPRS Score: 0 (no SSP sections = no controls assessed)")
    print("  SSP Completion: 0%")
    print("  Evidence Coverage: 0%")
    print("  POA&M Items: 0")
    print("  Audit Chain: Empty")
    print()
    print("Demo reset complete. Ready for a fresh walkthrough.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset CMMC demo to clean state")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--keep-evidence", action="store_true", help="Keep evidence, only clear SSP/POA&M")
    args = parser.parse_args()

    reset_demo(keep_evidence=args.keep_evidence, force=args.force)
