"""Stage 1: Invite → Redeem → Onboarding."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone

from scripts.simulation.agents.api_client import ApiClient
from scripts.simulation.agents.assertions import AssertionRecorder
from scripts.simulation.loader.schemas import Fixture


def run_setup(api: ApiClient, fixture: Fixture, recorder: AssertionRecorder,
              superadmin_email: str, superadmin_password: str) -> dict:
    """Returns {org_id, user_id, email, session_id} for downstream stages."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    meridian_email = f"meridian-{ts}@mailinator.example"
    cp = fixture.company_profile

    # ── 1. SUPERADMIN login ──
    api.login(superadmin_email, superadmin_password)

    # ── 2. Create invite ──
    r = api.post("/api/invites/new-customer", json={
        "email": meridian_email,
        "full_name": "Meridian Owner",
        "org_name": cp.company_name,
    })
    recorder.expect("setup.invite_created", r.status_code == 200,
                    actual=r.status_code, detail=r.text[:300] if r.status_code != 200 else "")
    invite_data = r.json() if r.ok else {}
    invite_code = invite_data.get("invite_code", "")
    invite_url = invite_data.get("invite_url", "")
    recorder.expect("setup.invite_has_url", bool(invite_url), actual=invite_url)

    # ── 3. Clear SUPERADMIN session, go public ──
    api.clear_auth()

    # ── 4. Fetch invite (public) ──
    r = api.get(f"/api/invites/new-customer/{invite_code}")
    recorder.expect("setup.invite_fetch_ok", r.status_code == 200, actual=r.status_code)
    if r.ok:
        inv = r.json()
        recorder.expect("setup.invite_org_name_matches",
                        inv.get("org_name") == cp.company_name,
                        actual=inv.get("org_name"), expected=cp.company_name)

    # ── 5. Redeem ──
    r = api.post(f"/api/invites/new-customer/{invite_code}/redeem", json={
        "password": "Meridian2026!Simulation",
        "full_name": "Meridian Owner",
    })
    recorder.expect("setup.redeem_success", r.status_code == 200,
                    actual=r.status_code, detail=r.text[:300] if r.status_code != 200 else "")
    redeem = r.json() if r.ok else {}
    org_id = redeem.get("org", {}).get("id", "")
    user_id = redeem.get("user", {}).get("id", "")
    access = redeem.get("access_token", "")
    refresh = redeem.get("refresh_token", "")

    api.set_tokens(access, refresh, org_id=org_id, user_id=user_id)

    # ── 6. Onboarding ──
    # Map fixture company_profile → onboarding payload
    mfa_raw = (cp.identity_provider or "").lower()
    mfa_enabled = "mfa" in mfa_raw or "2-step" in mfa_raw or "2sv" in mfa_raw

    onboarding_payload = {
        "organization": {
            "name": cp.company_name,
            "city": cp.primary_location.split(",")[0].strip() if cp.primary_location else "",
            "state": cp.primary_location.split(",")[-1].strip() if "," in (cp.primary_location or "") else "",
            "employee_count": cp.employee_count,
            "system_name": cp.system_name or "CUI Network",
        },
        "tech_stack": {
            "identity_provider": cp.identity_provider or "",
            "mfa_enabled": mfa_enabled,
            "email_platform": cp.email_platform or "",
            "edr_tool": cp.edr_product or "",
            "firewall": cp.firewall_product or "",
            "siem": cp.siem_product or "",
            "backup_tool": cp.backup_solution or "",
            "training_tool": cp.training_tool or "",
        },
        "cui_types": cp.cui_types or [],
    }

    r = api.post("/api/onboarding/complete", json=onboarding_payload)
    recorder.expect("setup.onboarding_complete", r.status_code == 200,
                    actual=r.status_code, detail=r.text[:300] if r.status_code != 200 else "")
    ob = r.json() if r.ok else {}
    recorder.expect("setup.onboarding_flag_true",
                    ob.get("onboarding_complete") is True,
                    actual=ob.get("onboarding_complete"))

    session_id = ob.get("session_id", "")

    # ── 7. Verify Module 0 pre-seed ──
    if session_id:
        r = api.get(f"/api/intake/sessions/{session_id}/module/0")
        if r.ok:
            questions = r.json().get("questions", [])
            preseeded = [q for q in questions if q.get("current_value")]
            m0_ids = {"m0_identity_provider", "m0_email_platform", "m0_edr", "m0_firewall"}
            found = {q["id"] for q in preseeded if q["id"] in m0_ids}
            recorder.expect("setup.module0_preseeded",
                            len(found) >= 4,
                            actual=sorted(found), expected=sorted(m0_ids))

    # ── 8. Check no forbidden tool in profile ──
    forbidden_tools_lower = {t.lower() for t in (fixture.forbidden.forbidden_tools or [])}
    profile_tools = [cp.identity_provider, cp.email_platform, cp.edr_product,
                     cp.firewall_product, cp.siem_product, cp.backup_solution, cp.training_tool]
    leaked = [t for t in profile_tools if t and t.lower() in forbidden_tools_lower]
    recorder.expect("setup.forbidden_tool_not_in_company_profile",
                    len(leaked) == 0, actual=leaked)

    # Save org info for reuse
    org_info = {
        "org_id": org_id, "user_id": user_id,
        "email": meridian_email, "session_id": session_id,
        "fixture": "meridian_aerospace",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    org_path = api.run_dir / "org.json"
    org_path.parent.mkdir(parents=True, exist_ok=True)
    with open(org_path, "w") as f:
        json.dump(org_info, f, indent=2)

    return org_info
