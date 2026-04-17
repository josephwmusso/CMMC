"""
Demo smoke test: hit every major endpoint category to confirm the backend is responsive.
Run: python scripts/demo_smoke_test.py [--base-url URL]
"""
import argparse
import sys
import time
from datetime import datetime

import requests


def main():
    parser = argparse.ArgumentParser(description="Smoke test all major endpoint categories")
    parser.add_argument("--base-url", default="http://localhost:8001")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    passed = 0
    failed = 0
    results = []

    def check(name, method, path, auth_header=None, expected_status=200, json_body=None):
        nonlocal passed, failed
        headers = auth_header or {}
        try:
            if method == "GET":
                r = requests.get(f"{base}{path}", headers=headers, timeout=30)
            elif method == "POST":
                r = requests.post(f"{base}{path}", headers=headers, json=json_body, timeout=30)
            else:
                r = requests.request(method, f"{base}{path}", headers=headers, timeout=30)

            ok = r.status_code == expected_status or (expected_status == 200 and r.status_code < 300)
            if ok:
                print(f"  ✓ {name} → {r.status_code} ({r.elapsed.total_seconds():.1f}s)")
                passed += 1
                results.append((name, "PASS", r.status_code))
            else:
                print(f"  ✗ {name} → {r.status_code} (expected {expected_status})")
                failed += 1
                results.append((name, "FAIL", r.status_code))
        except requests.exceptions.Timeout:
            print(f"  ✗ {name} → TIMEOUT")
            failed += 1
            results.append((name, "TIMEOUT", 0))
        except Exception as e:
            print(f"  ✗ {name} → ERROR: {e}")
            failed += 1
            results.append((name, "ERROR", 0))

    # Health (no auth)
    print("Public endpoints:")
    check("Health", "GET", "/health")
    check("API Health", "GET", "/api/health")

    # Login
    print("\nAuthentication:")
    r = requests.post(f"{base}/api/auth/login",
                      data={"username": "admin@intranest.ai", "password": "Intranest2026!"},
                      headers={"Content-Type": "application/x-www-form-urlencoded"},
                      timeout=30)
    if r.status_code == 200:
        token = r.json()["access_token"]
        auth = {"Authorization": f"Bearer {token}"}
        print(f"  ✓ Login → 200")
        passed += 1
    else:
        print(f"  ✗ Login → {r.status_code}")
        print(f"    Cannot continue without auth.")
        failed += 1
        _summary(base, passed, failed)
        sys.exit(1)

    check("GET /me", "GET", "/api/auth/me", auth)

    # Core platform
    print("\nScoring & Compliance:")
    check("SPRS Score", "GET", "/api/scoring/sprs", auth)
    check("Scoring Overview", "GET", "/api/scoring/overview", auth)

    print("\nIntake:")
    check("Intake Modules", "GET", "/api/intake/modules", auth)
    check("Intake Sessions", "GET", "/api/intake/sessions/none", auth, expected_status=404)

    print("\nEvidence:")
    check("Evidence List", "GET", "/api/evidence", auth)

    print("\nScans:")
    check("Scan List", "GET", "/api/scans/", auth)
    check("Scan Summary", "GET", "/api/scans/summary", auth)

    print("\nBaselines:")
    check("Baseline Catalog", "GET", "/api/baselines", auth)
    check("Baseline Summary", "GET", "/api/baselines/summary", auth)

    print("\nContradictions:")
    check("Contradiction Summary", "GET", "/api/contradictions/summary", auth)

    print("\nTruth Model:")
    check("Claims List", "GET", "/api/claims", auth)
    check("Claims Summary", "GET", "/api/claims/summary", auth)
    check("Observations Summary", "GET", "/api/observations/summary", auth)
    check("Resolutions Summary", "GET", "/api/resolutions/summary", auth)
    check("Freshness Summary", "GET", "/api/freshness/summary", auth)

    print("\nAssessment:")
    check("Assessment Latest", "GET", "/api/assessments/latest", auth)
    check("Assessment At-Risk", "GET", "/api/assessments/at-risk", auth)

    print("\nExports:")
    check("Export Preview", "GET", "/api/exports/preview", auth)
    check("Export History", "GET", "/api/exports/history", auth)
    check("SPRS Preview", "GET", "/api/exports/sprs-preview", auth)

    print("\nAffirmations:")
    check("Affirmation Status", "GET", "/api/affirmations/status", auth)

    print("\nGrounding (Truth):")
    check("Grounding AC.L2-3.1.1", "GET", "/api/truth/grounding-context/AC.L2-3.1.1", auth)

    print("\nAdmin:")
    check("Admin Users", "GET", "/api/admin/users", auth)
    check("Admin Orgs", "GET", "/api/admin/organizations", auth)
    check("Admin Invites", "GET", "/api/admin/invites", auth)

    print("\nOnboarding:")
    check("Onboarding Status", "GET", "/api/onboarding/status", auth)

    _summary(base, passed, failed)
    sys.exit(0 if failed == 0 else 1)


def _summary(base, passed, failed):
    total = passed + failed
    status = "PASS" if failed == 0 else "FAIL"
    print(f"\n{'═'*50}")
    print(f"  DEMO SMOKE TEST — {status}")
    print(f"  {datetime.now().isoformat()}")
    print(f"  Backend: {base}")
    print(f"  Endpoints: {passed}/{total} responding")
    if failed:
        print(f"  Failed: {failed}")
    print(f"{'═'*50}")


if __name__ == "__main__":
    main()
