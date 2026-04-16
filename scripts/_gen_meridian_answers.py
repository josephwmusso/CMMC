"""Generate intake_answers.yaml for Meridian Aerospace fixture."""
import yaml, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ANSWERS = {
    # Module 0 — must match company.yaml / evidence/*.md / forbidden.yaml persona
    "m0_company_name": "Meridian Aerospace Components, LLC",
    "m0_cage_code": "9MZ47",
    "m0_employee_count": "14",
    "m0_locations": "1",
    "m0_primary_location": "Wichita, KS",
    "m0_dfars_clause": "yes",
    "m0_cui_types": "Controlled Technical Information (CTI),Technical data (drawings, specs, test results)",
    "m0_cui_flow": "CUI is on individual laptops/desktops",
    "m0_remote_workers": "no",
    "m0_wireless": "yes",
    "m0_email_platform": "Google Workspace",
    "m0_identity_provider": "Google Identity",
    "m0_edr": "Traditional antivirus only (e.g., Norton, McAfee)",
    "m0_firewall": "SonicWall",
    "m0_siem": "No log collection",
    "m0_training_tool": "Other",
    "m0_existing_docs": "Incident Response Plan,Network Diagram",
    # Module 1 — Access Control (14-person shop, no remote workers, basic controls)
    "m1_q01": "manager_email",         # informal provisioning via owner email
    "m1_q02": "quarterly",             # AC_01 trap: claims quarterly reviews, no evidence
    "m1_q03": "within_week",           # not same-day (small shop, IT contractor does it)
    "m1_q04": "ad_groups",             # Google Workspace groups, not full RBAC
    "m1_q05": "yes_informal",          # least privilege exists but not documented
    "m1_q06": "named_admins",          # owner + IT contractor are the only admins
    "m1_q07": "yes_but_inconsistent",  # separation attempted but owner does everything
    "m1_q08": "yes_local_admin",       # shop floor PCs have local admin (CNC software needs it)
    "m1_q09": "lockout_configured",    # Google Workspace default lockout
    "m1_q10": "domain_gpo",            # Google Workspace login page counts
    "m1_q11": "generic_banner",        # "Authorized users only" on login
    "m1_q12": "yes_15_or_less",        # Windows screensaver lock 15 min
    "m1_q13": "no_termination",        # no session termination policy
    "m1_q14": "vpn_no_mfa",            # no remote access (no remote workers)
    "m1_q15": "vpn_logs_reviewed",     # N/A but closest non-gap answer
    "m1_q16": "unknown",               # don't know if crypto is FIPS
    "m1_q17": "few_managed",           # SonicWall + one Ubiquiti AP
    "m1_q18": "yes_unrestricted",      # no mobile device policy
    "m1_q19": "yes_wpa2_psk",          # WPA2-PSK (not enterprise)
    "m1_q20": "no_flat_network",       # flat network, no segmentation
    "m1_q21": "no_detection",          # no wireless IDS
    "m1_q22": "yes_unmanaged",         # personal phones access email, no MDM
    "m1_q23": "no_encryption",         # no mobile device encryption policy
    "m1_q24": "network_segmentation",  # SonicWall does basic zones
    "m1_q25": "policy_only",           # external system policy exists on paper
    "m1_q26": "firewall_controlled",   # SonicWall manages external connections
    "m1_q27": "no_policy",             # no portable storage policy
    "m1_q28": "no_public_systems",     # no public-facing systems
    "m2_at_3.2.1_status": "Partially implemented",
    "m2_at_3.2.2_status": "Partially implemented",
    "m2_at_3.2.3_status": "Not implemented",
    "m2_au_3.3.1_status": "Partially implemented",
    "m2_au_3.3.2_status": "Not implemented",
    "m2_au_3.3.3_status": "Partially implemented",
    "m2_au_3.3.4_status": "Not implemented",
    "m2_au_3.3.5_status": "Partially implemented",
    "m2_au_3.3.6_status": "Partially implemented",
    "m2_au_3.3.7_status": "Not implemented",
    "m2_au_3.3.8_status": "Fully implemented",
    "m2_au_3.3.9_status": "Not implemented",
    "m3_cm_3.4.1_status": "Fully implemented",
    "m3_cm_3.4.2_status": "Fully implemented",
    "m3_cm_3.4.3_status": "Partially implemented",
    "m3_cm_3.4.4_status": "Fully implemented",
    "m3_cm_3.4.5_status": "Partially implemented",
    "m3_cm_3.4.6_status": "Fully implemented",
    "m3_cm_3.4.7_status": "Partially implemented",
    "m3_cm_3.4.8_status": "Not implemented",
    "m3_cm_3.4.9_status": "Planned",
    "m3_ia_3.5.1_status": "Fully implemented",
    "m3_ia_3.5.2_status": "Fully implemented",
    "m3_ia_3.5.3_status": "Fully implemented",
    "m3_ia_3.5.3_mfa_scope": "All users and access methods",
    "m3_ia_3.5.4_status": "Fully implemented",
    "m3_ia_3.5.5_status": "Fully implemented",
    "m3_ia_3.5.6_status": "Fully implemented",
    "m3_ia_3.5.7_status": "Fully implemented",
    "m3_ia_3.5.8_status": "Fully implemented",
    "m3_ia_3.5.9_status": "Fully implemented",
    "m3_ia_3.5.10_status": "Partially implemented",
    "m3_ia_3.5.11_status": "Fully implemented",
    "m4_ir_3.6.1_status": "Partially implemented",
    "m4_ir_3.6.2_status": "Not implemented",
    "m4_ir_3.6.3_status": "Not implemented",
    "m4_ma_3.7.1_status": "Partially implemented",
    "m4_ma_3.7.2_status": "Not implemented",
    "m4_ma_3.7.3_status": "Partially implemented",
    "m4_ma_3.7.4_status": "Not implemented",
    "m4_ma_3.7.5_status": "Not implemented",
    "m4_ma_3.7.6_status": "Partially implemented",
    "m5_mp_3.8.1_status": "Partially implemented",
    "m5_mp_3.8.2_status": "Not implemented",
    "m5_mp_3.8.3_status": "Not implemented",
    "m5_mp_3.8.4_status": "Partially implemented",
    "m5_mp_3.8.5_status": "Partially implemented",
    "m5_mp_3.8.6_status": "Partially implemented",
    "m5_mp_3.8.7_status": "Not implemented",
    "m5_mp_3.8.8_status": "Not implemented",
    "m5_mp_3.8.9_status": "Not implemented",
    "m5_pe_3.10.1_status": "Fully implemented",
    "m5_pe_3.10.2_status": "Fully implemented",
    "m5_pe_3.10.3_status": "Partially implemented",
    "m5_pe_3.10.4_status": "Fully implemented",
    "m5_pe_3.10.5_status": "Fully implemented",
    "m5_pe_3.10.6_status": "Partially implemented",
    "m5_ps_3.9.1_status": "Fully implemented",
    "m5_ps_3.9.2_status": "Partially implemented",
    "m6_ra_3.11.1_status": "Partially implemented",
    "m6_ra_3.11.2_status": "Partially implemented",
    "m6_ra_3.11.3_status": "Not implemented",
    "m6_ca_3.12.1_status": "Partially implemented",
    "m6_ca_3.12.2_status": "Partially implemented",
    "m6_ca_3.12.3_status": "Partially implemented",
    "m6_ca_3.12.4_status": "Partially implemented",
    "m7_sc_3.13.1_status": "Fully implemented",
    "m7_sc_3.13.2_status": "Fully implemented",
    "m7_sc_3.13.3_status": "Fully implemented",
    "m7_sc_3.13.4_status": "Fully implemented",
    "m7_sc_3.13.5_status": "Fully implemented",
    "m7_sc_3.13.6_status": "Fully implemented",
    "m7_sc_3.13.7_status": "Fully implemented",
    "m7_sc_3.13.8_status": "Not implemented",
    "m7_sc_3.13.9_status": "Fully implemented",
    "m7_sc_3.13.10_status": "Fully implemented",
    "m7_sc_3.13.11_status": "Not implemented",
    "m7_sc_3.13.11_fips_scope": "No encryption",
    "m7_sc_3.13.12_status": "Partially implemented",
    "m7_sc_3.13.13_status": "Fully implemented",
    "m7_sc_3.13.14_status": "Fully implemented",
    "m7_sc_3.13.15_status": "Fully implemented",
    "m7_sc_3.13.16_status": "Not implemented",
    "m8_si_3.14.1_status": "Fully implemented",
    "m8_si_3.14.2_status": "Fully implemented",
    "m8_si_3.14.3_status": "Partially implemented",
    "m8_si_3.14.4_status": "Fully implemented",
    "m8_si_3.14.5_status": "Fully implemented",
    "m8_si_3.14.6_status": "Partially implemented",
    "m8_si_3.14.7_status": "Partially implemented",
}

from src.api.intake_modules import get_all_modules

out = []
for mod in get_all_modules():
    for q in mod.questions:
        qid = q.id
        if qid not in ANSWERS:
            print(f"WARNING: no answer for {qid}", file=sys.stderr)
            continue
        ctrls = list(set(filter(None, q.control_ids + ([q.control_id] if q.control_id else []))))
        out.append({
            "id": qid,
            "module": mod.number,
            "answer_value": ANSWERS[qid],
            "controls": sorted(ctrls) if ctrls else [],
        })

path = "scripts/simulation/fixtures/meridian_aerospace/intake_answers.yaml"
with open(path, "w", encoding="utf-8") as f:
    yaml.dump(out, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)

print(f"Wrote {len(out)} answers to {path}")
missing = set(ANSWERS.keys()) - {e["id"] for e in out}
if missing:
    print(f"WARN: defined but unmatched: {missing}")
extra = {e["id"] for e in out} - set(ANSWERS.keys())
if extra:
    print(f"WARN: questions without answers: {extra}")
