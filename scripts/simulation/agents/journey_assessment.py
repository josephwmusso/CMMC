"""Stage 12: Assessment simulation — LLM-generated assessor findings."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.simulation.agents.api_client import ApiClient
from scripts.simulation.agents.assertions import AssertionRecorder
from scripts.simulation.agents.journey_ssp import _build_forbidden_dict
from scripts.simulation.loader.schemas import Fixture


def run_assessment(
    api: ApiClient, fixture: Fixture, recorder: AssertionRecorder,
    run_dir: Path, skip_detector: bool = False,
) -> dict:
    det_dir = run_dir / "detector" / "assessment"
    det_dir.mkdir(parents=True, exist_ok=True)

    r = api.post("/api/assessments/simulate")
    recorder.expect("assessment.simulation_succeeded", r.ok,
                    actual=r.status_code if r else 0,
                    detail=r.text[:300] if r and not r.ok else "")
    if not r.ok:
        return {}

    snap = r.json()

    # Readiness
    readiness = snap.get("readiness_pct", 0)
    expected = fixture.expected_outputs
    if expected and expected.readiness_pct_target:
        rng = expected.readiness_pct_target.get("expected_range", [0, 100])
        if len(rng) == 2:
            recorder.expect("assessment.readiness_pct_in_range",
                            rng[0] <= readiness <= rng[1],
                            actual=readiness, expected=f"[{rng[0]}, {rng[1]}]")

    # SPRS
    sprs_actual = snap.get("sprs_actual", 0)
    sprs_adjusted = snap.get("sprs_truth_adjusted", 0)
    if expected and expected.sprs_target:
        lo, hi = expected.sprs_target.expected_range
        recorder.expect("assessment.sprs_actual_in_range",
                        lo <= sprs_actual <= hi,
                        actual=sprs_actual, expected=f"[{lo}, {hi}]")
    recorder.expect("assessment.sprs_truth_adjusted_lte_actual",
                    sprs_adjusted <= sprs_actual,
                    actual=f"adjusted={sprs_adjusted}, actual={sprs_actual}")

    # At-risk controls
    failures = snap.get("likely_failures", [])
    at_risk_cids = {f.get("control_id") for f in failures}
    if expected and expected.at_risk_top_10:
        must_include = expected.at_risk_top_10.get("must_include", [])
        for cid in must_include:
            recorder.expect(f"assessment.at_risk_includes.{cid}",
                            cid in at_risk_cids,
                            actual=sorted(at_risk_cids))

    # Detector on findings
    total_violations = 0
    if not skip_detector:
        forbidden = _build_forbidden_dict(fixture)
        for i, finding in enumerate(failures):
            finding_text = finding.get("finding", "")
            if not finding_text or len(finding_text) < 20:
                continue

            recorder.expect(f"assessment.finding_{i}.length",
                            len(finding_text) >= 100,
                            actual=len(finding_text), expected=">=100 chars")

            cid = finding.get("control_id", "")
            gr = api.get(f"/api/truth/grounding-context/{cid}")
            grounding = gr.json().get("grounding_universe", {}) if gr.ok else {}

            from scripts.simulation.detectors.hallucination_detector import detect
            report = detect(
                text=finding_text,
                artifact_id=f"assessor_finding_{i}",
                artifact_type="assessor_finding",
                control_ids=[cid],
                grounding_universe=grounding,
                forbidden=forbidden,
            )

            violations = [h for h in report.hits if h.severity == "violation"]
            total_violations += len(violations)

            with open(det_dir / f"finding_{i}.json", "w") as f:
                json.dump({"control_id": cid, "severity": report.severity,
                           "hits": [{"category": h.category, "entity": h.entity,
                                     "reason": h.reason} for h in report.hits]}, f, indent=2)

    recorder.expect("assessment.findings_clean", total_violations == 0,
                    actual=total_violations)

    return snap
