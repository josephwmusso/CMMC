"""CLI entry point for simulation runs.

Usage:
    python -m scripts.simulation.run --fixture meridian_aerospace [options]

3A.2a stages (deterministic): setup, intake, evidence, scans
3A.2b stages (LLM-dependent): ssp, claims, observations, resolutions,
                               freshness, assessment, exports
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.simulation.loader.fixture_loader import load_fixture, FixtureValidationError
from scripts.simulation.agents.api_client import ApiClient
from scripts.simulation.agents.assertions import AssertionRecorder, AssertionFailure
from scripts.simulation.agents.journey_setup import run_setup
from scripts.simulation.agents.journey_intake import run_intake
from scripts.simulation.agents.journey_evidence import run_evidence
from scripts.simulation.agents.journey_scans import run_scans

FIXTURE_BASE = ROOT / "scripts" / "simulation" / "fixtures"
SCHEMA_DIR = ROOT / "scripts" / "simulation" / "schema"
RUNS_DIR = ROOT / "scripts" / "simulation" / "runs"

ALL_STAGES = "setup,intake,evidence,scans,ssp,claims,observations,resolutions,freshness,assessment,exports,assert"

DEFAULT_SSP_CONTROLS = [
    "IA.L2-3.5.3", "SC.L2-3.13.11", "AC.L2-3.1.5", "SI.L2-3.14.1", "AC.L2-3.1.1",
]


def main():
    parser = argparse.ArgumentParser(description="Run simulation fixture against backend")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--backend-url", default="http://localhost:8001")
    parser.add_argument("--superadmin-email", default="admin@intranest.ai")
    parser.add_argument("--superadmin-password",
                        default=os.environ.get("SIM_SUPERADMIN_PASSWORD", "Intranest2026!"))
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--skip-setup", action="store_true")
    parser.add_argument("--reuse-org-id", default=None)
    parser.add_argument("--stages", default=ALL_STAGES)
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--verbose", action="store_true")
    # 3A.2b flags
    parser.add_argument("--ssp-controls", type=int, default=5)
    parser.add_argument("--ssp-control-ids", default=None, help="Comma-separated control IDs")
    parser.add_argument("--full", action="store_true", help="All 110 controls for SSP")
    parser.add_argument("--two-pass", action="store_true")
    parser.add_argument("--skip-detector", action="store_true")
    parser.add_argument("--detector-strict", action="store_true")
    parser.add_argument("--json-report", default=None, help="Write LayerResult JSON to this path")
    args = parser.parse_args()

    fixture_dir = FIXTURE_BASE / args.fixture
    if not fixture_dir.exists():
        print(f"ERROR: Fixture not found: {fixture_dir}", file=sys.stderr)
        sys.exit(2)

    try:
        fixture = load_fixture(fixture_dir, SCHEMA_DIR)
    except FixtureValidationError as e:
        print(f"FIXTURE VALIDATION FAILED:\n{e}", file=sys.stderr)
        sys.exit(2)

    stages = set(args.stages.split(","))
    run_name = args.run_name or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = RUNS_DIR / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    api = ApiClient(args.backend_url, run_dir, verbose=args.verbose)
    recorder = AssertionRecorder(fail_fast=args.fail_fast)

    # SSP control scope
    if args.ssp_control_ids:
        ssp_controls = args.ssp_control_ids.split(",")
    elif args.full:
        from scripts.simulation.loader.fixture_loader import _load_yaml
        schema = _load_yaml(SCHEMA_DIR / "intake_schema.yaml")
        all_cids = set()
        for q in schema:
            all_cids.update(q.get("controls", []))
        ssp_controls = sorted(all_cids)
    else:
        ssp_controls = DEFAULT_SSP_CONTROLS[:args.ssp_controls]

    t0 = time.monotonic()
    org_id = args.reuse_org_id or ""
    session_id = ""

    try:
        # ── 3A.2a stages ──
        if "setup" in stages and not args.skip_setup and not args.reuse_org_id:
            print("▸ Stage 1: Setup")
            org_info = run_setup(api, fixture, recorder,
                                args.superadmin_email, args.superadmin_password)
            org_id = org_info.get("org_id", "")
            session_id = org_info.get("session_id", "")
            print(f"  org_id={org_id}")
        elif args.reuse_org_id:
            org_id = args.reuse_org_id
            org_json = _find_org_json(args.reuse_org_id)
            if org_json and org_json.get("email"):
                # Login as the Meridian user so JWT carries the right org_id
                api.login(org_json["email"], "Meridian2026!Simulation")
                api.org_id = org_id
                session_id = org_json.get("session_id", "")
            else:
                api.login(args.superadmin_email, args.superadmin_password)
                api.org_id = org_id
            print(f"▸ Setup skipped, reusing org_id={org_id}")

        if "intake" in stages and not args.reuse_org_id:
            print("▸ Stage 2: Intake")
            if not session_id:
                r = api.post("/api/intake/sessions", json={})
                if r.ok:
                    session_id = r.json().get("session_id", "")
            run_intake(api, fixture, recorder, session_id)
            _print_stage("intake", recorder)

        if "evidence" in stages and not args.reuse_org_id:
            print("▸ Stage 3: Evidence")
            run_evidence(api, fixture, recorder)
            _print_stage("evidence", recorder)

        if "scans" in stages and not args.reuse_org_id:
            print("▸ Stage 4: Scans")
            run_scans(api, fixture, recorder, fixture_dir)
            _print_stage("scans", recorder)

        # ── 3A.2b stages ──
        if "ssp" in stages:
            print(f"▸ Stage 7: SSP Generation ({len(ssp_controls)} controls)")
            from scripts.simulation.agents.journey_ssp import run_ssp
            run_ssp(api, fixture, recorder, run_dir, ssp_controls,
                    skip_detector=args.skip_detector, detector_strict=args.detector_strict)
            _print_stage("ssp", recorder)

        if "claims" in stages:
            print("▸ Stage 8: Claim Extraction")
            from scripts.simulation.agents.journey_claims import run_claims
            run_claims(api, fixture, recorder, run_dir, ssp_controls,
                       skip_detector=args.skip_detector)
            _print_stage("claims", recorder)

        if "observations" in stages:
            print("▸ Stage 9: Observations")
            from scripts.simulation.agents.journey_observations import run_observations
            run_observations(api, fixture, recorder, ssp_controls)
            _print_stage("observations", recorder)

        if "resolutions" in stages:
            print("▸ Stage 10: Resolutions")
            from scripts.simulation.agents.journey_resolutions import run_resolutions
            run_resolutions(api, fixture, recorder, run_dir, ssp_controls,
                            skip_detector=args.skip_detector)
            _print_stage("resolutions", recorder)

        if "freshness" in stages:
            print("▸ Stage 11: Freshness")
            from scripts.simulation.agents.journey_freshness import run_freshness
            run_freshness(api, recorder)
            _print_stage("freshness", recorder)

        if "assessment" in stages:
            print("▸ Stage 12: Assessment Simulation")
            from scripts.simulation.agents.journey_assessment import run_assessment
            run_assessment(api, fixture, recorder, run_dir,
                           skip_detector=args.skip_detector)
            _print_stage("assessment", recorder)

        if "exports" in stages:
            print("▸ Stage 13: Exports")
            from scripts.simulation.agents.journey_exports import run_exports
            run_exports(api, fixture, recorder, run_dir)
            _print_stage("exports", recorder)

        if "assert" in stages:
            print("▸ Stage 14: Cross-cutting assertions")
            _run_cross_assertions(api, fixture, recorder)
            _print_stage("cross", recorder)

    except AssertionFailure as e:
        print(f"\nFAIL-FAST: {e}")
    except Exception as e:
        print(f"\nINFRA ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()

    duration = time.monotonic() - t0

    api.flush_log()
    recorder.flush(run_dir)

    summary = recorder.summary_text(run_dir, args.fixture, args.backend_url,
                                    org_id, duration)
    print(f"\n{summary}")
    (run_dir / "summary.txt").write_text(summary, encoding="utf-8")

    if args.json_report:
        from scripts.verification.result_schema import AssertionResult as AR, LayerResult, save_json
        assertions = [
            AR(name=r.name, status="PASS" if r.passed else "FAIL",
               message=r.detail or "")
            for r in recorder.results
        ]
        layer = LayerResult(
            layer_name="Pipeline Harness", layer_id="harness",
            total=len(assertions),
            passed=recorder.passed_count, failed=recorder.failed_count,
            warned=len(recorder.warnings()), skipped=0,
            duration_seconds=round(duration, 1),
            assertions=assertions,
            environment="render" if "render" in args.backend_url else "local",
            timestamp=datetime.now(timezone.utc).isoformat(),
            fixture_name=args.fixture,
        )
        save_json(layer, args.json_report)

    sys.exit(0 if recorder.all_passed else 1)


def _print_stage(name: str, recorder: AssertionRecorder):
    p, f = recorder.by_stage(f"{name}.")
    print(f"  {p} passed, {f} failed")


def _find_org_json(org_id: str) -> dict | None:
    """Search runs/ for an org.json matching the given org_id."""
    for run_path in sorted(RUNS_DIR.iterdir(), reverse=True) if RUNS_DIR.exists() else []:
        org_path = run_path / "org.json"
        if org_path.exists():
            try:
                data = json.loads(org_path.read_text(encoding="utf-8"))
                if data.get("org_id") == org_id:
                    return data
            except Exception:
                pass
    return None


def _run_cross_assertions(api: ApiClient, fixture: Fixture, recorder: AssertionRecorder):
    r = api.get("/api/scoring/sprs")
    if r.ok:
        sprs = r.json()
        score = sprs.get("score", 0)
        expected = fixture.expected_outputs.sprs_target
        if expected and expected.expected_range:
            lo, hi = expected.expected_range
            recorder.expect("cross.sprs.score_in_range",
                            lo <= score <= hi,
                            actual=score, expected=f"[{lo}, {hi}]")
        recorder.expect("cross.sprs.below_poam_threshold",
                        score < 88, actual=score, expected="< 88")

    for path, name in [("/api/scans/", "scans"), ("/api/claims", "claims")]:
        r = api.get(path)
        if r.ok:
            data = r.json()
            items = data if isinstance(data, list) else data.get("items", [])
            apex_leak = any("9de53b587b23450b87af" in json.dumps(item) for item in items[:20])
            recorder.expect(f"cross.org_isolation.{name}",
                            not apex_leak, actual=f"apex_leak={apex_leak}")


if __name__ == "__main__":
    main()
