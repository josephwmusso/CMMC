"""
SPRS Score Calculator for CMMC Level 2.

Scoring methodology (NIST SP 800-171 DoD Assessment):
- Start at 110 (all controls met)
- Subtract points for each NOT MET control (1, 3, or 5 based on control weight)
- Partially Implemented controls scored based on CMMC assessment rules:
    - If on POA&M with approved plan: scored as MET (conditional)
    - Otherwise: scored as NOT MET (full deduction)
- SPRS floor is -203 (theoretical minimum)
- POA&M eligibility requires score >= 88 (80% threshold) for conditional cert

Reads from:
- controls table: id, family, family_abbrev, title, points, poam_eligible
- ssp_sections table: control_id, implementation_status, org_id
- poam_items table: control_id, org_id, status (enum: OPEN, IN_PROGRESS, CLOSED, OVERDUE)
"""

import sys
import os
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import text
from src.db.session import get_session


@dataclass
class ControlScore:
    control_id: str
    family: str
    family_abbrev: str
    title: str
    points: int
    implementation_status: Optional[str]
    poam_eligible: bool
    on_poam: bool = False
    deduction: int = 0
    status_label: str = "NOT ASSESSED"
    # 2.9B — when an OPEN contradiction covers this control, the scorer
    # forces NOT MET (full deduction, no POA&M credit) regardless of the
    # org's intake/implementation answer. DISMISSED/OVERRIDDEN/RESOLVED
    # contradictions are NOT loaded here — they don't impact scoring.
    contradiction_override: bool = False
    contradiction_ids: list = field(default_factory=list)


@dataclass
class FamilyScore:
    family: str
    family_abbrev: str
    total_controls: int = 0
    met: int = 0
    not_met: int = 0
    partial: int = 0
    not_assessed: int = 0
    total_points: int = 0
    points_lost: int = 0


@dataclass
class SPRSResult:
    score: int = 110              # raw score (no POA&M credit)
    conditional_score: int = 110  # with POA&M credit
    max_score: int = 110
    floor: int = -203
    met_count: int = 0
    not_met_count: int = 0
    partial_count: int = 0
    not_assessed_count: int = 0
    total_controls: int = 0
    total_deductions: int = 0     # conditional deductions (with POA&M credit)
    raw_deductions: int = 0       # raw deductions (no POA&M credit)
    poam_threshold: int = 88
    poam_eligible: bool = False
    controls: list = field(default_factory=list)
    families: dict = field(default_factory=dict)
    critical_gaps: list = field(default_factory=list)


class SPRSCalculator:
    """
    Calculate SPRS score from Postgres data.

    Usage:
        calc = SPRSCalculator(org_id="9de53b587b23450b87af")
        result = calc.calculate()
        print(f"SPRS Score: {result.score}/110")
    """

    def __init__(self, org_id: str):
        self.org_id = org_id

    def calculate(self) -> SPRSResult:
        result = SPRSResult()

        with get_session() as session:
            # All controls with optional SSP status
            rows = session.execute(text("""
                SELECT
                    c.id AS control_id,
                    c.family,
                    c.family_abbrev,
                    c.title,
                    c.points,
                    c.poam_eligible,
                    s.implementation_status
                FROM controls c
                LEFT JOIN ssp_sections s
                    ON c.id = s.control_id
                    AND s.org_id = :org_id
                ORDER BY c.family_abbrev, c.id
            """), {"org_id": self.org_id}).fetchall()

            # Active POA&M items (OPEN or IN_PROGRESS — not CLOSED or OVERDUE)
            poam_controls = set()
            poam_rows = session.execute(text("""
                SELECT control_id FROM poam_items
                WHERE org_id = :org_id
                AND status IN ('OPEN', 'IN_PROGRESS')
            """), {"org_id": self.org_id}).fetchall()
            for pr in poam_rows:
                poam_controls.add(pr[0])

            # 2.9B — OPEN contradictions force NOT MET on their affected
            # controls. DISMISSED / OVERRIDDEN / RESOLVED don't impact scoring.
            contradiction_map: dict[str, list[str]] = {}
            try:
                contra_rows = session.execute(text("""
                    SELECT id, affected_control_ids
                    FROM intake_contradictions
                    WHERE org_id = :org_id AND status = 'OPEN'
                """), {"org_id": self.org_id}).fetchall()
                import json as _json
                for contra_id, ctrls_json in contra_rows:
                    ctrls = ctrls_json
                    if isinstance(ctrls, str):
                        try:
                            ctrls = _json.loads(ctrls)
                        except Exception:
                            ctrls = []
                    if not isinstance(ctrls, list):
                        ctrls = []
                    for cid in ctrls:
                        contradiction_map.setdefault(cid, []).append(contra_id)
            except Exception:
                # intake_contradictions table may not exist yet pre-2.9A — fail open.
                contradiction_map = {}

        result.total_controls = len(rows)

        for row in rows:
            control_id, family, family_abbrev, title, points, poam_eligible, impl_status = row

            cs = ControlScore(
                control_id=control_id,
                family=family,
                family_abbrev=family_abbrev,
                title=title,
                points=points,
                implementation_status=impl_status,
                poam_eligible=poam_eligible,
                on_poam=control_id in poam_controls,
            )

            # raw_ded = deduction for raw score (no POA&M credit)
            # cond_ded = deduction for conditional score (with POA&M credit)
            #
            # 2.9B — check contradiction override BEFORE reading impl_status.
            # An OPEN contradiction forces NOT MET and denies POA&M credit
            # because the dispute (not a remediation plan) is what's causing
            # the gap. Resolving the contradiction restores normal scoring.
            overrides = contradiction_map.get(control_id, [])
            if overrides:
                cs.contradiction_override = True
                cs.contradiction_ids = overrides
                cs.deduction = points
                raw_ded = points
                cs.status_label = "NOT MET"
                result.not_met_count += 1

            elif impl_status == "Implemented":
                cs.deduction = 0
                raw_ded = 0
                cs.status_label = "MET"
                result.met_count += 1

            elif impl_status == "Partially Implemented":
                raw_ded = points  # raw always deducts for partial
                if cs.on_poam and poam_eligible:
                    cs.deduction = 0  # conditional gives POA&M credit
                    cs.status_label = "PARTIAL (ON POAM)"
                    result.partial_count += 1
                else:
                    cs.deduction = points
                    cs.status_label = "NOT MET"
                    result.not_met_count += 1

            elif impl_status == "Not Implemented":
                cs.deduction = points
                raw_ded = points
                cs.status_label = "NOT MET"
                result.not_met_count += 1

            else:
                cs.deduction = points
                raw_ded = points
                cs.status_label = "NOT ASSESSED"
                result.not_assessed_count += 1

            result.total_deductions += cs.deduction
            result.raw_deductions += raw_ded
            result.controls.append(cs)

            if points == 5 and cs.status_label in ("NOT MET", "NOT ASSESSED"):
                result.critical_gaps.append(cs)

            # Family aggregation
            if family_abbrev not in result.families:
                result.families[family_abbrev] = FamilyScore(
                    family=family, family_abbrev=family_abbrev,
                )
            fs = result.families[family_abbrev]
            fs.total_controls += 1
            fs.total_points += points
            fs.points_lost += cs.deduction
            if cs.status_label == "MET":
                fs.met += 1
            elif cs.status_label == "NOT MET":
                fs.not_met += 1
            elif cs.status_label.startswith("PARTIAL"):
                fs.partial += 1
            else:
                fs.not_assessed += 1

        result.score = max(result.max_score - result.raw_deductions, result.floor)
        result.conditional_score = max(result.max_score - result.total_deductions, result.floor)
        result.poam_eligible = result.score >= result.poam_threshold

        return result

    def get_score_summary(self) -> dict:
        r = self.calculate()

        # 2.9B — contradiction impact aggregation.
        overridden = [c for c in r.controls if c.contradiction_override]
        contradiction_impact = {
            "controls_overridden": len(overridden),
            "points_lost": sum(c.points for c in overridden),
            "open_contradictions": len({cid for c in overridden for cid in c.contradiction_ids}),
        }

        return {
            "score": r.score,
            "conditional_score": r.conditional_score,
            "max_score": r.max_score,
            "percentage": round((r.score / r.max_score) * 100, 1) if r.max_score > 0 else 0,
            "met": r.met_count,
            "not_met": r.not_met_count,
            "partial": r.partial_count,
            "not_assessed": r.not_assessed_count,
            "total_controls": r.total_controls,
            "total_deductions": r.total_deductions,
            "poam_eligible": r.poam_eligible,
            "contradiction_impact": contradiction_impact,
            "critical_gaps": [
                {
                    "control_id": c.control_id,
                    "title": c.title,
                    "points": c.points,
                    "family": c.family_abbrev,
                }
                for c in r.critical_gaps
            ],
            "families": {
                abbrev: {
                    "family": fs.family,
                    "total": fs.total_controls,
                    "met": fs.met,
                    "not_met": fs.not_met,
                    "partial": fs.partial,
                    "not_assessed": fs.not_assessed,
                    "points_available": fs.total_points,
                    "points_lost": fs.points_lost,
                }
                for abbrev, fs in r.families.items()
            },
            "details": [
                {
                    "control_id": c.control_id,
                    "title": c.title,
                    "family": c.family_abbrev,
                    "points": c.points,
                    "implementation_status": c.implementation_status or "NOT ASSESSED",
                    "status_label": c.status_label,
                    "deduction": c.deduction,
                    "on_poam": c.on_poam,
                    "contradiction_override": c.contradiction_override,
                    "contradiction_ids": list(c.contradiction_ids),
                }
                for c in r.controls
            ],
        }


if __name__ == "__main__":
    org_id = sys.argv[1] if len(sys.argv) > 1 else "9de53b587b23450b87af"
    calc = SPRSCalculator(org_id=org_id)
    result = calc.calculate()

    print(f"\n{'='*60}")
    print(f"  SPRS RAW SCORE:         {result.score} / {result.max_score}")
    print(f"  SPRS CONDITIONAL SCORE: {result.conditional_score} / {result.max_score}")
    print(f"{'='*60}")
    print(f"  Met: {result.met_count}  |  Not Met: {result.not_met_count}  |  "
          f"Partial: {result.partial_count}  |  Not Assessed: {result.not_assessed_count}")
    print(f"  Raw Deductions: {result.raw_deductions} pts  |  "
          f"Conditional Deductions: {result.total_deductions} pts")
    print(f"  POA&M Eligible (>=88): {'YES' if result.poam_eligible else 'NO'}")

    if result.critical_gaps:
        print(f"\n  CRITICAL GAPS (5-point controls):")
        for g in result.critical_gaps:
            print(f"    - {g.control_id}: {g.title} ({g.points} pts)")

    print(f"\n  FAMILY BREAKDOWN:")
    for abbrev in sorted(result.families.keys()):
        fs = result.families[abbrev]
        pct = round(fs.met / fs.total_controls * 100) if fs.total_controls else 0
        print(f"    {abbrev:5s}  {fs.met}/{fs.total_controls} met ({pct}%)  "
              f"[-{fs.points_lost} pts]")
    print()
