"""Stage 9: Observation building (deterministic, no LLM)."""
from __future__ import annotations

from scripts.simulation.agents.api_client import ApiClient
from scripts.simulation.agents.assertions import AssertionRecorder
from scripts.simulation.loader.schemas import Fixture


def run_observations(api: ApiClient, fixture: Fixture, recorder: AssertionRecorder,
                     control_ids: list[str]) -> dict:
    r = api.post("/api/observations/build")
    recorder.expect("observations.build_succeeded", r.ok,
                    actual=r.status_code if r else 0)
    if not r.ok:
        return {}

    data = r.json()
    by_source = data.get("by_source_type", {})

    recorder.expect("observations.scan_findings_present",
                    by_source.get("SCAN_FINDING", 0) >= 1,
                    actual=by_source.get("SCAN_FINDING", 0))
    recorder.expect("observations.evidence_artifacts_present",
                    by_source.get("EVIDENCE_ARTIFACT", 0) >= 1,
                    actual=by_source.get("EVIDENCE_ARTIFACT", 0))
    recorder.expect("observations.baseline_deviations_present",
                    by_source.get("BASELINE_DEVIATION", 0) >= 1,
                    actual=by_source.get("BASELINE_DEVIATION", 0))

    # Per contradiction-seed control: check for observations.
    # Controls with detection_layer=resolution_engine may have NO observations
    # (evidence-gap contradictions are detected by absence, not presence).
    resolution_controls = set()
    for c in fixture.contradictions:
        if getattr(c, "detection_layer", None) == "resolution_engine":
            resolution_controls.update(c.affected_controls)

    for cid in control_ids[:4]:
        cr = api.get(f"/api/observations/by-control/{cid}")
        count = cr.json().get("count", 0) if cr.ok else 0
        if cid in resolution_controls and count == 0:
            recorder.warn(f"observations.{cid}_evidence_gap_expected",
                          detail=f"{cid} has detection_layer=resolution_engine; no observations is expected",
                          actual=count)
        else:
            recorder.expect(f"observations.{cid}_has_observations",
                            count >= 1, actual=count)

    return data
