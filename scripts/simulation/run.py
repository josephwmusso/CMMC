"""CLI entry point for simulation runs.

Usage:
    python -m scripts.simulation.run --fixture meridian_aerospace [options]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root on path
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


def main():
    parser = argparse.ArgumentParser(description="Run simulation fixture against backend")
    parser.add_argument("--fixture", required=True, help="Fixture subdirectory name")
    parser.add_argument("--backend-url", default="http://localhost:8001")
    parser.add_argument("--superadmin-email", default="admin@intranest.ai")
    parser.add_argument("--superadmin-password",
                        default=os.environ.get("SIM_SUPERADMIN_PASSWORD", "Intranest2026!"))
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--skip-setup", action="store_true")
    parser.add_argument("--reuse-org-id", default=None)
    parser.add_argument("--stages", default="setup,intake,evidence,scans,assert",
                        help="Comma-separated: setup,intake,evidence,scans,assert")
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    fixture_dir = FIXTURE_BASE / args.fixture
    if not fixture_dir.exists():
        print(f"ERROR: Fixture directory not found: {fixture_dir}", file=sys.stderr)
        sys.exit(2)

    # ── Load fixture ──
    try:
        fixture = load_fixture(fixture_dir, SCHEMA_DIR)
    except FixtureValidationError as e:
        print(f"FIXTURE VALIDATION FAILED:\n{e}", file=sys.stderr)
        sys.exit(2)

    stages = set(args.stages.split(","))

    # ── Run directory ──
    run_name = args.run_name or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = RUNS_DIR / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    api = ApiClient(args.backend_url, run_dir, verbose=args.verbose)
    recorder = AssertionRecorder(fail_fast=args.fail_fast)

    t0 = time.monotonic()
    org_id = args.reuse_org_id or ""
    session_id = ""

    try:
        # ── Stage 1: Setup ──
        if "setup" in stages and not args.skip_setup:
            print("▸ Stage 1: Setup")
            org_info = run_setup(api, fixture, recorder,
                                args.superadmin_email, args.superadmin_password)
            org_id = org_info.get("org_id", "")
            session_id = org_info.get("session_id", "")
            print(f"  org_id={org_id}")
        elif args.reuse_org_id:
            # Load org info from a prior run
            org_id = args.reuse_org_id
            # Need to login as the reuse org's user — for now login as superadmin
            api.login(args.superadmin_email, args.superadmin_password)
            print(f"▸ Setup skipped, reusing org_id={org_id}")

        # ── Stage 2: Intake ──
        if "intake" in stages:
            print("▸ Stage 2: Intake")
            if not session_id:
                # Create a new session
                r = api.post("/api/intake/sessions", json={})
                if r.ok:
                    session_id = r.json().get("session_id", "")
            run_intake(api, fixture, recorder, session_id)
            p, f = recorder.by_stage("intake")
            print(f"  {p} passed, {f} failed")

        # ── Stage 3: Evidence ──
        if "evidence" in stages:
            print("▸ Stage 3: Evidence")
            run_evidence(api, fixture, recorder)
            p, f = recorder.by_stage("evidence")
            print(f"  {p} passed, {f} failed")

        # ── Stage 4: Scans ──
        if "scans" in stages:
            print("▸ Stage 4: Scans")
            run_scans(api, fixture, recorder, fixture_dir)
            p, f = recorder.by_stage("scans")
            print(f"  {p} passed, {f} failed")

        # ── Stage 5: Cross-cutting assertions ──
        if "assert" in stages:
            print("▸ Stage 5: Cross-cutting assertions")
            _run_cross_assertions(api, fixture, recorder)
            p, f = recorder.by_stage("cross")
            print(f"  {p} passed, {f} failed")

    except AssertionFailure as e:
        print(f"\nFAIL-FAST: {e}")
    except Exception as e:
        print(f"\nINFRA ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()

    duration = time.monotonic() - t0

    # ── Output ──
    api.flush_log()
    recorder.flush(run_dir)

    summary = recorder.summary_text(run_dir, args.fixture, args.backend_url,
                                    org_id, duration)
    print(f"\n{summary}")
    (run_dir / "summary.txt").write_text(summary, encoding="utf-8")

    if recorder.failed_count > 0:
        sys.exit(1)
    sys.exit(0)


def _run_cross_assertions(api: ApiClient, fixture: Fixture, recorder: AssertionRecorder):
    """Post-stage aggregate assertions."""
    # SPRS score
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
                        score < 88,
                        actual=score, expected="< 88",
                        detail="Meridian should not be POA&M-eligible")

    # Org isolation spot check
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
