"""
Gap Assessment Engine for CMMC Level 2.

Cross-references three data sources to identify compliance gaps:
1. SSP sections (ssp_sections) — does a narrative exist? what's the status?
2. Evidence artifacts (evidence_artifacts) — are there PUBLISHED evidence files?
3. Control requirements (controls) — what's the weight/criticality?

Gap types:
- NO_SSP: Control has no SSP narrative at all
- NO_EVIDENCE: Control has no evidence mapped (or only DRAFT evidence)
- PARTIAL_EVIDENCE: Control has some evidence but not PUBLISHED
- SSP_NOT_IMPLEMENTED: SSP exists but status is "Not Implemented"
- SSP_PARTIAL: SSP exists but status is "Partially Implemented" with no POA&M

Reads from: controls, ssp_sections, evidence_artifacts, evidence_control_map, poam_items
poam_items.status enum: OPEN, IN_PROGRESS, CLOSED, OVERDUE
"""

import sys
import os
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import text
from src.db.session import get_session


@dataclass
class EvidenceInfo:
    total_artifacts: int = 0
    published: int = 0
    approved: int = 0
    reviewed: int = 0
    draft: int = 0
    artifact_names: list = field(default_factory=list)


@dataclass
class ControlGap:
    control_id: str
    family: str
    family_abbrev: str
    title: str
    points: int
    gap_type: str
    severity: str
    description: str
    implementation_status: Optional[str] = None
    evidence_info: Optional[EvidenceInfo] = None
    on_poam: bool = False
    poam_eligible: bool = True
    remediation_hint: str = ""


@dataclass
class GapAssessmentResult:
    org_id: str
    assessed_at: str = ""
    total_controls: int = 0
    controls_with_ssp: int = 0
    controls_without_ssp: int = 0
    controls_with_evidence: int = 0
    controls_without_evidence: int = 0
    controls_fully_compliant: int = 0
    ssp_completion_pct: float = 0.0
    evidence_coverage_pct: float = 0.0
    gaps: list = field(default_factory=list)
    gaps_by_severity: dict = field(default_factory=lambda: {"CRITICAL": [], "HIGH": [], "MEDIUM": []})
    gaps_by_type: dict = field(default_factory=dict)


class GapAssessmentEngine:
    """
    Identify compliance gaps by cross-referencing SSP, evidence, and controls.

    Usage:
        engine = GapAssessmentEngine(org_id="9de53b587b23450b87af")
        result = engine.assess()
    """

    def __init__(self, org_id: str):
        self.org_id = org_id

    def _severity_from_points(self, points: int) -> str:
        if points >= 5:
            return "CRITICAL"
        elif points >= 3:
            return "HIGH"
        return "MEDIUM"

    def assess(self) -> GapAssessmentResult:
        result = GapAssessmentResult(
            org_id=self.org_id,
            assessed_at=datetime.utcnow().isoformat() + "Z",
        )

        with get_session() as session:
            # 1. All controls with SSP status
            controls = session.execute(text("""
                SELECT
                    c.id, c.family, c.family_abbrev, c.title, c.points, c.poam_eligible,
                    s.implementation_status, s.narrative
                FROM controls c
                LEFT JOIN ssp_sections s
                    ON c.id = s.control_id AND s.org_id = :org_id
                ORDER BY c.points DESC, c.family_abbrev, c.id
            """), {"org_id": self.org_id}).fetchall()

            # 2. Evidence mapping with artifact states
            evidence_map = {}
            ev_rows = session.execute(text("""
                SELECT
                    ecm.control_id,
                    ea.filename,
                    ea.state::text AS state
                FROM evidence_control_map ecm
                JOIN evidence_artifacts ea ON ea.id = ecm.evidence_id
                WHERE ea.org_id = :org_id
            """), {"org_id": self.org_id}).fetchall()

            for er in ev_rows:
                cid = er[0]
                if cid not in evidence_map:
                    evidence_map[cid] = EvidenceInfo()
                ei = evidence_map[cid]
                ei.total_artifacts += 1
                ei.artifact_names.append(er[1])
                state = er[2]
                if state == "PUBLISHED":
                    ei.published += 1
                elif state == "APPROVED":
                    ei.approved += 1
                elif state == "REVIEWED":
                    ei.reviewed += 1
                else:
                    ei.draft += 1

            # 3. Active POA&M items (OPEN or IN_PROGRESS)
            poam_controls = set()
            poam_rows = session.execute(text("""
                SELECT control_id FROM poam_items
                WHERE org_id = :org_id
                AND status IN ('OPEN', 'IN_PROGRESS')
            """), {"org_id": self.org_id}).fetchall()
            for pr in poam_rows:
                poam_controls.add(pr[0])

        result.total_controls = len(controls)

        for row in controls:
            cid, family, family_abbrev, title, points, poam_eligible, impl_status, narrative = row
            severity = self._severity_from_points(points)
            ev_info = evidence_map.get(cid, EvidenceInfo())
            has_ssp = impl_status is not None and narrative is not None
            has_published_evidence = ev_info.published > 0
            on_poam = cid in poam_controls

            if has_ssp:
                result.controls_with_ssp += 1
            else:
                result.controls_without_ssp += 1

            if ev_info.total_artifacts > 0:
                result.controls_with_evidence += 1
            else:
                result.controls_without_evidence += 1

            # Fully compliant — no gap
            if has_ssp and impl_status == "Implemented" and has_published_evidence:
                result.controls_fully_compliant += 1
                continue

            # --- Identify gaps ---

            if not has_ssp:
                gap = ControlGap(
                    control_id=cid, family=family, family_abbrev=family_abbrev,
                    title=title, points=points, gap_type="NO_SSP",
                    severity=severity, on_poam=on_poam, poam_eligible=poam_eligible,
                    evidence_info=ev_info,
                    description=f"No SSP narrative exists for {cid}. This control has not been assessed.",
                    remediation_hint="Run SSP generation for this control to create an implementation narrative.",
                )
                result.gaps.append(gap)
                result.gaps_by_severity[severity].append(gap)
                continue

            if impl_status == "Not Implemented":
                gap = ControlGap(
                    control_id=cid, family=family, family_abbrev=family_abbrev,
                    title=title, points=points, gap_type="SSP_NOT_IMPLEMENTED",
                    severity=severity, implementation_status=impl_status,
                    on_poam=on_poam, poam_eligible=poam_eligible,
                    evidence_info=ev_info,
                    description=f"{cid} is assessed as Not Implemented. Full {points}-point deduction applies.",
                    remediation_hint="Implement this control and update the SSP narrative with evidence of implementation." if poam_eligible else "This control CANNOT be placed on POA&M. Must be fully implemented.",
                )
                result.gaps.append(gap)
                result.gaps_by_severity[severity].append(gap)

            elif impl_status == "Partially Implemented" and not on_poam:
                gap = ControlGap(
                    control_id=cid, family=family, family_abbrev=family_abbrev,
                    title=title, points=points, gap_type="SSP_PARTIAL",
                    severity=severity, implementation_status=impl_status,
                    on_poam=False, poam_eligible=poam_eligible,
                    evidence_info=ev_info,
                    description=f"{cid} is Partially Implemented with no POA&M plan. Scores as NOT MET.",
                    remediation_hint="Complete implementation or create a POA&M item with remediation plan." if poam_eligible else "This control CANNOT be placed on POA&M. Must be fully implemented.",
                )
                result.gaps.append(gap)
                result.gaps_by_severity[severity].append(gap)

            if ev_info.total_artifacts == 0:
                gap = ControlGap(
                    control_id=cid, family=family, family_abbrev=family_abbrev,
                    title=title, points=points, gap_type="NO_EVIDENCE",
                    severity=severity, implementation_status=impl_status,
                    on_poam=on_poam, poam_eligible=poam_eligible,
                    evidence_info=ev_info,
                    description=f"No evidence artifacts mapped to {cid}. Assessors require documentary evidence.",
                    remediation_hint="Upload and link evidence files (policies, configs, screenshots, logs) for this control.",
                )
                result.gaps.append(gap)
                result.gaps_by_severity[severity].append(gap)

            elif not has_published_evidence:
                gap = ControlGap(
                    control_id=cid, family=family, family_abbrev=family_abbrev,
                    title=title, points=points, gap_type="PARTIAL_EVIDENCE",
                    severity=severity, implementation_status=impl_status,
                    on_poam=on_poam, poam_eligible=poam_eligible,
                    evidence_info=ev_info,
                    description=f"{cid} has {ev_info.total_artifacts} evidence artifact(s) but none are PUBLISHED. "
                                f"States: {ev_info.draft}D/{ev_info.reviewed}R/{ev_info.approved}A.",
                    remediation_hint="Review and approve existing evidence, then publish to lock hashes.",
                )
                result.gaps.append(gap)
                result.gaps_by_severity[severity].append(gap)

        # Aggregation
        result.ssp_completion_pct = round(
            result.controls_with_ssp / result.total_controls * 100, 1
        ) if result.total_controls > 0 else 0.0

        result.evidence_coverage_pct = round(
            result.controls_with_evidence / result.total_controls * 100, 1
        ) if result.total_controls > 0 else 0.0

        for gap in result.gaps:
            result.gaps_by_type.setdefault(gap.gap_type, []).append(gap)

        return result

    def get_summary(self) -> dict:
        r = self.assess()
        return {
            "org_id": r.org_id,
            "assessed_at": r.assessed_at,
            "total_controls": r.total_controls,
            "ssp_completion": {
                "with_ssp": r.controls_with_ssp,
                "without_ssp": r.controls_without_ssp,
                "pct": r.ssp_completion_pct,
            },
            "evidence_coverage": {
                "with_evidence": r.controls_with_evidence,
                "without_evidence": r.controls_without_evidence,
                "pct": r.evidence_coverage_pct,
            },
            "fully_compliant": r.controls_fully_compliant,
            "total_gaps": len(r.gaps),
            "gaps_by_severity": {
                sev: len(gaps) for sev, gaps in r.gaps_by_severity.items()
            },
            "gaps_by_type": {
                gtype: len(gaps) for gtype, gaps in r.gaps_by_type.items()
            },
            "gap_details": [
                {
                    "control_id": g.control_id,
                    "family": g.family_abbrev,
                    "title": g.title,
                    "points": g.points,
                    "gap_type": g.gap_type,
                    "severity": g.severity,
                    "description": g.description,
                    "remediation": g.remediation_hint,
                    "on_poam": g.on_poam,
                }
                for g in r.gaps
            ],
        }


if __name__ == "__main__":
    org_id = sys.argv[1] if len(sys.argv) > 1 else "9de53b587b23450b87af"
    engine = GapAssessmentEngine(org_id=org_id)
    result = engine.assess()

    print(f"\n{'='*60}")
    print(f"  GAP ASSESSMENT — {result.org_id}")
    print(f"  Assessed: {result.assessed_at}")
    print(f"{'='*60}")
    print(f"  SSP Completion: {result.controls_with_ssp}/{result.total_controls} ({result.ssp_completion_pct}%)")
    print(f"  Evidence Coverage: {result.controls_with_evidence}/{result.total_controls} ({result.evidence_coverage_pct}%)")
    print(f"  Fully Compliant: {result.controls_fully_compliant}/{result.total_controls}")
    print(f"  Total Gaps: {len(result.gaps)}")

    for sev in ("CRITICAL", "HIGH", "MEDIUM"):
        gaps = result.gaps_by_severity.get(sev, [])
        if gaps:
            print(f"\n  {sev} ({len(gaps)}):")
            for g in gaps:
                print(f"    [{g.gap_type:20s}] {g.control_id} ({g.points}pt) — {g.description[:80]}")
    print()
