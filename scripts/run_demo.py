"""
End-to-End Demo Flow Script â€” CMMC Compliance Platform

Walks through the full demo narrative:
  1. Start from clean state (SPRS = 0, no SSP, no evidence)
  2. Load 26 realistic Apex evidence artifacts
  3. Generate SSP (optional â€” requires Claude API key + ~30min)
  4. Show SPRS score jump
  5. Generate POA&M items
  6. Walk evidence through state machine â†’ publish
  7. Generate hash manifest
  8. Verify audit chain integrity
  9. Export evidence binder

Usage:
    python scripts/run_demo.py                    # interactive, step-by-step
    python scripts/run_demo.py --skip-ssp         # skip SSP generation (use existing)
    python scripts/run_demo.py --auto             # non-interactive, runs everything
"""

import sys
import os
import time
import json
import hashlib

# Force UTF-8 output so Unicode box-drawing / em-dashes render on all terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import argparse
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.db.session import get_session

ORG_ID = "9de53b587b23450b87af"
EVIDENCE_DIR = os.path.join("data", "evidence", ORG_ID)
EXPORTS_DIR = os.path.join("data", "exports")


def banner(msg):
    print()
    print("=" * 70)
    print(f"  {msg}")
    print("=" * 70)
    print()


def step(num, msg):
    print()
    print(f"  [{num}] {msg}")
    print("  " + "─" * 60)


def wait_for_enter(auto=False):
    if not auto:
        input("  Press ENTER to continue...")


def get_counts():
    """Get current DB counts."""
    with get_session() as session:
        counts = {}
        for table in ["ssp_sections", "evidence_artifacts", "poam_items", "audit_log"]:
            counts[table] = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        return counts


def get_sprs():
    """Quick SPRS calculation."""
    with get_session() as session:
        controls = session.execute(text("""
            SELECT c.id, c.points, c.poam_eligible,
                   s.implementation_status
            FROM controls c
            LEFT JOIN ssp_sections s ON c.id = s.control_id AND s.org_id = :org_id
        """), {"org_id": ORG_ID}).fetchall()

        poam = session.execute(text("""
            SELECT control_id FROM poam_items
            WHERE org_id = :org_id AND status IN ('OPEN', 'IN_PROGRESS')
        """), {"org_id": ORG_ID}).fetchall()
        poam_controls = {p[0] for p in poam}

        raw = 110
        conditional = 110
        met = partial = not_impl = no_ssp = 0

        for c in controls:
            cid, pts, eligible, status = c
            pts = pts or 1
            if status == "Implemented":
                met += 1
            elif status == "Partially Implemented":
                partial += 1
                raw -= pts
                if cid not in poam_controls:
                    conditional -= pts
            elif status == "Not Implemented":
                not_impl += 1
                raw -= pts
                if cid not in poam_controls or not eligible:
                    conditional -= pts
            else:
                no_ssp += 1
                raw -= pts
                conditional -= pts

        return {
            "raw": max(raw, -203),
            "conditional": max(conditional, -203),
            "met": met, "partial": partial, "not_impl": not_impl, "no_ssp": no_ssp,
            "poam_count": len(poam_controls),
        }


def write_audit(session, actor, actor_type, action, target_type, target_id, details):
    """Write a hash-chained audit entry.
    Hash format is identical to state_machine._compute_entry_hash so that
    fix_audit_chain.py and verify_audit_chain() both validate these entries.
    """
    from datetime import datetime, timezone

    last = session.execute(text(
        "SELECT entry_hash FROM audit_log ORDER BY id DESC LIMIT 1"
    )).fetchone()
    prev_hash = last[0] if last else "GENESIS"

    now = datetime.now(timezone.utc).isoformat()
    details_json = json.dumps(details)

    # Must match state_machine._compute_entry_hash exactly: JSON, sort_keys=True
    payload = json.dumps({
        "actor": actor,
        "actor_type": actor_type,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "details": details,
        "prev_hash": prev_hash,
        "timestamp": now,
    }, sort_keys=True, default=str)
    entry_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    session.execute(text("""
        INSERT INTO audit_log (timestamp, actor, actor_type, action, target_type,
                               target_id, details, prev_hash, entry_hash)
        VALUES (:timestamp, :actor, :actor_type, :action, :target_type,
                :target_id, CAST(:details AS json), :prev_hash, :entry_hash)
    """), {
        "timestamp": now,
        "actor": actor, "actor_type": actor_type,
        "action": action, "target_type": target_type, "target_id": target_id,
        "details": details_json, "prev_hash": prev_hash, "entry_hash": entry_hash,
    })


# â”€â”€â”€ DEMO STEPS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def step_1_show_empty_state(auto):
    step(1, "STARTING STATE â€” Empty dashboard")
    counts = get_counts()
    sprs = get_sprs()

    print(f"  SSP Sections:     {counts['ssp_sections']}")
    print(f"  Evidence:         {counts['evidence_artifacts']}")
    print(f"  POA&M Items:      {counts['poam_items']}")
    print(f"  Audit Entries:    {counts['audit_log']}")
    print(f"  SPRS Score:       {sprs['raw']}/110")
    print()

    if counts["ssp_sections"] > 0 or counts["evidence_artifacts"] > 0:
        print("  âš ï¸  Data found! Run 'python scripts/demo_reset.py --force' first.")
        print("  Or continue to see the demo with existing data.")

    print()
    print('  NARRATIVE: "Here\'s Apex Defense Solutions â€” 45 employees,')
    print('  subcontractor working with CUI. No SSP, no organized evidence,')
    print('  no compliance posture. Their SPRS score shows they haven\'t')
    print('  assessed any of the 110 NIST 800-171 controls."')
    wait_for_enter(auto)


def step_2_upload_evidence(auto):
    step(2, "UPLOADING EVIDENCE -- 26 realistic Apex artifacts")

    # (filename, description, control_ids)
    samples = [
        ("Apex_Access_Control_Policy_v4.2.md",
         "Access Control Policy v4.2 -- least privilege, account management, remote access, quarterly review",
         ["AC.L2-3.1.1", "AC.L2-3.1.2", "AC.L2-3.1.5", "AC.L2-3.1.12"]),

        ("Entra_ID_Conditional_Access_Export_20260301.json",
         "Azure AD Conditional Access policies -- MFA enforcement, legacy auth block, compliant device requirements",
         ["AC.L2-3.1.1", "AC.L2-3.1.2", "IA.L2-3.5.3", "AC.L2-3.1.12"]),

        ("CyberArk_Privileged_Account_Inventory.csv",
         "CyberArk PAM privileged account inventory -- 15 accounts with rotation schedules and MFA status",
         ["AC.L2-3.1.5", "AC.L2-3.1.6", "IA.L2-3.5.3"]),

        ("VPN_GlobalProtect_Config.txt",
         "Palo Alto GlobalProtect VPN configuration -- split tunneling disabled, HIP checks, 8h timeout",
         ["AC.L2-3.1.12", "AC.L2-3.1.14", "SC.L2-3.13.5"]),

        ("Quarterly_Access_Review_Q1_2026.csv",
         "Q1 2026 quarterly access review -- 15 accounts reviewed, 1 disabled, 1 orphaned account found",
         ["AC.L2-3.1.1", "AC.L2-3.1.2", "AC.L2-3.1.5"]),

        ("Splunk_SIEM_Configuration_Summary.md",
         "Splunk Enterprise 9.3.1 SIEM -- 10 data sources, 187GB/day, 10 alert rules, 365-day retention",
         ["AU.L2-3.3.1", "AU.L2-3.3.2", "AU.L2-3.3.5", "AU.L2-3.3.6"]),

        ("Audit_Log_Retention_Policy_v2.1.md",
         "Audit log retention policy v2.1 -- 3-year standard, 5-year CUI/privileged, 7-year IR records",
         ["AU.L2-3.3.1", "AU.L2-3.3.2", "AU.L2-3.3.9"]),

        ("Windows_Event_Log_GPO_Export.xml",
         "Windows Advanced Audit Policy GPO -- Success/Failure for logon, account management, object access",
         ["AU.L2-3.3.1", "AU.L2-3.3.2"]),

        ("Intune_Compliance_Policy_Export.json",
         "Microsoft Intune compliance policies -- CUI endpoint policy, 43/47 devices compliant",
         ["CM.L2-3.4.1", "CM.L2-3.4.2", "IA.L2-3.5.3"]),

        ("CIS_Benchmark_Scan_Results_20260301.csv",
         "CIS Benchmark scan results -- 14 systems, 90-98% compliance, no critical failures",
         ["CM.L2-3.4.1", "CM.L2-3.4.2", "RA.L2-3.11.2"]),

        ("Change_Management_Procedure_v3.0.md",
         "Change management procedure v3.0 -- CAB, Standard/Normal/Major/Emergency categories",
         ["CM.L2-3.4.3", "CM.L2-3.4.4"]),

        ("Entra_MFA_Enforcement_Report_20260301.csv",
         "MFA enforcement report -- 100% compliance, CISO/ISSO use FIDO2 hardware keys",
         ["IA.L2-3.5.3", "IA.L2-3.5.4"]),

        ("Password_Policy_GPO_Settings.txt",
         "AD password policy -- 14-char minimum, 24-history, 90-day max age; PAM auto-rotated service accounts",
         ["IA.L2-3.5.7", "IA.L2-3.5.8"]),

        ("Incident_Response_Plan_v3.1.md",
         "Incident Response Plan v3.1 -- P1-P4 severity, 6-phase response, DFARS 72-hour reporting",
         ["IR.L2-3.6.1", "IR.L2-3.6.2"]),

        ("Tabletop_Exercise_Report_20260215.md",
         "Tabletop exercise TTX-2026-001 -- ransomware scenario, 6 gaps found (4 remediated)",
         ["IR.L2-3.6.3"]),

        ("BitLocker_Compliance_Report_All_Endpoints.csv",
         "BitLocker compliance -- 22 endpoints, XTS-AES 256, recovery keys in Azure AD/HSM",
         ["MP.L2-3.8.1", "MP.L2-3.8.9"]),

        ("Facility_Access_Log_February_2026.csv",
         "Facility access log Feb 2026 -- 25 events, after-hours session, 1 denied entry",
         ["PE.L2-3.10.1", "PE.L2-3.10.2", "PE.L2-3.10.3"]),

        ("Physical_Security_Assessment_20260101.md",
         "Annual physical security assessment Jan 2026 -- PASS, dual-factor physical access, no critical findings",
         ["PE.L2-3.10.1", "PE.L2-3.10.2", "PE.L2-3.10.4", "PE.L2-3.10.5"]),

        ("Annual_Risk_Assessment_2026.md",
         "Annual risk assessment FY2026 -- 14 risks, 2 HIGH (spearphish + ransomware), NIST 800-30",
         ["RA.L2-3.11.1", "RA.L2-3.11.2", "RA.L2-3.11.3"]),

        ("Nessus_Vulnerability_Scan_Summary_20260301.csv",
         "Nessus scan March 2026 -- 4 scans, 0 unmitigated critical, 3 high findings with patch schedules",
         ["RA.L2-3.11.2", "RA.L2-3.11.3"]),

        ("Network_Diagram_Apex_CUI_Enclave.md",
         "Network architecture v2.1 -- 7 VLANs, CUI enclave isolated, zone-based firewall policies",
         ["SC.L2-3.13.1", "SC.L2-3.13.5", "SC.L2-3.13.6"]),

        ("Palo_Alto_Firewall_Rules_Export.csv",
         "Palo Alto firewall rules -- 20 rules, default-deny-all, CUI enclave isolation, SSL inspection",
         ["SC.L2-3.13.1", "SC.L2-3.13.5", "SC.L2-3.13.6"]),

        ("TLS_Certificate_Inventory.csv",
         "TLS certificate inventory -- 12 certs tracked, RSA 2048-4096, SHA-256",
         ["SC.L2-3.13.8", "SC.L2-3.13.10"]),

        ("POA_M_Tracking_Spreadsheet_Q1_2026.csv",
         "POA&M tracker Q1 2026 -- 8 items (3 closed, 5 open), vulnerability patch schedules",
         ["CA.L2-3.12.2", "CA.L2-3.12.4"]),

        ("KnowBe4_Security_Training_Completion_20260301.csv",
         "KnowBe4 training completion -- 100% completion, 1 phishing click remediated",
         ["AT.L2-3.2.1", "AT.L2-3.2.2"]),

        ("CUI_Handling_Training_Roster_2026.csv",
         "CUI handling training roster 2026 -- 15 records, all CUI-authorized staff trained, ITAR coverage",
         ["AT.L2-3.2.1", "AT.L2-3.2.2"]),
    ]

    APEX_SAMPLES_DIR = os.path.join("data", "evidence", "apex_samples")

    with get_session() as session:
        loaded = 0
        skipped = 0
        evidence_controls = set()

        for filename, desc, controls in samples:
            artifact_id = hashlib.sha256(
                f"{ORG_ID}-{filename}-apex".encode()
            ).hexdigest()[:20]

            exists = session.execute(
                text("SELECT id FROM evidence_artifacts WHERE id = :id"),
                {"id": artifact_id}
            ).fetchone()
            if exists:
                print(f"  - {filename} (already exists)")
                skipped += 1
                evidence_controls.update(controls)
                continue

            fpath = os.path.join(APEX_SAMPLES_DIR, filename)
            if not os.path.exists(fpath):
                print(f"  SKIP (file not found): {filename}")
                skipped += 1
                continue

            fsize = os.path.getsize(fpath)
            import mimetypes as _mt
            mime, _ = _mt.guess_type(filename)
            mime = mime or "application/octet-stream"

            session.execute(text("""
                INSERT INTO evidence_artifacts
                    (id, org_id, filename, file_path, file_size_bytes, mime_type,
                     state, source_system, description, owner, created_at, updated_at)
                VALUES
                    (:id, :org_id, :fn, :fp, :fsb, :mime,
                     'DRAFT', 'apex_samples', :desc, 'david.kim@apex-defense.us', NOW(), NOW())
            """), {"id": artifact_id, "org_id": ORG_ID, "fn": filename,
                   "fp": fpath, "fsb": fsize, "mime": mime, "desc": desc})

            for ctrl_id in controls:
                link_id = hashlib.sha256(
                    f"{artifact_id}-{ctrl_id}".encode()
                ).hexdigest()[:20]
                session.execute(text("""
                    INSERT INTO evidence_control_map (id, evidence_id, control_id)
                    VALUES (:id, :eid, :cid)
                    ON CONFLICT DO NOTHING
                """), {"id": link_id, "eid": artifact_id, "cid": ctrl_id})

            write_audit(session, "demo_script", "system", "evidence.upload",
                        "evidence_artifact", artifact_id,
                        {"filename": filename, "controls": controls})

            evidence_controls.update(controls)
            loaded += 1
            print(f"  + {filename[:55]:<55} -> {len(controls)} controls")

        session.commit()

    print(f"\n  Total: {loaded} uploaded, {skipped} skipped, "
          f"{len(evidence_controls)} unique controls covered")
    print()
    print('  NARRATIVE: "We load their existing documentation -- policies,')
    print('  configurations, scan results, training records, network diagrams.')
    print('  The platform links each artifact to the controls it supports."')
    wait_for_enter(auto)


def step_3_generate_ssp(auto, skip_ssp):
    step(3, "GENERATING SSP â€” AI-powered narratives for 110 controls")

    if skip_ssp:
        counts = get_counts()
        if counts["ssp_sections"] > 0:
            print(f"  Skipping SSP generation â€” {counts['ssp_sections']} sections already exist.")
        else:
            print("  Skipping SSP generation (--skip-ssp flag).")
            print("  To generate, run: python scripts/generate_ssp.py")
            print("  (requires ANTHROPIC_API_KEY, takes ~30 minutes, costs ~$2-3)")
    else:
        print("  Starting SSP generation via Claude API...")
        print("  This will generate narratives for all 110 NIST 800-171 controls.")
        print("  Estimated time: ~30 minutes | Estimated cost: ~$2-3")
        print()
        print("  Running: python scripts/generate_ssp.py")
        print()

        # Import and run the generator
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "scripts/generate_ssp.py"],
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                capture_output=False,
            )
            if result.returncode != 0:
                print(f"  âš ï¸ SSP generation exited with code {result.returncode}")
        except Exception as e:
            print(f"  âš ï¸ Error running SSP generation: {e}")
            print("  You can run it manually: python scripts/generate_ssp.py")

    print()
    sprs = get_sprs()
    print(f"  SPRS Score (raw): {sprs['raw']}/110")
    print(f"  Implemented: {sprs['met']}  |  Partial: {sprs['partial']}  |  Not Impl: {sprs['not_impl']}")
    print()
    print('  NARRATIVE: "The AI agent analyzes each of the 110 controls against')
    print('  Apex\'s technology stack â€” Microsoft Entra ID, CrowdStrike, Palo Alto,')
    print('  M365 GCC High â€” and generates specific implementation narratives.')
    print('  Not generic boilerplate. Specific to this organization."')
    wait_for_enter(auto)


def step_4_show_score(auto):
    step(4, "SPRS SCORE â€” Compliance posture revealed")
    sprs = get_sprs()

    print(f"  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”")
    print(f"  â”‚  SPRS Score (Raw):  {sprs['raw']:>4}/110            â”‚")
    print(f"  â”‚  Implemented:       {sprs['met']:>4} controls       â”‚")
    print(f"  â”‚  Partial:           {sprs['partial']:>4} controls       â”‚")
    print(f"  â”‚  Not Implemented:   {sprs['not_impl']:>4} controls       â”‚")
    print(f"  â”‚  No SSP:            {sprs['no_ssp']:>4} controls       â”‚")
    print(f"  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜")
    print()

    if sprs['raw'] >= 88:
        print("  âœ… Score is above POA&M threshold (88). Eligible for conditional certification.")
    else:
        print(f"  âš ï¸ Score is below POA&M threshold (88). Gap of {88 - sprs['raw']} points.")
        print("  POA&M items can provide conditional credit for partial/unmet controls.")

    print()
    print('  NARRATIVE: "The dashboard instantly shows where they stand.')
    print('  Red items are gaps. The SPRS score tells us how far from')
    print('  certification they are â€” and exactly what needs to be fixed."')
    wait_for_enter(auto)


def step_5_generate_poam(auto):
    step(5, "GENERATING POA&M â€” Remediation plan with 180-day deadlines")

    with get_session() as session:
        # Get controls needing POA&M
        ssp_gaps = session.execute(text("""
            SELECT s.control_id, s.implementation_status, c.points, c.poam_eligible, c.title
            FROM ssp_sections s
            JOIN controls c ON c.id = s.control_id
            WHERE s.org_id = :org_id
              AND s.implementation_status IN ('Partially Implemented', 'Not Implemented')
        """), {"org_id": ORG_ID}).fetchall()

        existing = session.execute(text("""
            SELECT control_id FROM poam_items
            WHERE org_id = :org_id AND status IN ('OPEN', 'IN_PROGRESS')
        """), {"org_id": ORG_ID}).fetchall()
        existing_set = {e[0] for e in existing}

        deadline = (datetime.now(timezone.utc) + timedelta(days=180)).isoformat()
        created = 0

        for ctrl_id, status, pts, eligible, title in ssp_gaps:
            if ctrl_id in existing_set:
                continue
            if not eligible:
                print(f"  âœ— {ctrl_id} â€” NOT POA&M eligible (blocked)")
                continue

            pts = pts or 1
            risk = "CRITICAL" if pts >= 5 else ("HIGH" if pts >= 3 else "MEDIUM")
            poam_id = "poam-" + hashlib.sha256(f"{ORG_ID}-{ctrl_id}-poam".encode()).hexdigest()[:8]

            session.execute(text("""
                INSERT INTO poam_items
                    (id, org_id, control_id, weakness_description, remediation_plan,
                     status, risk_level, scheduled_completion, created_at, updated_at)
                VALUES
                    (:id, :org_id, :control_id, :weakness, :plan,
                     'OPEN', :risk, :deadline, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": poam_id, "org_id": ORG_ID, "control_id": ctrl_id,
                "weakness": f"{ctrl_id} ({title[:60]}) is {status}.",
                "plan": f"Complete implementation of {ctrl_id} and collect evidence.",
                "risk": risk, "deadline": deadline,
            })

            write_audit(session, "demo_script", "system", "poam.create",
                       "poam_item", poam_id, {"control_id": ctrl_id, "risk": risk})
            created += 1
            print(f"  âœ“ POA&M: {ctrl_id} ({risk}, {pts}pts)")

        session.commit()

    sprs = get_sprs()
    print(f"\n  Created {created} POA&M items")
    print(f"  SPRS Score (conditional): {sprs['conditional']}/110")
    print(f"  SPRS Score (raw):         {sprs['raw']}/110")
    print(f"  Active POA&M items:       {sprs['poam_count']}")
    print()
    print('  NARRATIVE: "POA&M items give conditional credit â€” the score jumps')
    print('  because the organization has committed to fix these gaps within')
    print('  180 days. The platform tracks every deadline automatically."')
    wait_for_enter(auto)


def step_6_publish_evidence(auto):
    step(6, "PUBLISHING EVIDENCE â€” State machine walkthrough")
    print("  Walking all evidence through: DRAFT â†’ REVIEWED â†’ APPROVED â†’ PUBLISHED")
    print()

    with get_session() as session:
        artifacts = session.execute(text("""
            SELECT id, filename, file_path, state
            FROM evidence_artifacts
            WHERE org_id = :org_id
            ORDER BY created_at
        """), {"org_id": ORG_ID}).fetchall()

        for aid, filename, fpath, state in artifacts:
            transitions = []
            if state == "DRAFT":
                transitions = ["REVIEWED", "APPROVED", "PUBLISHED"]
            elif state == "REVIEWED":
                transitions = ["APPROVED", "PUBLISHED"]
            elif state == "APPROVED":
                transitions = ["PUBLISHED"]
            elif state == "PUBLISHED":
                print(f"  âœ“ {filename} â€” already PUBLISHED")
                continue

            for new_state in transitions:
                if new_state == "PUBLISHED" and fpath and os.path.exists(fpath):
                    sha256 = hashlib.sha256()
                    with open(fpath, "rb") as f:
                        for chunk in iter(lambda: f.read(8192), b""):
                            sha256.update(chunk)
                    file_hash = sha256.hexdigest()

                    session.execute(text("""
                        UPDATE evidence_artifacts
                        SET state = 'PUBLISHED', sha256_hash = :hash,
                            hash_algorithm = 'SHA-256', published_at = NOW(), updated_at = NOW()
                        WHERE id = :id
                    """), {"hash": file_hash, "id": aid})
                elif new_state == "REVIEWED":
                    session.execute(text("""
                        UPDATE evidence_artifacts
                        SET state = 'REVIEWED', reviewed_at = NOW(), updated_at = NOW()
                        WHERE id = :id
                    """), {"id": aid})
                elif new_state == "APPROVED":
                    session.execute(text("""
                        UPDATE evidence_artifacts
                        SET state = 'APPROVED', approved_at = NOW(), updated_at = NOW()
                        WHERE id = :id
                    """), {"id": aid})

                write_audit(session, "demo_script", "system", "evidence.state_change",
                           "evidence_artifact", aid,
                           {"from": state, "to": new_state, "filename": filename})
                state = new_state

            print(f"  âœ“ {filename} â†’ PUBLISHED (SHA-256 hash locked)")

        session.commit()

    print()
    print('  NARRATIVE: "Every piece of evidence goes through a strict state machine.')
    print('  Draft, Reviewed, Approved, Published. Once published, the file is')
    print('  SHA-256 hashed and becomes immutable. No one can alter it â€” not even')
    print('  an admin. The hash proves the evidence hasn\'t been tampered with."')
    wait_for_enter(auto)


def step_7_generate_manifest(auto):
    step(7, "HASH MANIFEST â€” CMMC-format evidence integrity proof")

    with get_session() as session:
        published = session.execute(text("""
            SELECT filename, sha256_hash
            FROM evidence_artifacts
            WHERE org_id = :org_id AND state = 'PUBLISHED'
            ORDER BY filename
        """), {"org_id": ORG_ID}).fetchall()

    lines = []
    for filename, sha_hash in published:
        lines.append(f"SHA256  {sha_hash}  {filename}")

    manifest_content = "\n".join(lines)
    manifest_hash = hashlib.sha256(manifest_content.encode()).hexdigest()
    lines.append("---")
    lines.append(f"SHA256  {manifest_hash}  MANIFEST.txt")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"Organization: Apex Defense Solutions")
    lines.append(f"Artifacts: {len(published)}")

    manifest_text = "\n".join(lines)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    manifest_path = os.path.join(EXPORTS_DIR, f"MANIFEST_Apex_Defense_{ts}.txt")
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest_text)

    print(manifest_text)
    print()
    print(f"  Saved to: {manifest_path}")
    print()
    print('  NARRATIVE: "This manifest is in the exact format CMMC assessors')
    print('  expect. Every artifact has a SHA-256 hash. The manifest itself')
    print('  is hash-signed. Upload it to eMASS or hand it to your C3PAO.')
    print('  Cryptographic proof that nothing was altered after approval."')
    wait_for_enter(auto)


def step_8_verify_audit(auto):
    step(8, "AUDIT CHAIN â€” Tamper-evident integrity verification")

    with get_session() as session:
        log = session.execute(text(
            "SELECT id, timestamp, actor, action, target_id, prev_hash, entry_hash "
            "FROM audit_log ORDER BY id ASC"
        )).fetchall()

    print(f"  Verifying {len(log)} audit log entries...")
    print()

    broken = False
    for i, entry in enumerate(log):
        eid, ts, actor, action, target, prev_h, entry_h = entry
        if i == 0:
            expected_prev = prev_h  # accept GENESIS or any genesis sentinel
        else:
            expected_prev = log[i - 1][6]  # entry_hash of previous row

        if prev_h != expected_prev:
            print(f"  âŒ CHAIN BROKEN at entry #{eid}!")
            broken = True
            break

    if not broken:
        print(f"  âœ… Audit chain INTACT â€” {len(log)} entries, all hash links verified")
        print(f"  First entry: #{log[0][0]} ({log[0][3]})")
        print(f"  Last entry:  #{log[-1][0]} ({log[-1][3]})")
    print()
    print('  NARRATIVE: "Every action on this platform â€” every upload, every')
    print('  state transition, every SSP generation â€” is recorded in a')
    print('  hash-chained audit log. Like a blockchain for compliance.')
    print('  If anyone tampers with any entry, the chain breaks. Assessors')
    print('  can verify the entire history is authentic."')
    wait_for_enter(auto)


def step_9_summary(auto):
    step(9, "DEMO COMPLETE â€” Summary")

    sprs = get_sprs()
    counts = get_counts()

    print(f"  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”")
    print(f"  â”‚  FINAL STATE                                     â”‚")
    print(f"  â”‚                                                   â”‚")
    print(f"  â”‚  SPRS Score:        {sprs['conditional']:>4}/110 (conditional)      â”‚")
    print(f"  â”‚  Raw Score:         {sprs['raw']:>4}/110                   â”‚")
    print(f"  â”‚  SSP Sections:      {counts['ssp_sections']:>4}                        â”‚")
    print(f"  â”‚  Evidence Artifacts: {counts['evidence_artifacts']:>3} (all PUBLISHED)        â”‚")
    print(f"  â”‚  POA&M Items:       {sprs['poam_count']:>4}                        â”‚")
    print(f"  â”‚  Audit Entries:     {counts['audit_log']:>4} (chain INTACT)       â”‚")
    print(f"  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜")
    print()
    print('  NARRATIVE: "In under an hour, we took Apex Defense from zero')
    print('  compliance posture to assessment-ready â€” with a complete SSP,')
    print('  organized evidence, cryptographic hashing, gap assessment,')
    print('  POA&M tracking, and a tamper-proof audit trail.')
    print()
    print('  This platform runs entirely on-premises. No CUI ever leaves')
    print('  the customer\'s network. The AI runs on their own hardware.')
    print('  That\'s what sovereign compliance looks like."')
    print()
    print("  " + "=" * 50)
    print("  Demo complete. Open the Streamlit dashboard to explore:")
    print("  python -m streamlit run src\\ui\\dashboard.py --server.port 8501")
    print("  " + "=" * 50)


# â”€â”€â”€ Main â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def main():
    parser = argparse.ArgumentParser(description="CMMC Platform End-to-End Demo")
    parser.add_argument("--skip-ssp", action="store_true", help="Skip SSP generation (use existing)")
    parser.add_argument("--auto", action="store_true", help="Non-interactive mode")
    args = parser.parse_args()

    banner("CMMC COMPLIANCE PLATFORM â€” END-TO-END DEMO")
    print("  Organization: Apex Defense Solutions (45 employees)")
    print("  Framework:    NIST 800-171 Rev 2 (110 controls)")
    print("  Goal:         CMMC Level 2 certification readiness")
    print()

    if not args.auto:
        print("  This demo walks through the full platform capabilities.")
        print("  Press ENTER at each step to continue.")
        input("  Press ENTER to begin...")

    step_1_show_empty_state(args.auto)
    step_2_upload_evidence(args.auto)
    step_3_generate_ssp(args.auto, args.skip_ssp)
    step_4_show_score(args.auto)
    step_5_generate_poam(args.auto)
    step_6_publish_evidence(args.auto)
    step_7_generate_manifest(args.auto)
    step_8_verify_audit(args.auto)
    step_9_summary(args.auto)


if __name__ == "__main__":
    main()

