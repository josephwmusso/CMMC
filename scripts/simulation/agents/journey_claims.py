"""Stage 8: Claim extraction + per-claim hallucination detection."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.simulation.agents.api_client import ApiClient
from scripts.simulation.agents.assertions import AssertionRecorder
from scripts.simulation.agents.journey_ssp import _build_forbidden_dict
from scripts.simulation.loader.schemas import Fixture


def run_claims(
    api: ApiClient, fixture: Fixture, recorder: AssertionRecorder,
    run_dir: Path, control_ids: list[str],
    skip_detector: bool = False,
) -> dict:
    det_dir = run_dir / "detector" / "claims"
    det_dir.mkdir(parents=True, exist_ok=True)

    total_claims = 0
    total_violations = 0
    types_seen: set[str] = set()

    for cid in control_ids:
        r = api.post(f"/api/claims/extract/{cid}")
        if not r.ok:
            recorder.expect(f"claims.extract.{cid}", False,
                            detail=f"{r.status_code} {r.text[:200]}")
            continue

        data = r.json()
        claims = data.get("claims", [])
        recorder.expect(f"claims.extracted.{cid}",
                        len(claims) >= 1,
                        actual=len(claims), expected=">=1")
        total_claims += len(claims)

        for cl in claims:
            types_seen.add(cl.get("claim_type", ""))

            if skip_detector:
                continue

            gr = api.get(f"/api/truth/grounding-context/{cid}")
            grounding = gr.json().get("grounding_universe", {}) if gr.ok else {}
            forbidden = _build_forbidden_dict(fixture)

            from scripts.simulation.detectors.hallucination_detector import detect
            report = detect(
                text=cl.get("claim_text", ""),
                artifact_id=f"claim_{cl.get('id', 'unknown')}",
                artifact_type="claim_text",
                control_ids=[cid],
                grounding_universe=grounding,
                forbidden=forbidden,
            )

            violations = [h for h in report.hits if h.severity == "violation"]
            total_violations += len(violations)

            if violations:
                with open(det_dir / f"{cl.get('id', 'unknown')}.json", "w") as f:
                    json.dump({"severity": report.severity,
                               "hits": [{"category": h.category, "entity": h.entity,
                                         "reason": h.reason} for h in violations]}, f, indent=2)

    recorder.expect("claims.all_grounded", total_violations == 0,
                    actual=total_violations)

    has_all_types = len(types_seen & {"POLICY", "TECHNICAL", "OPERATIONAL"}) >= 2
    if not has_all_types:
        recorder.warn("claims.types_present",
                      detail=f"Types seen: {types_seen}; expected POLICY+TECHNICAL+OPERATIONAL",
                      actual=sorted(types_seen))

    return {"total_claims": total_claims, "violations": total_violations}
