"""
Full demo: Upload evidence â†’ Review â†’ Approve â†’ Publish â†’ Hash â†’ Manifest.
Run: python -m scripts.demo_evidence_flow
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from configs.settings import DATABASE_URL, EVIDENCE_DIR

from src.evidence.storage import (
    upload_evidence,
    link_evidence_to_controls,
    get_published_artifacts,
)
from src.evidence.state_machine import transition_evidence, verify_audit_chain
from src.evidence.hasher import generate_manifest, save_manifest


# â”€â”€ Sample evidence for Apex Defense Solutions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

SAMPLE_EVIDENCE = [
    {
        "filename": "AC_Policy_v2.1.pdf",
        "content": (
            b"ACCESS CONTROL POLICY\nApex Defense Solutions\nVersion 2.1\n"
            b"Effective: January 15, 2026\n\n"
            b"1. All system access requires unique user identification.\n"
            b"2. Multi-factor authentication (MFA) via Microsoft Entra ID is mandatory.\n"
            b"3. Privileged access is limited to authorized administrators only.\n"
            b"4. Access reviews conducted quarterly by IT Security Manager.\n"
            b"5. Account lockout after 5 failed attempts.\n"
        ),
        "description": "Access Control policy covering AC family requirements",
        "controls": ["AC.L2-3.1.1", "AC.L2-3.1.2", "AC.L2-3.1.5"],
    },
    {
        "filename": "Entra_MFA_Config_Export.json",
        "content": (
            b'{"tenant": "apexdefense.onmicrosoft.com",\n'
            b' "mfa_enforcement": "all_users",\n'
            b' "conditional_access_policies": 12,\n'
            b' "legacy_auth_blocked": true,\n'
            b' "exported": "2026-03-01T00:00:00Z"}\n'
        ),
        "description": "Microsoft Entra ID MFA configuration export",
        "controls": ["IA.L2-3.5.3"],
    },
    {
        "filename": "CrowdStrike_EDR_Dashboard_2026Q1.png",
        "content": b"\x89PNG\r\n\x1a\n" + b"\x00" * 256 + b"[simulated EDR screenshot]",
        "description": "CrowdStrike Falcon EDR dashboard screenshot Q1 2026",
        "controls": ["SI.L2-3.14.1", "SI.L2-3.14.2", "SI.L2-3.14.6"],
    },
    {
        "filename": "Incident_Response_Plan_v3.docx",
        "content": (
            b"INCIDENT RESPONSE PLAN\nApex Defense Solutions\nVersion 3.0\n"
            b"1. Preparation: Roles defined, tools provisioned.\n"
            b"2. Detection: Microsoft Sentinel SIEM with automated alerts.\n"
            b"3. Containment: Network isolation via Palo Alto PA-450.\n"
            b"4. Eradication: CrowdStrike Falcon remediation.\n"
            b"5. Recovery: Backup restoration from Veeam.\n"
            b"6. Lessons Learned: Post-incident review within 72 hours.\n"
        ),
        "description": "Incident Response Plan covering IR family",
        "controls": ["IR.L2-3.6.1", "IR.L2-3.6.2"],
    },
    {
        "filename": "KnowBe4_Training_Completion_2026.csv",
        "content": (
            b"employee_id,name,training_module,completion_date,score\n"
            b"E001,Jane Smith,Security Awareness 2026,2026-02-15,95\n"
            b"E002,Bob Johnson,Phishing Simulation,2026-02-20,88\n"
            b"E003,Alice Chen,CUI Handling,2026-01-30,92\n"
        ),
        "description": "KnowBe4 security awareness training completion report",
        "controls": ["AT.L2-3.2.1", "AT.L2-3.2.2"],
    },
    {
        "filename": "BitLocker_Compliance_Report.txt",
        "content": (
            b"BitLocker Encryption Status Report\n"
            b"Date: 2026-03-01\n"
            b"Total endpoints: 52\n"
            b"Encrypted (AES-256): 52\n"
            b"Compliance: 100%\n"
            b"Recovery keys escrowed to Entra ID: 52\n"
        ),
        "description": "BitLocker full-disk encryption compliance report",
        "controls": ["SC.L2-3.13.11", "MP.L2-3.8.6"],
    },
]


def main():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    org_id = "9de53b587b23450b87af"

    print("=" * 60)
    print("CMMC EVIDENCE LIFECYCLE DEMO â€” Apex Defense Solutions")
    print("=" * 60)

    # â”€â”€ Step 1: Upload all evidence â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print("\n--- STEP 1: Upload Evidence Artifacts ---")
    artifact_ids = []

    for ev in SAMPLE_EVIDENCE:
        result = upload_evidence(
            db=db,
            org_id=org_id,
            filename=ev["filename"],
            file_bytes=ev["content"],
            uploaded_by="demo-script",
            description=ev["description"],
            source_system="manual",
            evidence_dir=EVIDENCE_DIR,
        )
        artifact_ids.append((result["artifact_id"], ev))
        print(f"  Uploaded: {ev['filename']} â†’ {result['artifact_id']} (DRAFT)")

    print(f"\n  Total uploaded: {len(artifact_ids)} artifacts")

    # â”€â”€ Step 2: Link to controls â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print("\n--- STEP 2: Link Evidence to Controls ---")
    for aid, ev in artifact_ids:
        count = link_evidence_to_controls(db, aid, ev["controls"])
        print(f"  {ev['filename']} â†’ {count} control(s): {', '.join(ev['controls'])}")

    # â”€â”€ Step 3: Review all â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print("\n--- STEP 3: Review Evidence (DRAFT â†’ REVIEWED) ---")
    for aid, ev in artifact_ids:
        r = transition_evidence(db, aid, "reviewed", "sarah.jones@apex.com", "Reviewed for accuracy")
        print(f"  {ev['filename']}: {r['previous_state']} â†’ {r['new_state']}")

    # â”€â”€ Step 4: Approve all â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print("\n--- STEP 4: Approve Evidence (REVIEWED â†’ APPROVED) ---")
    for aid, ev in artifact_ids:
        r = transition_evidence(db, aid, "approved", "mike.director@apex.com", "Approved for publication")
        print(f"  {ev['filename']}: {r['previous_state']} â†’ {r['new_state']}")

    # â”€â”€ Step 5: Publish all (triggers SHA-256 hashing) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print("\n--- STEP 5: Publish Evidence (APPROVED â†’ PUBLISHED) ---")
    print("  (SHA-256 hashing occurs at publish time)")
    for aid, ev in artifact_ids:
        r = transition_evidence(db, aid, "published", "compliance-officer@apex.com", "Final for CMMC assessment")
        print(f"  {ev['filename']}: PUBLISHED")
        print(f"    SHA-256: {r['sha256_hash']}")

    # â”€â”€ Step 6: Generate manifest â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print("\n--- STEP 6: Generate CMMC Hash Manifest ---")
    published = get_published_artifacts(db, org_id)
    artifact_hashes = [
        {"filename": a["filename"], "sha256": a["sha256_hash"],
         "algorithm": "SHA-256", "file_size": a["file_size"]}
        for a in published
        if a["sha256_hash"]  # only include hashed artifacts
    ]

    manifest = generate_manifest(artifact_hashes, org_name="Apex Defense Solutions")
    filepath = save_manifest(manifest, "D:/cmmc-platform/data/exports", "Apex_Defense")
    print(f"\n  Manifest saved to: {filepath}")
    print(f"  Artifacts in manifest: {len(artifact_hashes)}")
    print(f"\n  --- Manifest Preview ---")
    print(manifest)

    # â”€â”€ Step 7: Verify audit chain â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print("\n--- STEP 7: Verify Audit Chain Integrity ---")
    chain = verify_audit_chain(db, org_id)
    print(f"  Chain valid: {chain['valid']}")
    print(f"  Entries checked: {chain['entries_checked']}")
    if chain["valid"]:
        print("  RESULT: Tamper-evident audit trail is INTACT")
    else:
        print(f"  WARNING: Chain broken at entry {chain['first_broken']}")

    # â”€â”€ Step 8: Try to tamper (should fail) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print("\n--- STEP 8: Immutability Test ---")
    try:
        transition_evidence(db, artifact_ids[0][0], "draft", "attacker")
        print("  FAIL: Published artifact was modified!")
    except Exception as e:
        print(f"  PASS: Published artifact is immutable ({type(e).__name__})")

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print(f"\nArtifacts uploaded: {len(artifact_ids)}")
    print(f"Artifacts published with SHA-256: {len(artifact_hashes)}")
    print(f"Audit trail entries: {chain['entries_checked']}")
    print(f"Manifest: {filepath}")

    db.close()


if __name__ == "__main__":
    main()
