"""
Test suite for SPRS Scoring, Gap Assessment, and POA&M generation.

Run with:
    cd D:\\cmmc-platform
    python scripts\\test_scoring.py

Requires: Docker running (Postgres), evidence uploaded (Week 4-5).
Note: SSP sections may be empty (0 rows) — tests handle this gracefully.
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from src.db.session import get_session
from src.scoring.sprs import SPRSCalculator, SPRSResult
from src.scoring.gap_assessment import GapAssessmentEngine
from src.scoring.poam import POAMGenerator

ORG_ID = "9de53b587b23450b87af"
TOTAL_CONTROLS = 110
MAX_SPRS = 110
SPRS_FLOOR = -203
POAM_THRESHOLD = 88

passed = 0
failed = 0
errors = []


def check(name: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        msg = f"  ❌ {name}"
        if detail:
            msg += f" — {detail}"
        print(msg)
        errors.append(name)


def test_db_direct():
    """Verify raw DB state."""
    print("\n--- Direct DB Verification ---")

    with get_session() as session:
        ctrl_count = session.execute(text("SELECT COUNT(*) FROM controls")).scalar()
        check("110 controls in DB", ctrl_count == 110, f"got {ctrl_count}")

        ssp_count = session.execute(text(
            "SELECT COUNT(*) FROM ssp_sections WHERE org_id = :org_id"
        ), {"org_id": ORG_ID}).scalar()
        if ssp_count == 0:
            print(f"  ⚠️  SSP sections: 0 rows (SSP not yet generated for this org)")
            print(f"      Run: python scripts\\generate_ssp.py to populate SSP data")
            print(f"      Tests will proceed — all controls scored as NOT ASSESSED")
        else:
            check(f"SSP sections exist for dev org", True, f"got {ssp_count}")

        weights = session.execute(text(
            "SELECT points, COUNT(*) FROM controls GROUP BY points ORDER BY points"
        )).fetchall()
        weight_map = {w: c for w, c in weights}
        check("11 five-point controls", weight_map.get(5, 0) == 11,
              f"got {weight_map.get(5, 0)}")
        check("22 three-point controls", weight_map.get(3, 0) == 22,
              f"got {weight_map.get(3, 0)}")
        check("77 one-point controls", weight_map.get(1, 0) == 77,
              f"got {weight_map.get(1, 0)}")

        ssp_ctrl = session.execute(text(
            "SELECT poam_eligible FROM controls WHERE id = 'CA.L2-3.12.4'"
        )).scalar()
        check("CA.L2-3.12.4 not POA&M eligible", ssp_ctrl == False,
              f"got {ssp_ctrl}")

        ev_count = session.execute(text(
            "SELECT COUNT(*) FROM evidence_artifacts WHERE org_id = :org_id"
        ), {"org_id": ORG_ID}).scalar()
        check("Evidence artifacts exist", ev_count > 0, f"got {ev_count}")

        # Verify poam_status enum values
        enum_vals = session.execute(text(
            "SELECT unnest(enum_range(NULL::poam_status))"
        )).fetchall()
        enum_set = {r[0] for r in enum_vals}
        check("poam_status enum has OPEN", "OPEN" in enum_set, f"got {enum_set}")
        check("poam_status enum has CLOSED", "CLOSED" in enum_set, f"got {enum_set}")

    return ssp_count


def test_sprs_calculator():
    print("\n--- SPRS Score Calculator ---")
    calc = SPRSCalculator(org_id=ORG_ID)
    result = calc.calculate()

    check("Result is SPRSResult", isinstance(result, SPRSResult))
    check("Total controls is 110", result.total_controls == TOTAL_CONTROLS,
          f"got {result.total_controls}")
    check("Max score is 110", result.max_score == MAX_SPRS)
    check("Floor is -203", result.floor == SPRS_FLOOR)

    check("Score >= floor (-203)", result.score >= SPRS_FLOOR,
          f"got {result.score}")
    check("Score <= 110", result.score <= MAX_SPRS,
          f"got {result.score}")

    # Math consistency
    computed_total = result.met_count + result.not_met_count + result.partial_count + result.not_assessed_count
    check("Status counts sum to total", computed_total == result.total_controls,
          f"{computed_total} vs {result.total_controls}")

    expected_score = max(MAX_SPRS - result.total_deductions, SPRS_FLOOR)
    check("Score = 110 - deductions (clamped)", result.score == expected_score,
          f"score={result.score}, expected={expected_score}")

    sum_deductions = sum(c.deduction for c in result.controls)
    check("Control deductions sum matches total", sum_deductions == result.total_deductions,
          f"sum={sum_deductions}, total={result.total_deductions}")

    check("POA&M eligible iff score >= 88",
          result.poam_eligible == (result.score >= POAM_THRESHOLD),
          f"score={result.score}, eligible={result.poam_eligible}")

    family_control_sum = sum(fs.total_controls for fs in result.families.values())
    check("Family totals sum to 110", family_control_sum == TOTAL_CONTROLS,
          f"got {family_control_sum}")
    check("14 families present", len(result.families) == 14,
          f"got {len(result.families)}")

    for cg in result.critical_gaps:
        if cg.points != 5:
            check(f"Critical gap {cg.control_id} is 5-point", False, f"got {cg.points}")
            break
    else:
        check("All critical gaps are 5-point controls", True)

    summary = calc.get_score_summary()
    check("Summary is dict with 'score' key", isinstance(summary, dict) and "score" in summary)
    check("Summary score matches result", summary["score"] == result.score)

    print(f"\n  📊 SPRS Score: {result.score}/{MAX_SPRS}")
    print(f"     Met: {result.met_count}, Not Met: {result.not_met_count}, "
          f"Partial: {result.partial_count}, Not Assessed: {result.not_assessed_count}")
    return result


def test_gap_assessment():
    print("\n--- Gap Assessment Engine ---")
    engine = GapAssessmentEngine(org_id=ORG_ID)
    result = engine.assess()

    check("Total controls is 110", result.total_controls == TOTAL_CONTROLS,
          f"got {result.total_controls}")
    check("SSP + no SSP sums to total",
          result.controls_with_ssp + result.controls_without_ssp == TOTAL_CONTROLS,
          f"{result.controls_with_ssp} + {result.controls_without_ssp}")
    check("Evidence + no evidence sums to total",
          result.controls_with_evidence + result.controls_without_evidence == TOTAL_CONTROLS,
          f"{result.controls_with_evidence} + {result.controls_without_evidence}")
    check("SSP completion pct 0-100",
          0 <= result.ssp_completion_pct <= 100,
          f"got {result.ssp_completion_pct}")
    check("Evidence coverage pct 0-100",
          0 <= result.evidence_coverage_pct <= 100,
          f"got {result.evidence_coverage_pct}")

    valid_types = {"NO_SSP", "NO_EVIDENCE", "PARTIAL_EVIDENCE",
                   "SSP_NOT_IMPLEMENTED", "SSP_PARTIAL"}
    for gap in result.gaps:
        if gap.gap_type not in valid_types:
            check(f"Gap type valid: {gap.gap_type}", False)
            break
    else:
        check("All gap types are valid", True)

    for gap in result.gaps:
        expected_sev = "CRITICAL" if gap.points >= 5 else ("HIGH" if gap.points >= 3 else "MEDIUM")
        if gap.severity != expected_sev:
            check(f"Severity for {gap.control_id}", False,
                  f"expected {expected_sev}, got {gap.severity}")
            break
    else:
        check("All severities match point weights", True)

    check("Fully compliant count reasonable",
          result.controls_fully_compliant <= TOTAL_CONTROLS,
          f"got {result.controls_fully_compliant}")

    summary = engine.get_summary()
    check("Summary has gap_details", "gap_details" in summary)
    check("Summary gap count matches", len(summary["gap_details"]) == len(result.gaps),
          f"{len(summary['gap_details'])} vs {len(result.gaps)}")

    print(f"\n  📊 Gap Assessment:")
    print(f"     SSP: {result.controls_with_ssp}/{TOTAL_CONTROLS} ({result.ssp_completion_pct}%)")
    print(f"     Evidence: {result.controls_with_evidence}/{TOTAL_CONTROLS} ({result.evidence_coverage_pct}%)")
    print(f"     Fully Compliant: {result.controls_fully_compliant}")
    print(f"     Total Gaps: {len(result.gaps)}")
    return result


def test_poam_generator(ssp_count: int):
    print("\n--- POA&M Generator ---")
    gen = POAMGenerator(org_id=ORG_ID)

    # Generate
    created, skipped = gen.generate_from_ssp()
    check("Generate returns tuple", isinstance(created, int) and isinstance(skipped, int))
    check("Created >= 0", created >= 0)
    check("Skipped >= 0", skipped >= 0)

    if ssp_count == 0:
        check("No POA&M created when SSP is empty (expected)", created == 0,
              f"created {created} but SSP is empty")
    else:
        # Verify CA.L2-3.12.4 NOT on POA&M
        with get_session() as session:
            ssp_poam = session.execute(text(
                "SELECT COUNT(*) FROM poam_items WHERE control_id = 'CA.L2-3.12.4' "
                "AND org_id = :org_id AND status IN ('OPEN', 'IN_PROGRESS')"
            ), {"org_id": ORG_ID}).scalar()
        check("CA.L2-3.12.4 (SSP) NOT on POA&M", ssp_poam == 0,
              f"found {ssp_poam} active POA&M items for SSP control")

    # Summary
    summary = gen.get_poam_summary()
    check("Summary has items list", "items" in summary)
    check("Summary has status_counts", "status_counts" in summary)
    check("Summary has total_points_at_risk", "total_points_at_risk" in summary)

    # All active POA&M items should have deadlines
    active_items = [i for i in summary["items"] if i["status"] in ("OPEN", "IN_PROGRESS")]
    for item in active_items:
        if not item["deadline"]:
            check(f"POA&M {item['poam_id']} has deadline", False)
            break
    else:
        check("All active POA&M items have deadlines",
              True if active_items else True)  # pass if no items

    # Re-run should not create duplicates
    created2, _ = gen.generate_from_ssp()
    check("Re-run creates 0 duplicates", created2 == 0,
          f"created {created2} on re-run")

    print(f"\n  📊 POA&M: {summary['total_items']} items, "
          f"{summary['total_points_at_risk']} points at risk")
    return summary


def test_cross_consistency(sprs_result, gap_result):
    print("\n--- Cross-Consistency Checks ---")

    sprs_not_met = sprs_result.not_met_count + sprs_result.not_assessed_count
    check("SPRS not-met > 0 implies gaps exist",
          sprs_not_met == 0 or len(gap_result.gaps) > 0,
          f"not_met={sprs_not_met}, gaps={len(gap_result.gaps)}")

    if sprs_result.not_assessed_count > 0:
        check("Not-assessed controls → SSP incomplete",
              gap_result.ssp_completion_pct < 100,
              f"not_assessed={sprs_result.not_assessed_count}, "
              f"ssp_pct={gap_result.ssp_completion_pct}")

    check("SPRS deductions > 0 implies score < 110",
          sprs_result.total_deductions == 0 or sprs_result.score < MAX_SPRS,
          f"deductions={sprs_result.total_deductions}, score={sprs_result.score}")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"  SCORING ENGINE TEST SUITE")
    print(f"  Org: {ORG_ID}")
    print(f"{'='*60}")

    ssp_count = test_db_direct()
    sprs = test_sprs_calculator()
    gaps = test_gap_assessment()
    test_poam_generator(ssp_count)
    test_cross_consistency(sprs, gaps)

    print(f"\n{'='*60}")
    print(f"  RESULTS: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    if errors:
        print(f"  Failed tests:")
        for e in errors:
            print(f"    - {e}")

    if ssp_count == 0:
        print(f"\n  ⚠️  NOTE: SSP sections are empty. To get meaningful scores,")
        print(f"     run: python scripts\\generate_ssp.py")
        print(f"     Then re-run this test suite.")

    print()
    sys.exit(0 if failed == 0 else 1)
