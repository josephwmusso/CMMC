"""
Pre-demo cleanup: verify no stale test data exists that could interfere with a live demo.
Run: python scripts/pre_demo_cleanup.py [--base-url URL]
"""
import argparse
import sys
from datetime import datetime

import requests


def main():
    parser = argparse.ArgumentParser(description="Pre-demo cleanup check")
    parser.add_argument("--base-url", default="http://localhost:8001")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    issues = []
    checks = 0

    # Login as admin
    r = requests.post(f"{base}/api/auth/login",
                      data={"username": "admin@intranest.ai", "password": "Intranest2026!"},
                      headers={"Content-Type": "application/x-www-form-urlencoded"})
    if r.status_code != 200:
        print(f"✗ Admin login failed: {r.status_code}")
        sys.exit(1)
    token = r.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    # Check 1: No stale test users
    checks += 1
    r = requests.get(f"{base}/api/admin/users", headers=auth)
    if r.ok:
        users = r.json()
        test_users = [u for u in users if "test" in u.get("email", "").lower()
                      or "demo" in u.get("email", "").lower()
                      or "mailinator" in u.get("email", "").lower()
                      or "example" in u.get("email", "").lower()]
        if test_users:
            issues.append(f"Stale test users found: {[u['email'] for u in test_users]}")
            print(f"⚠ Check 1: {len(test_users)} stale test user(s) found")
        else:
            print(f"✓ Check 1: No stale test users")
    else:
        print(f"⚠ Check 1: Could not check users ({r.status_code})")

    # Check 2: No stale test orgs
    checks += 1
    r = requests.get(f"{base}/api/admin/organizations", headers=auth)
    if r.ok and r.text.strip().startswith("["):
        try:
            orgs = r.json()
        except Exception:
            orgs = []
        test_orgs = [o for o in orgs if any(kw in o.get("name", "").lower()
                     for kw in ["test", "demo test", "meridian-", "fixture"])]
        # Apex is expected
        non_apex = [o for o in orgs if o.get("id") != "9de53b587b23450b87af"]
        if test_orgs:
            issues.append(f"Stale test orgs: {[o['name'] for o in test_orgs]}")
            print(f"⚠ Check 2: {len(test_orgs)} stale test org(s) found")
        else:
            print(f"✓ Check 2: No stale test orgs")
    else:
        print(f"⚠ Check 2: Could not check orgs ({r.status_code})")

    # Check 3: Apex company_profiles exists
    checks += 1
    r = requests.get(f"{base}/api/intake/company-profile/9de53b587b23450b87af", headers=auth)
    cp_ok = False
    if r.ok:
        try:
            cp_ok = r.json().get("company_name") == "Apex Defense Solutions"
        except Exception:
            pass
    if cp_ok:
        print(f"✓ Check 3: Apex company_profile present and complete")
    else:
        issues.append("Apex company_profile missing or incomplete")
        print(f"⚠ Check 3: Apex company_profile issue")

    # Check 4: No expired/unredeemed invites cluttering the list
    checks += 1
    r = requests.get(f"{base}/api/admin/invites", headers=auth)
    if r.ok and r.text.strip().startswith("["):
        try:
            invites = r.json()
        except Exception:
            invites = []
        stale = [i for i in invites if i.get("used_at") is None
                 and i.get("invite_type") == "NEW_CUSTOMER"]
        if stale:
            issues.append(f"{len(stale)} unredeemed NEW_CUSTOMER invite(s)")
            print(f"⚠ Check 4: {len(stale)} unredeemed invite(s)")
        else:
            print(f"✓ Check 4: No stale invites")
    else:
        print(f"⚠ Check 4: Could not check invites ({r.status_code})")

    # Check 5: Health endpoint
    checks += 1
    r = requests.get(f"{base}/health")
    if r.ok and r.json().get("status") == "ok":
        print(f"✓ Check 5: Backend healthy")
    else:
        issues.append("Backend unhealthy")
        print(f"✗ Check 5: Backend NOT healthy")

    # Summary
    status = "CLEAN" if not issues else "ISSUES FOUND"
    print(f"\n{'═'*50}")
    print(f"  PRE-DEMO CLEANUP — {status}")
    print(f"  {datetime.now().isoformat()}")
    print(f"  Backend: {base}")
    print(f"  Checks: {checks - len(issues)}/{checks} clean")
    if issues:
        print(f"\n  Issues to resolve:")
        for i in issues:
            print(f"    • {i}")
    print(f"{'═'*50}")
    sys.exit(0 if not issues else 1)


if __name__ == "__main__":
    main()
