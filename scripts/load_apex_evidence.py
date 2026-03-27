"""
Load Apex Defense Solutions evidence artifacts from data/evidence/apex_samples/
into the database and link them to NIST 800-171 controls.

All artifacts loaded as DRAFT — run this once, then use the dashboard or demo
script to transition states.

Usage:
    python scripts/load_apex_evidence.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text
from src.db.session import get_session
from src.evidence.storage import upload_evidence, link_evidence_to_controls


def classify_evidence_type(filename: str) -> str:
    """Derive a CMMC evidence type label from a filename."""
    name = filename.lower()
    if any(k in name for k in ("policy", "plan")):
        return "Policy"
    if any(k in name for k in ("config", "configuration", "export")):
        return "Configuration"
    if any(k in name for k in ("scan", "vulnerability", "assessment")):
        return "Scan Report"
    if any(k in name for k in ("log", "audit")):
        return "Audit Log"
    if any(k in name for k in ("training", "awareness")):
        return "Training Record"
    if any(k in name for k in ("screenshot", "screen")):
        return "Screenshot"
    if any(k in name for k in ("diagram", "network")):
        return "Network Diagram"
    if any(k in name for k in ("incident", "response")):
        return "Incident Record"
    if any(k in name for k in ("roster", "personnel", "access")):
        return "Access Record"
    return "Documentation"

ORG_ID = "9de53b587b23450b87af"  # Apex Defense Solutions
UPLOADED_BY = "david.kim@apex-defense.us"
SAMPLES_DIR = os.path.join("data", "evidence", "apex_samples")

# Each entry: (filename, description, control_ids)
EVIDENCE_MANIFEST = [
    # ── ACCESS CONTROL ────────────────────────────────────────────────────────
    (
        "Apex_Access_Control_Policy_v4.2.md",
        "Access Control Policy v4.2 — least privilege, account management, remote access, quarterly review",
        ["AC.L2-3.1.1", "AC.L2-3.1.2", "AC.L2-3.1.5", "AC.L2-3.1.12"],
    ),
    (
        "Entra_ID_Conditional_Access_Export_20260301.json",
        "Azure AD Conditional Access policies export — MFA enforcement, legacy auth block, compliant device requirements",
        ["AC.L2-3.1.1", "AC.L2-3.1.2", "IA.L2-3.5.3", "AC.L2-3.1.12"],
    ),
    (
        "CyberArk_Privileged_Account_Inventory.csv",
        "CyberArk PAM privileged account inventory — 15 accounts with rotation schedules and MFA status",
        ["AC.L2-3.1.5", "AC.L2-3.1.6", "IA.L2-3.5.3"],
    ),
    (
        "VPN_GlobalProtect_Config.txt",
        "Palo Alto GlobalProtect VPN configuration — split tunneling disabled, HIP checks, 8h timeout",
        ["AC.L2-3.1.12", "AC.L2-3.1.14", "SC.L2-3.13.5"],
    ),
    (
        "Quarterly_Access_Review_Q1_2026.csv",
        "Q1 2026 quarterly access review — 15 accounts reviewed, 1 disabled, 1 orphaned account found and remediated",
        ["AC.L2-3.1.1", "AC.L2-3.1.2", "AC.L2-3.1.5"],
    ),
    # ── AUDIT & ACCOUNTABILITY ────────────────────────────────────────────────
    (
        "Splunk_SIEM_Configuration_Summary.md",
        "Splunk Enterprise 9.3.1 SIEM configuration — 10 data sources, 187GB/day, 10 active alert rules, 365-day retention",
        ["AU.L2-3.3.1", "AU.L2-3.3.2", "AU.L2-3.3.5", "AU.L2-3.3.6"],
    ),
    (
        "Audit_Log_Retention_Policy_v2.1.md",
        "Audit log retention policy v2.1 — 3-year standard, 5-year CUI/privileged activity, 7-year IR records",
        ["AU.L2-3.3.1", "AU.L2-3.3.2", "AU.L2-3.3.9"],
    ),
    (
        "Windows_Event_Log_GPO_Export.xml",
        "Windows Advanced Audit Policy GPO — Success/Failure for logon, account management, object access, privilege use",
        ["AU.L2-3.3.1", "AU.L2-3.3.2"],
    ),
    # ── CONFIGURATION MANAGEMENT ──────────────────────────────────────────────
    (
        "Intune_Compliance_Policy_Export.json",
        "Microsoft Intune compliance policies — CUI endpoint policy (BitLocker, Defender, patch level), 43/47 devices compliant",
        ["CM.L2-3.4.1", "CM.L2-3.4.2", "IA.L2-3.5.3"],
    ),
    (
        "CIS_Benchmark_Scan_Results_20260301.csv",
        "CIS Benchmark scan results — 14 systems, 90-98% compliance, no critical failures, review items tracked",
        ["CM.L2-3.4.1", "CM.L2-3.4.2", "RA.L2-3.11.2"],
    ),
    (
        "Change_Management_Procedure_v3.0.md",
        "Change management procedure v3.0 — Standard/Normal/Major/Emergency categories, CAB, two-person rule for Major changes",
        ["CM.L2-3.4.3", "CM.L2-3.4.4"],
    ),
    # ── IDENTIFICATION & AUTHENTICATION ───────────────────────────────────────
    (
        "Entra_MFA_Enforcement_Report_20260301.csv",
        "MFA enforcement report — 100% MFA compliance across all 16 active accounts; CISO/ISSO use FIDO2 hardware keys",
        ["IA.L2-3.5.3", "IA.L2-3.5.4"],
    ),
    (
        "Password_Policy_GPO_Settings.txt",
        "AD password policy — 14-char minimum, 24-history, 90-day max age; privileged accounts 20-char/60-day; service accounts CyberArk auto-rotated",
        ["IA.L2-3.5.7", "IA.L2-3.5.8"],
    ),
    # ── INCIDENT RESPONSE ────────────────────────────────────────────────────
    (
        "Incident_Response_Plan_v3.1.md",
        "Incident Response Plan v3.1 — P1-P4 severity, 6-phase response, DFARS 72-hour reporting procedures, SecureIT retainer",
        ["IR.L2-3.6.1", "IR.L2-3.6.2"],
    ),
    (
        "Tabletop_Exercise_Report_20260215.md",
        "Tabletop exercise TTX-2026-001 — ransomware scenario, 3hr exercise, 6 gaps found (4 remediated), DFARS reporting validated",
        ["IR.L2-3.6.3"],
    ),
    # ── MEDIA PROTECTION ─────────────────────────────────────────────────────
    (
        "BitLocker_Compliance_Report_All_Endpoints.csv",
        "BitLocker encryption compliance — 22 endpoints, XTS-AES 256, recovery keys backed up to Azure AD/HSM; 1 non-compliant (AES-128, older OS)",
        ["MP.L2-3.8.1", "MP.L2-3.8.9"],
    ),
    # ── PHYSICAL PROTECTION ──────────────────────────────────────────────────
    (
        "Facility_Access_Log_February_2026.csv",
        "Facility access log February 2026 — 25 events including 1 after-hours session, 1 denied entry, 1 vendor escort",
        ["PE.L2-3.10.1", "PE.L2-3.10.2", "PE.L2-3.10.3"],
    ),
    (
        "Physical_Security_Assessment_20260101.md",
        "Annual physical security assessment Jan 2026 — PASS, dual-factor physical access, CCTV, no critical findings",
        ["PE.L2-3.10.1", "PE.L2-3.10.2", "PE.L2-3.10.4", "PE.L2-3.10.5"],
    ),
    # ── RISK ASSESSMENT ──────────────────────────────────────────────────────
    (
        "Annual_Risk_Assessment_2026.md",
        "Annual risk assessment FY2026 — 14 risks identified, 2 HIGH (spearphish + ransomware), NIST 800-30 methodology",
        ["RA.L2-3.11.1", "RA.L2-3.11.2", "RA.L2-3.11.3"],
    ),
    (
        "Nessus_Vulnerability_Scan_Summary_20260301.csv",
        "Nessus vulnerability scan March 2026 — 4 scans, 0 unmitigated critical, 3 high findings with patch schedules",
        ["RA.L2-3.11.2", "RA.L2-3.11.3"],
    ),
    # ── SYSTEM & COMMUNICATIONS PROTECTION ───────────────────────────────────
    (
        "Network_Diagram_Apex_CUI_Enclave.md",
        "Network architecture doc v2.1 — 7 VLANs, CUI enclave isolated, zone-based firewall policies, remote access architecture",
        ["SC.L2-3.13.1", "SC.L2-3.13.5", "SC.L2-3.13.6"],
    ),
    (
        "Palo_Alto_Firewall_Rules_Export.csv",
        "Palo Alto firewall rule export — 20 rules, default-deny-all, CUI enclave isolation, SSL inspection, logging to Splunk",
        ["SC.L2-3.13.1", "SC.L2-3.13.5", "SC.L2-3.13.6"],
    ),
    (
        "TLS_Certificate_Inventory.csv",
        "TLS certificate inventory — 12 certs tracked, RSA 2048-4096, SHA-256, internal CA + public CA, 1 expired (decommissioned system)",
        ["SC.L2-3.13.8", "SC.L2-3.13.10"],
    ),
    # ── SECURITY ASSESSMENT ──────────────────────────────────────────────────
    (
        "POA_M_Tracking_Spreadsheet_Q1_2026.csv",
        "POA&M tracker Q1 2026 — 8 items (3 closed, 5 open), includes vulnerability patch schedules and NAS migration",
        ["CA.L2-3.12.2", "CA.L2-3.12.4"],
    ),
    # ── AWARENESS & TRAINING ─────────────────────────────────────────────────
    (
        "KnowBe4_Security_Training_Completion_20260301.csv",
        "KnowBe4 security training completion — 100% completion rate, 1 phishing click remediated, phishing simulation results",
        ["AT.L2-3.2.1", "AT.L2-3.2.2"],
    ),
    (
        "CUI_Handling_Training_Roster_2026.csv",
        "CUI handling training roster 2026 — 15 records, all CUI-authorized staff trained, ITAR training for export-control roles",
        ["AT.L2-3.2.1", "AT.L2-3.2.2"],
    ),
]


def load_all_evidence():
    loaded = 0
    skipped = 0
    total_links = 0

    print(f"\nLoading Apex Defense Solutions evidence artifacts")
    print(f"Source: {SAMPLES_DIR}")
    print(f"Org: {ORG_ID}")
    print("=" * 60)

    with get_session() as db:
        # Check for existing artifacts to avoid duplicates
        existing = db.execute(
            "SELECT filename FROM evidence_artifacts WHERE org_id = :org_id",
            {"org_id": ORG_ID},
        ).fetchall() if False else []  # Skip check — always load fresh

        for filename, description, control_ids in EVIDENCE_MANIFEST:
            file_path = os.path.join(SAMPLES_DIR, filename)

            if not os.path.exists(file_path):
                print(f"  SKIP (not found): {filename}")
                skipped += 1
                continue

            with open(file_path, "rb") as f:
                file_bytes = f.read()

            try:
                result = upload_evidence(
                    db=db,
                    org_id=ORG_ID,
                    filename=filename,
                    file_bytes=file_bytes,
                    uploaded_by=UPLOADED_BY,
                    description=description,
                    source_system="apex_samples",
                )

                artifact_id = result["artifact_id"]
                evidence_type = classify_evidence_type(filename)

                # Set evidence_type — upload_evidence doesn't accept it directly
                db.execute(
                    text("UPDATE evidence_artifacts SET evidence_type = :t WHERE id = :id"),
                    {"t": evidence_type, "id": artifact_id},
                )
                db.commit()

                links = link_evidence_to_controls(
                    db=db,
                    artifact_id=artifact_id,
                    control_ids=control_ids,
                )

                total_links += links
                loaded += 1
                print(
                    f"  OK  [{artifact_id}] {filename[:48]:<48} "
                    f"type={evidence_type:<18} → {len(control_ids)} controls"
                )

            except Exception as e:
                print(f"  ERR {filename}: {e}")
                skipped += 1

    print("=" * 60)
    print(f"Loaded:  {loaded} artifacts")
    print(f"Skipped: {skipped}")
    print(f"Control links created: {total_links}")
    print(f"\nAll artifacts in DRAFT state. Use the dashboard or run_demo.py")
    print(f"to transition states as needed.\n")


if __name__ == "__main__":
    load_all_evidence()
