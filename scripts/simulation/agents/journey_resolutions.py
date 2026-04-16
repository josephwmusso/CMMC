"""Stage 10: Resolution engine — match claims against observations."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.simulation.agents.api_client import ApiClient
from scripts.simulation.agents.assertions import AssertionRecorder
from scripts.simulation.agents.journey_ssp import _build_forbidden_dict
from scripts.simulation.loader.schemas import Fixture


def run_resolutions(
    api: ApiClient, fixture: Fixture, recorder: AssertionRecorder,
    run_dir: Path, control_ids: list[str],
    skip_detector: bool = False,
) -> dict:
    det_dir = run_dir / "detector" / "resolutions"
    det_dir.mkdir(parents=True, exist_ok=True)

    total_resolved = 0
    for cid in control_ids:
        r = api.post(f"/api/resolutions/resolve/{cid}")
        if r.ok:
            data = r.json()
            total_resolved += data.get("claims_resolved", data.get("resolved_claims", 0))
        else:
            recorder.expect(f"resolutions.{cid}.resolved", False,
                            detail=f"{r.status_code} {r.text[:200]}")

    recorder.expect("resolutions.per_control_complete",
                    total_resolved >= len(control_ids),
                    actual=total_resolved, expected=f">={len(control_ids)}")

    # Check conflicts
    cr = api.get("/api/resolutions/conflicts")
    conflicts = cr.json() if cr.ok else {}
    conflict_items = conflicts.get("items", [])
    conflict_count = conflicts.get("count", len(conflict_items))

    recorder.expect("resolutions.conflicts_present",
                    conflict_count >= 1,
                    actual=conflict_count, expected=">=1")

    # Check fixture-required conflicts
    expected = fixture.expected_outputs
    if expected and expected.resolution_conflicts_must_catch:
        must = expected.resolution_conflicts_must_catch
        conflict_controls = {c.get("control_id") for c in conflict_items}
        for req in must.required:
            if isinstance(req, dict):
                ctrl = req.get("claim_control", "")
                cid_label = req.get("contradiction_id", ctrl)
            else:
                ctrl = str(req)
                cid_label = ctrl
            recorder.expect(f"resolutions.conflicts_match_fixture.{cid_label}",
                            ctrl in conflict_controls,
                            actual=sorted(conflict_controls), expected=ctrl)

    # Detector on conflict reasoning
    total_violations = 0
    if not skip_detector:
        forbidden = _build_forbidden_dict(fixture)
        for item in conflict_items:
            for contra in item.get("contradictions", []):
                reasoning = contra.get("reasoning", "")
                if not reasoning:
                    continue
                from scripts.simulation.detectors.hallucination_detector import detect
                cid = item.get("control_id", "")
                gr = api.get(f"/api/truth/grounding-context/{cid}")
                grounding = gr.json().get("grounding_universe", {}) if gr.ok else {}
                report = detect(
                    text=reasoning,
                    artifact_id=f"resolution_{contra.get('resolution_id', '')}",
                    artifact_type="resolution_reasoning",
                    control_ids=[cid],
                    grounding_universe=grounding,
                    forbidden=forbidden,
                )
                violations = [h for h in report.hits if h.severity == "violation"]
                total_violations += len(violations)

    recorder.expect("resolutions.reasoning_clean", total_violations == 0,
                    actual=total_violations)

    return {"total_resolved": total_resolved, "conflicts": conflict_count}
