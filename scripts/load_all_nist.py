"""
Week 2, Step 2 — Master Loader

Runs the full NIST knowledge base load in sequence:
1. Load controls + objectives into Postgres
2. Chunk, embed, and load into Qdrant
3. Run verification

Usage:
  cd D:\cmmc-platform
  python scripts\load_all_nist.py

This is the one-command way to run the entire step.
Individual scripts can also be run separately:
  python scripts\load_nist_to_postgres.py
  python scripts\load_nist_to_qdrant.py
  python scripts\verify_rag.py
"""

import subprocess
import sys
import os

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable


def run_script(name, description):
    """Run a script and check for errors."""
    script_path = os.path.join(SCRIPTS_DIR, name)
    print(f"\n{'#' * 60}")
    print(f"# {description}")
    print(f"# Running: {name}")
    print(f"{'#' * 60}\n")

    result = subprocess.run(
        [PYTHON, script_path],
        cwd=os.path.dirname(SCRIPTS_DIR),  # project root
    )

    if result.returncode != 0:
        print(f"\nERROR: {name} failed with exit code {result.returncode}")
        print("Fix the error above and re-run this script.")
        sys.exit(1)

    print(f"\n{name} completed successfully!")


def main():
    print("=" * 60)
    print("CMMC PLATFORM — Week 2, Step 2: Full NIST Knowledge Load")
    print("=" * 60)
    print()
    print("This will:")
    print("  1. Load 110 controls + 246 objectives into Postgres")
    print("  2. Chunk, embed (BGE-small), and load into Qdrant")
    print("  3. Verify RAG queries return correct results")
    print()
    print("Prerequisites:")
    print("  - Postgres running on localhost:5432")
    print("  - Qdrant running on localhost:6333")
    print("  - Tables created (run scripts\\init_db.py first)")
    print("  - sentence-transformers installed")
    print()

    input("Press Enter to continue (Ctrl+C to cancel)...")

    run_script("load_nist_to_postgres.py", "Step 1/3: Load Postgres")
    run_script("load_nist_to_qdrant.py", "Step 2/3: Load Qdrant")
    run_script("verify_rag.py", "Step 3/3: Verify Everything")

    print("\n" + "=" * 60)
    print("ALL DONE! Week 2, Step 2 is complete.")
    print("=" * 60)
    print()
    print("What you now have:")
    print("  Postgres: 110 controls, 246 objectives, 14 families")
    print("  Qdrant:   ~370 vectors (controls + objectives + family overviews)")
    print("  RAG:      Query any control and get relevant context back")
    print()
    print("Next step: Week 3 — SSP Generation Agent")


if __name__ == "__main__":
    main()
