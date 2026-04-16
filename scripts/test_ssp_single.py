"""
scripts/test_ssp_single.py

Quick test: generate SSP narrative for a single control.
Run from D:\\cmmc-platform with venv activated:

    python scripts/test_ssp_single.py

Tests the full pipeline: Qdrant RAG -> Claude API -> parsed output.
Uses the demo org profile (Apex Defense Solutions).
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.llm_client import get_llm
from src.agents.ssp_generator_v2 import SSPGenerator
from src.agents.org_profile import build_org_profile
from src.db.session import get_session


def _get_profile():
    with get_session() as db:
        return build_org_profile("9de53b587b23450b87af", db)


def main():
    # Pick a high-value control to test with (5-point, access control)
    test_controls = [
        "AC.L2-3.1.1",   # 5 pts - Authorized Access Control
        "IA.L2-3.5.3",   # 3 pts - Multifactor Authentication
        "SC.L2-3.13.11", # 5 pts - CUI Encryption
    ]

    print("=" * 70)
    print("SSP SINGLE CONTROL TEST")
    print("=" * 70)

    # Initialize
    print("\n[1/3] Initializing LLM client...")
    llm = get_llm()
    print(f"  Provider: {llm.provider}")
    print(f"  Model: {llm.model}")

    print("\n[2/3] Initializing SSP Generator (connects to Qdrant)...")
    generator = SSPGenerator(llm=llm)

    # Test each control
    for control_id in test_controls:
        print(f"\n{'=' * 70}")
        print(f"[3/3] Generating SSP narrative for: {control_id}")
        print("=" * 70)

        start = time.time()
        result = generator.generate_single_control(
            control_id=control_id,
            org_profile=_get_profile(),
        )
        elapsed = time.time() - start

        if result.error:
            print(f"\n  ERROR: {result.error}")
            continue

        print(f"\n  Status: {result.status}")
        print(f"  Time:   {elapsed:.1f}s")
        print(f"\n  --- NARRATIVE ---")
        print(f"  {result.narrative[:500]}{'...' if len(result.narrative) > 500 else ''}")
        print(f"\n  --- EVIDENCE ({len(result.evidence_artifacts)} items) ---")
        for ev in result.evidence_artifacts[:5]:
            print(f"    - {ev}")
        print(f"\n  --- OBJECTIVES ({len(result.objectives_addressed)} addressed) ---")
        for obj_id, how in list(result.objectives_addressed.items())[:3]:
            print(f"    {obj_id}: {how[:80]}...")
        print(f"\n  --- GAPS ({len(result.gaps)} found) ---")
        for gap in result.gaps:
            print(f"    - {gap[:100]}")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
