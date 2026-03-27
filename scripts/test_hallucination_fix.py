"""
scripts/test_hallucination_fix.py
Test the evidence-gated SSP generation pipeline.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.ssp_schemas import SSPSectionOutput, ImplementationStatus
from src.agents.hallucination_detector import (
    verify_narrative,
    verify_evidence_references,
    run_verification,
    VerificationResult,
)

passed = 0
failed = 0
total = 0


def check(name: str, condition: bool, detail: str = ""):
    global passed, failed, total
    total += 1
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name}{' - ' + detail if detail else ''}")


def test_pydantic_schema():
    """Test that the schema enforces required fields."""
    print("\n=== Test 1: Pydantic Schema Validation ===\n")

    valid_data = {
        "control_id": "AC.L2-3.1.1",
        "control_title": "Authorized Access Control",
        "implementation_status": "Implemented",
        "narrative": "Apex Defense Solutions implements authorized access control using Microsoft Entra ID with role-based access assignments. All user accounts require MFA via Entra ID Conditional Access policies.",
        "evidence_references": [
            {
                "artifact_id": "ev001",
                "artifact_title": "Entra ID MFA Configuration Screenshot",
                "confidence": "direct",
                "description": "Shows MFA enforcement policy for all users"
            }
        ],
        "gaps": [],
        "assessment_objectives_met": ["3.1.1[a]", "3.1.1[b]"],
        "assessment_objectives_not_met": [],
    }

    try:
        section = SSPSectionOutput(**valid_data)
        check("Valid section parses successfully", True)
        check("Status is Implemented", section.implementation_status == ImplementationStatus.IMPLEMENTED)
    except Exception as e:
        check("Valid section parses successfully", False, str(e))

    bad_data = valid_data.copy()
    bad_data["implementation_status"] = "Partially Implemented"
    bad_data["gaps"] = []

    try:
        section = SSPSectionOutput(**bad_data)
        check("Partial without gaps rejected", False, "Should have raised ValidationError")
    except Exception:
        check("Partial without gaps rejected", True)

    bad_data2 = valid_data.copy()
    bad_data2["narrative"] = "Too short"
    try:
        section = SSPSectionOutput(**bad_data2)
        check("Short narrative rejected", False, "Should have raised ValidationError")
    except Exception:
        check("Short narrative rejected", True)


def test_hallucination_detector():
    """Test that fabricated values are detected."""
    print("\n=== Test 2: Hallucination Detector ===\n")

    bad_narrative = (
        "Apex Defense Solutions enforces authorized access control on server SRV-DC01 "
        "at 192.168.10.50. The domain controller at 10.0.1.100 manages all Active "
        "Directory accounts with MFA enforced via Entra ID. Firewall rule 4.2.1 on "
        "the PA-450 restricts CUI access to VLAN 10 (192.168.10.0/24)."
    )

    result = verify_narrative(
        control_id="AC.L2-3.1.1",
        narrative=bad_narrative,
        evidence_artifacts=[],
    )

    check("Detects fabricated IPs", any(
        f.finding_type == "ip_address" for f in result.findings
    ))
    check("Detects fabricated hostname (SRV-DC01)", any(
        f.finding_type == "hostname" and "SRV" in f.value for f in result.findings
    ))
    check("Detects subnet CIDR", any(
        f.finding_type == "subnet" for f in result.findings
    ))
    check("Result is FAIL", not result.passed)
    check(
        f"Found {result.critical_count} critical findings",
        result.critical_count >= 2,
    )

    good_narrative = (
        "Apex Defense Solutions implements authorized access control using Microsoft "
        "Entra ID as the centralized identity provider. All user accounts require "
        "multi-factor authentication via Entra ID Conditional Access policies. "
        "Role-based access control is enforced through Entra ID security groups, "
        "with access reviews conducted quarterly by the IT Security Manager."
    )

    result2 = verify_narrative(
        control_id="AC.L2-3.1.1",
        narrative=good_narrative,
        evidence_artifacts=[],
    )

    check("Clean narrative passes", result2.passed)
    check("No critical findings", result2.critical_count == 0)


def test_phantom_evidence():
    """Test detection of references to non-existent evidence."""
    print("\n=== Test 3: Phantom Evidence Detection ===\n")

    claimed = ["ev001", "ev002", "ev999"]
    actual = {"ev001", "ev002"}

    findings = verify_evidence_references("AC.L2-3.1.1", claimed, actual)
    check("Detects phantom artifact ev999", len(findings) == 1)
    check("Phantom finding is critical", findings[0].severity == "critical" if findings else False)
    check("Phantom ID matches", findings[0].value == "ev999" if findings else False)


def test_evidence_gating_prompts():
    """Test that prompt builder changes behavior based on evidence."""
    print("\n=== Test 4: Evidence-Gated Prompt Builder ===\n")

    from src.agents.ssp_prompts_v2 import build_evidence_section

    # No evidence
    text_out, instructions = build_evidence_section([])
    check("No evidence -> gap report mode", "NO EVIDENCE" in text_out)
    check("No evidence -> NOT fabricate instruction", "DO NOT fabricate" in instructions)
    check("No evidence -> Not Implemented instruction", "Not Implemented" in instructions)

    # Published evidence
    text2, instructions2 = build_evidence_section([
        {"id": "ev001", "title": "MFA Config", "state": "PUBLISHED", "evidence_type": "screenshot",
         "source_system": "Entra ID", "description": "MFA policy screenshot", "sha256_hash": "abc123"}
    ])
    check("Published evidence -> shows artifact", "ev001" in text2)
    check("Published evidence -> reference instruction", "PUBLISHED" in instructions2)
    check("Published evidence -> not gap mode", "GAP REPORT" not in instructions2)

    # Draft-only evidence
    text3, instructions3 = build_evidence_section([
        {"id": "ev002", "title": "Draft Policy", "state": "DRAFT", "evidence_type": "policy",
         "source_system": "manual", "description": "Draft access policy", "sha256_hash": None}
    ])
    check("Draft evidence -> warns about state", "not final" in text3.lower() or "STATE=DRAFT" in text3)
    check("Draft evidence -> scoring rules note", "CMMC scoring rules" in instructions3)


def test_full_pipeline():
    """Integration test — requires Docker + API key."""
    print("\n=== Test 5: Full Pipeline (requires Docker + API key) ===\n")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  SKIP: ANTHROPIC_API_KEY not set")
        return

    try:
        from src.agents.ssp_generator_v2 import SSPGeneratorV2

        gen = SSPGeneratorV2()

        print("  Generating AC.L2-3.1.1 (may have demo evidence)...")
        result = gen.generate_section("AC.L2-3.1.1")

        parsed = result["parsed"]
        check("Generation completed", parsed is not None)
        check("Has implementation_status", "implementation_status" in parsed)
        check("Has narrative", len(parsed.get("narrative", "")) > 50)
        check(f"Mode: {result['generation_mode']}", True)
        check(f"Verification: {result['verification'].summary()}", True)

        print("\n  Generating MA.L2-3.7.5 (unlikely to have evidence)...")
        result2 = gen.generate_section("MA.L2-3.7.5")

        parsed2 = result2["parsed"]
        if result2["evidence_count"] == 0:
            check(
                "No-evidence control -> gap report or not implemented",
                parsed2["implementation_status"] in ("Not Implemented", "Partially Implemented")
                or "GAP REPORT" in parsed2.get("narrative", "").upper()
            )
        else:
            check(f"MA.L2-3.7.5 has {result2['evidence_count']} evidence (ok)", True)

    except Exception as e:
        check(f"Pipeline test failed: {e}", False)


if __name__ == "__main__":
    print("=" * 60)
    print("HALLUCINATION FIX - TEST SUITE")
    print("=" * 60)

    test_pydantic_schema()
    test_hallucination_detector()
    test_phantom_evidence()
    test_evidence_gating_prompts()

    if "--full" in sys.argv:
        test_full_pipeline()
    else:
        print("\n  SKIP: Integration test (run with --full)")

    print(f"\n{'='*60}")
    print(f"RESULTS: {passed}/{total} passed, {failed} failed")
    print(f"{'='*60}")

    sys.exit(0 if failed == 0 else 1)
