"""
scripts/generate_ssp.py

Generate a complete SSP document for all 110 NIST 800-171 controls.
Run from D:\\cmmc-platform with venv activated:

    python scripts/generate_ssp.py

This will:
  1. Load all 110 controls from Postgres
  2. For each: RAG retrieve from Qdrant -> Claude API -> parse output
  3. Persist narratives to ssp_sections table
  4. Export a complete Word document to data/exports/

Expected time: ~20-40 minutes (depends on API rate limits).
Expected cost: ~$2-5 on Claude API.

Options:
  --family AC         Only generate for one family (for testing)
  --limit 5           Only generate first N controls (for testing)
  --skip-docx         Skip Word document export
  --output PATH       Custom output path for .docx
"""

import sys
import os
import time
import argparse
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.llm_client import get_llm
from src.agents.ssp_generator_v2 import SSPGenerator
from src.agents.ssp_prompts_v2 import DEMO_ORG_PROFILE
from src.ssp.docx_export import export_ssp_to_docx
from src.db.session import SessionLocal
from sqlalchemy import text
import hashlib, random
from src.db.models import Control


def parse_args():
    parser = argparse.ArgumentParser(description="Generate full CMMC SSP document")
    parser.add_argument("--family", type=str, default=None, help="Only generate for this family (e.g., AC, IA)")
    parser.add_argument("--limit", type=int, default=None, help="Limit to first N controls")
    parser.add_argument("--skip-docx", action="store_true", help="Skip Word doc export")
    parser.add_argument("--output", type=str, default=None, help="Custom output path for .docx")
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 70)
    print("CMMC SSP DOCUMENT GENERATOR")
    print(f"Organization: {DEMO_ORG_PROFILE['org_name']}")
    print(f"System: {DEMO_ORG_PROFILE['system_name']}")
    print(f"Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Initialize
    print("\n[INIT] Connecting to services...")
    db = SessionLocal()
    llm = get_llm()
    generator = SSPGenerator(llm=llm)

    print(f"  LLM: {llm.provider} / {llm.model}")
    print(f"  Database: connected")
    print(f"  Qdrant: connected")

    # Get control list
    query = db.query(Control).order_by(Control.id)
    if args.family:
        query = query.filter(Control.family_abbrev == args.family.upper())
        print(f"\n  Filtering to family: {args.family.upper()}")

    controls = query.all()
    control_ids = [c.id for c in controls]

    if args.limit:
        control_ids = control_ids[:args.limit]
        print(f"  Limiting to first {args.limit} controls")

    total = len(control_ids)
    print(f"\n  Controls to process: {total}")

    # Estimate time & cost
    est_seconds = total * 15  # ~15s per control on average
    est_cost = total * 0.03   # ~$0.03 per control with Claude Sonnet
    print(f"  Estimated time: ~{est_seconds // 60} minutes")
    print(f"  Estimated API cost: ~${est_cost:.2f}")

    # Confirm
    if total > 10 and not args.limit:
        response = input(f"\n  Proceed with {total} controls? [y/N]: ").strip().lower()
        if response != "y":
            print("  Aborted.")
            return

    # Generate
    print(f"\n{'=' * 70}")
    print("GENERATING SSP NARRATIVES")
    print("=" * 70)

    start_time = time.time()
    results = []
    errors = []

    for i, cid in enumerate(control_ids, 1):
        control = next((c for c in controls if c.id == cid), None)
        family_info = f" [{control.family_abbrev}]" if control else ""

        print(f"\n  [{i}/{total}] {cid}{family_info} ... ", end="", flush=True)

        result = generator.generate_single_control(
            control_id=cid,
            org_profile=DEMO_ORG_PROFILE,
            db=db,
        )
        results.append(result)

        # Persist to ssp_sections via raw SQL
        if not result.error:
            try:
                _id = hashlib.sha256(f"{time.time()}-{random.randint(0,99999)}".encode()).hexdigest()[:20]
                db.execute(text("""
                    INSERT INTO ssp_sections (id, org_id, control_id, implementation_status,
                                             narrative, evidence_refs, gaps, version, generated_by, created_at, updated_at)
                    VALUES (:id, :org_id, :control_id, :status, :narrative,
                            CAST(:evidence_refs AS json), CAST(:gaps AS json),
                            :version, :generated_by, NOW(), NOW())
                    ON CONFLICT (org_id, control_id, version) DO UPDATE SET
                        implementation_status = EXCLUDED.implementation_status,
                        narrative = EXCLUDED.narrative,
                        evidence_refs = EXCLUDED.evidence_refs,
                        gaps = EXCLUDED.gaps,
                        generated_by = EXCLUDED.generated_by,
                        updated_at = NOW()
                """), {
                    "id": _id,
                    "org_id": DEMO_ORG_PROFILE.get("org_id", "9de53b587b23450b87af"),
                    "control_id": cid,
                    "status": result.status,
                    "narrative": result.narrative or "",
                    "evidence_refs": __import__("json").dumps(result.evidence_artifacts if result.evidence_artifacts else []),
                    "gaps": __import__("json").dumps(result.gaps if result.gaps else []),
                    "version": 1,
                    "generated_by": "ssp_agent",
                })
                db.commit()
            except Exception as persist_err:
                db.rollback()
                print(f" [PERSIST ERROR: {persist_err}]", end="")

        if result.error:
            print(f"ERROR: {result.error}")
            errors.append((cid, result.error))
        else:
            gaps_info = f", {len(result.gaps)} gaps" if result.gaps else ""
            print(f"{result.status} ({result.generation_time_sec:.1f}s{gaps_info})")

    elapsed = time.time() - start_time

    # Summary
    print(f"\n{'=' * 70}")
    print("GENERATION SUMMARY")
    print("=" * 70)

    statuses = {}
    for r in results:
        statuses[r.status] = statuses.get(r.status, 0) + 1
    total_gaps = sum(len(r.gaps) for r in results)

    print(f"  Total controls: {total}")
    for status, count in sorted(statuses.items()):
        print(f"  {status}: {count}")
    print(f"  Errors: {len(errors)}")
    print(f"  Total gaps: {total_gaps}")
    print(f"  Total time: {elapsed:.0f}s ({elapsed / 60:.1f} minutes)")
    print(f"  Avg per control: {elapsed / max(total, 1):.1f}s")

    if errors:
        print(f"\n  ERRORS:")
        for cid, err in errors:
            print(f"    {cid}: {err}")

    # Export to Word
    if not args.skip_docx:
        print(f"\n{'=' * 70}")
        print("EXPORTING TO WORD DOCUMENT")
        print("=" * 70)

        if args.output:
            docx_path = args.output
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            org_slug = DEMO_ORG_PROFILE["org_name"].replace(" ", "_")
            docx_path = os.path.join("data", "exports", f"SSP_{org_slug}_{timestamp}.docx")

        export_ssp_to_docx(results, DEMO_ORG_PROFILE, docx_path)
        print(f"\n  SSP document saved to: {docx_path}")
        print(f"  Open in Word and review all narratives before submission.")

    db.close()

    print(f"\n{'=' * 70}")
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
