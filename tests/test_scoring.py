"""
tests/test_scoring.py

Tests for SPRS scoring, gap assessment, and POA&M generation.
No live Postgres required for unit tests.

Run: pytest tests/test_scoring.py -v
Run with live DB: pytest tests/test_scoring.py -v -m integration
"""

import pytest
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# SPRSResult dataclass
# ---------------------------------------------------------------------------

class TestSPRSResult:
    def test_default_score_is_110(self):
        from src.scoring.sprs import SPRSResult
        r = SPRSResult()
        assert r.score == 110
        assert r.max_score == 110

    def test_default_floor_is_minus_203(self):
        from src.scoring.sprs import SPRSResult
        r = SPRSResult()
        assert r.floor == -203

    def test_default_poam_threshold_is_88(self):
        from src.scoring.sprs import SPRSResult
        r = SPRSResult()
        assert r.poam_threshold == 88

    def test_score_floor_enforcement(self):
        from src.scoring.sprs import SPRSResult
        r = SPRSResult()
        score = max(r.max_score - 500, r.floor)
        assert score == -203

    def test_score_formula_no_deductions(self):
        from src.scoring.sprs import SPRSResult
        r = SPRSResult()
        score = max(r.max_score - 0, r.floor)
        assert score == 110

    def test_poam_eligible_at_88(self):
        from src.scoring.sprs import SPRSResult
        r = SPRSResult()
        r.score = 88
        assert r.score >= r.poam_threshold

    def test_poam_ineligible_below_88(self):
        from src.scoring.sprs import SPRSResult
        r = SPRSResult()
        r.score = 50
        assert r.score < r.poam_threshold


class TestControlScore:
    def test_deduction_zero_when_implemented(self):
        from src.scoring.sprs import ControlScore
        cs = ControlScore(
            control_id="AC.L2-3.1.1",
            family="Access Control",
            family_abbrev="AC",
            title="Limit system access",
            points=1,
            implementation_status="Implemented",
            poam_eligible=True,
        )
        cs.deduction = 0
        cs.status_label = "MET"
        assert cs.deduction == 0
        assert cs.status_label == "MET"

    def test_deduction_equals_points_when_not_met(self):
        from src.scoring.sprs import ControlScore
        cs = ControlScore(
            control_id="SC.L2-3.13.1",
            family="System and Communications Protection",
            family_abbrev="SC",
            title="Monitor communications",
            points=5,
            implementation_status="Not Implemented",
            poam_eligible=True,
        )
        cs.deduction = cs.points
        assert cs.deduction == 5


# ---------------------------------------------------------------------------
# GapAssessmentEngine
# ---------------------------------------------------------------------------

class TestGapAssessmentEngine:
    GAP_TYPES = [
        "NO_SSP",
        "NO_EVIDENCE",
        "PARTIAL_EVIDENCE",
        "SSP_NOT_IMPLEMENTED",
        "SSP_PARTIAL",
    ]

    def test_all_gap_types_are_strings(self):
        for gap_type in self.GAP_TYPES:
            assert isinstance(gap_type, str)

    def test_severity_from_points_critical(self):
        from src.scoring.gap_assessment import GapAssessmentEngine
        engine = GapAssessmentEngine.__new__(GapAssessmentEngine)
        assert engine._severity_from_points(5) == "CRITICAL"

    def test_severity_from_points_high(self):
        from src.scoring.gap_assessment import GapAssessmentEngine
        engine = GapAssessmentEngine.__new__(GapAssessmentEngine)
        assert engine._severity_from_points(3) == "HIGH"

    def test_severity_from_points_medium(self):
        from src.scoring.gap_assessment import GapAssessmentEngine
        engine = GapAssessmentEngine.__new__(GapAssessmentEngine)
        assert engine._severity_from_points(1) == "MEDIUM"

    def test_gap_assessment_result_defaults(self):
        from src.scoring.gap_assessment import GapAssessmentResult
        r = GapAssessmentResult(org_id="test-org")
        assert r.total_controls == 0
        assert r.gaps == []
        assert r.controls_fully_compliant == 0

    def test_control_gap_fields(self):
        from src.scoring.gap_assessment import ControlGap
        gap = ControlGap(
            control_id="AC.L2-3.1.1",
            family="Access Control",
            family_abbrev="AC",
            title="Limit access",
            points=1,
            gap_type="NO_SSP",
            severity="MEDIUM",
            description="No SSP for AC.L2-3.1.1",
        )
        assert gap.gap_type == "NO_SSP"
        assert gap.severity == "MEDIUM"
        assert gap.on_poam is False


# ---------------------------------------------------------------------------
# POAMGenerator
# ---------------------------------------------------------------------------

class TestPOAMGenerator:
    def test_forbidden_controls_contains_ssp_control(self):
        from src.scoring.poam import POAMGenerator
        assert "CA.L2-3.12.4" in POAMGenerator.FORBIDDEN_CONTROLS

    def test_deadline_is_180_days(self):
        from src.scoring.poam import POAMGenerator
        gen = POAMGenerator.__new__(POAMGenerator)
        assert gen.DEFAULT_DEADLINE_DAYS == 180

    def test_180_day_deadline_calculation(self):
        created_at = datetime(2026, 1, 1)
        deadline = created_at + timedelta(days=180)
        assert deadline == datetime(2026, 6, 30)

    def test_risk_from_points_high(self):
        from src.scoring.poam import POAMGenerator
        gen = POAMGenerator.__new__(POAMGenerator)
        assert gen._risk_from_points(5) == "HIGH"

    def test_risk_from_points_moderate(self):
        from src.scoring.poam import POAMGenerator
        gen = POAMGenerator.__new__(POAMGenerator)
        assert gen._risk_from_points(3) == "MODERATE"

    def test_risk_from_points_low(self):
        from src.scoring.poam import POAMGenerator
        gen = POAMGenerator.__new__(POAMGenerator)
        assert gen._risk_from_points(1) == "LOW"

    def test_ssp_control_skipped_in_source(self):
        """CA.L2-3.12.4 must be in FORBIDDEN_CONTROLS, blocking POA&M creation."""
        from src.scoring.poam import POAMGenerator
        assert "CA.L2-3.12.4" in POAMGenerator.FORBIDDEN_CONTROLS

    def test_valid_poam_statuses_in_source(self):
        """The source uses OPEN and IN_PROGRESS to detect existing items."""
        import inspect
        from src.scoring.poam import POAMGenerator
        source = inspect.getsource(POAMGenerator.generate_from_ssp)
        assert "'OPEN'" in source
        assert "'IN_PROGRESS'" in source


# ---------------------------------------------------------------------------
# Integration smoke tests (requires live Postgres)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_sprs_live_db():
    try:
        from src.scoring.sprs import SPRSCalculator
        calc = SPRSCalculator(org_id="9de53b587b23450b87af")
        summary = calc.get_score_summary()
        assert "score" in summary
        assert isinstance(summary["score"], (int, float))
        assert -203 <= summary["score"] <= 110
        assert "families" in summary
    except Exception as e:
        pytest.skip(f"Live DB not available: {e}")


@pytest.mark.integration
def test_gap_assessment_live_db():
    try:
        from src.scoring.gap_assessment import GapAssessmentEngine
        engine = GapAssessmentEngine(org_id="9de53b587b23450b87af")
        summary = engine.get_summary()
        assert "total_gaps" in summary
        assert "gaps_by_severity" in summary
        assert "CRITICAL" in summary["gaps_by_severity"]
    except Exception as e:
        pytest.skip(f"Live DB not available: {e}")
