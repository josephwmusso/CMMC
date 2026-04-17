"""Run all verification layers and generate HTML report.

Usage:
    python scripts/run_full_verification.py [--env local|render] [--output path]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports" / "latest"


def run_script(cmd: list[str], label: str) -> int:
    print(f"\n{'─'*50}")
    print(f"▸ {label}")
    print(f"{'─'*50}")
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        print(f"  ⚠ {label} exited with code {result.returncode}")
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run full verification suite")
    parser.add_argument("--env", default="local", choices=["local", "render"])
    parser.add_argument("--fixture", default="meridian_aerospace")
    parser.add_argument("--playwright-status", default="SKIP", choices=["PASS", "FAIL", "SKIP"])
    parser.add_argument("--output", default="reports/verification_report.html")
    parser.add_argument("--skip-harness", action="store_true")
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--reuse-org-id", default=None)
    args = parser.parse_args()

    base_url = "https://cmmc.onrender.com" if args.env == "render" else "http://localhost:8001"
    frontend_url = "https://intranest.ai" if args.env == "render" else "http://localhost:5173"
    py = sys.executable

    # Clean results dir
    if REPORTS_DIR.exists():
        shutil.rmtree(REPORTS_DIR)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    codes = {}

    # 1. Database state check
    codes["dbcheck"] = run_script([
        py, "scripts/pre_demo_cleanup.py",
        "--base-url", base_url,
        "--json-report", str(REPORTS_DIR / "dbcheck.json"),
    ], "Database State Check")

    # 2. Onboarding flow
    codes["onboarding"] = run_script([
        py, "scripts/test_onboarding_flow.py",
        "--base-url", base_url,
        "--frontend-url", frontend_url,
        "--json-report", str(REPORTS_DIR / "onboarding.json"),
    ], "Onboarding API")

    # 3. Endpoint smoke test
    if not args.skip_smoke:
        codes["smoke"] = run_script([
            py, "scripts/demo_smoke_test.py",
            "--base-url", base_url,
            "--json-report", str(REPORTS_DIR / "smoke.json"),
        ], "Endpoint Smoke Test")

    # 4. Pipeline harness
    if not args.skip_harness:
        harness_cmd = [
            py, "-m", "scripts.simulation.run",
            "--fixture", args.fixture,
            "--backend-url", base_url,
            "--json-report", str(REPORTS_DIR / "harness.json"),
        ]
        if args.reuse_org_id:
            harness_cmd += ["--reuse-org-id", args.reuse_org_id,
                            "--stages", "ssp,claims,observations,resolutions,freshness,assessment,exports"]
        codes["harness"] = run_script(harness_cmd, "Pipeline Harness")

    # Generate HTML report
    print(f"\n{'─'*50}")
    print(f"▸ Generating HTML Report")
    print(f"{'─'*50}")
    gen_cmd = [
        py, "scripts/generate_verification_report.py",
        "--results-dir", str(REPORTS_DIR),
        "--output", args.output,
        "--audit-file", "docs/DATA_INTEGRITY_AUDIT.md",
        "--playwright-status", args.playwright_status,
    ]
    subprocess.run(gen_cmd, cwd=str(ROOT))

    output_path = ROOT / args.output
    if output_path.exists():
        print(f"\n{'═'*50}")
        print(f"  Report: {output_path}")
        print(f"  Opening in browser...")
        print(f"{'═'*50}")
        webbrowser.open(output_path.as_uri())
    else:
        print(f"\n⚠ Report not generated at {output_path}")

    any_fail = any(c != 0 for c in codes.values())
    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    main()
