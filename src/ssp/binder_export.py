"""
Evidence Binder Export — generates a complete CMMC assessment package as ZIP.

Contents:
  00_INDEX.txt                    — Binder table of contents
  01_SSP/                         — System Security Plan (.docx)
  02_Evidence/{FAMILY}/           — Evidence files organized by control family
  03_Manifest/                    — SHA-256 hash manifest
  04_POAM/                        — POA&M report
  05_Audit/                       — Audit log export
  06_Scoring/                     — SPRS scoring breakdown

Usage:
    from src.ssp.binder_export import generate_binder
    zip_path = generate_binder(org_id="9de53b587b23450b87af")

    # Or run directly:
    python -m src.ssp.binder_export
"""

import os
import sys
import json
import zipfile
import hashlib
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from src.db.session import get_session

ORG_ID = "9de53b587b23450b87af"
EVIDENCE_DIR = os.path.join("data", "evidence", ORG_ID)
EXPORTS_DIR = os.path.join("data", "exports")

FAMILY_NAMES = {
    "AC": "Access_Control", "AT": "Awareness_Training", "AU": "Audit_Accountability",
    "CM": "Config_Management", "IA": "Identification_Auth", "IR": "Incident_Response",
    "MA": "Maintenance", "MP": "Media_Protection", "PE": "Physical_Protection",
    "PS": "Personnel_Security", "RA": "Risk_Assessment", "CA": "Security_Assessment",
    "SC": "System_Comms_Protection", "SI": "System_Info_Integrity",
}


def generate_binder(org_id=ORG_ID, org_name="Apex Defense Solutions"):
    """Generate a complete CMMC assessment binder as a ZIP file."""

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"CMMC_Assessment_Binder_{ts}.zip"
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    zip_path = os.path.join(EXPORTS_DIR, zip_name)

    with get_session() as session:
        # Gather all data
        ssp_sections = session.execute(text("""
            SELECT s.control_id, s.implementation_status, s.narrative, s.evidence_refs, s.gaps,
                   c.family_abbrev, c.title, c.points
            FROM ssp_sections s
            JOIN controls c ON c.id = s.control_id
            WHERE s.org_id = :org_id
            ORDER BY c.family_abbrev, c.id
        """), {"org_id": org_id}).fetchall()

        evidence = session.execute(text("""
            SELECT id, filename, file_path, sha256_hash, state, evidence_type,
                   source_system, description
            FROM evidence_artifacts
            WHERE org_id = :org_id
            ORDER BY filename
        """), {"org_id": org_id}).fetchall()

        # Evidence-control links
        ev_links = session.execute(text("""
            SELECT ecm.evidence_id, ecm.control_id, c.family_abbrev
            FROM evidence_control_map ecm
            JOIN evidence_artifacts ea ON ea.id = ecm.evidence_id
            JOIN controls c ON c.id = ecm.control_id
            WHERE ea.org_id = :org_id
        """), {"org_id": org_id}).fetchall()

        poam = session.execute(text("""
            SELECT p.id, p.control_id, p.weakness_description, p.remediation_plan,
                   p.status, p.risk_level, p.scheduled_completion,
                   c.title as control_title, c.points, c.family_abbrev
            FROM poam_items p
            JOIN controls c ON c.id = p.control_id
            WHERE p.org_id = :org_id
            ORDER BY c.points DESC
        """), {"org_id": org_id}).fetchall()

        audit_log = session.execute(text("""
            SELECT id, timestamp, actor, actor_type, action, target_type,
                   target_id, details, entry_hash
            FROM audit_log ORDER BY id ASC
        """)).fetchall()

        # SPRS calculation
        controls = session.execute(text("""
            SELECT c.id, c.points, c.poam_eligible,
                   s.implementation_status
            FROM controls c
            LEFT JOIN ssp_sections s ON c.id = s.control_id AND s.org_id = :org_id
        """), {"org_id": org_id}).fetchall()

        poam_controls = {p[1] for p in poam if p[4] in ("OPEN", "IN_PROGRESS")}
        raw_score = 110
        conditional_score = 110
        met = partial = not_impl = no_ssp = 0

        for c in controls:
            cid, pts, eligible, status = c
            pts = pts or 1
            if status == "Implemented":
                met += 1
            elif status == "Partially Implemented":
                partial += 1
                raw_score -= pts
                if cid not in poam_controls:
                    conditional_score -= pts
            elif status == "Not Implemented":
                not_impl += 1
                raw_score -= pts
                if cid not in poam_controls or not eligible:
                    conditional_score -= pts
            else:
                no_ssp += 1
                raw_score -= pts
                conditional_score -= pts

    # Build evidence-to-family mapping
    ev_family_map = {}  # evidence_id -> set of families
    for eid, ctrl_id, fam in ev_links:
        ev_family_map.setdefault(eid, set()).add(fam)

    # ─── Write ZIP ────────────────────────────────────────────────────────
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:

        # 1. SSP Document
        ssp_files = sorted(
            [f for f in os.listdir(EXPORTS_DIR) if f.startswith("SSP_") and f.endswith(".docx")],
            reverse=True,
        ) if os.path.exists(EXPORTS_DIR) else []
        if ssp_files:
            zf.write(os.path.join(EXPORTS_DIR, ssp_files[0]), f"01_SSP/{ssp_files[0]}")

        # Also write a text summary of SSP
        if ssp_sections:
            ssp_text = f"SYSTEM SECURITY PLAN — TEXT SUMMARY\n"
            ssp_text += f"Organization: {org_name}\n"
            ssp_text += f"Generated: {datetime.now(timezone.utc).isoformat()}\n"
            ssp_text += f"Controls: {len(ssp_sections)}/110\n"
            ssp_text += "=" * 80 + "\n\n"

            current_family = None
            for ctrl_id, status, narrative, ev_refs, gaps, fam, title, pts in ssp_sections:
                if fam != current_family:
                    current_family = fam
                    fam_name = FAMILY_NAMES.get(fam, fam)
                    ssp_text += f"\n{'=' * 70}\n"
                    ssp_text += f"  {fam} — {fam_name}\n"
                    ssp_text += f"{'=' * 70}\n\n"

                ssp_text += f"─── {ctrl_id} — {title} ({pts}pts, {status}) ───\n\n"
                ssp_text += f"{narrative or 'No narrative generated.'}\n\n"

                if gaps:
                    gap_list = gaps if isinstance(gaps, list) else json.loads(gaps) if gaps else []
                    if gap_list:
                        ssp_text += f"GAPS: {', '.join(str(g) for g in gap_list)}\n\n"

            zf.writestr("01_SSP/SSP_Text_Summary.txt", ssp_text)

        # 2. Evidence files by family
        for eid, filename, fpath, sha_hash, state, etype, source, desc in evidence:
            families = ev_family_map.get(eid, {"UNLINKED"})
            for fam in families:
                fam_name = FAMILY_NAMES.get(fam, fam)
                if fpath and os.path.exists(fpath):
                    zf.write(fpath, f"02_Evidence/{fam}_{fam_name}/{filename}")

        # Evidence index
        ev_index = "EVIDENCE INDEX\n" + "=" * 60 + "\n\n"
        for eid, filename, fpath, sha_hash, state, etype, source, desc in evidence:
            families = ev_family_map.get(eid, set())
            ev_index += f"File: {filename}\n"
            ev_index += f"  Type: {etype}  |  Source: {source}  |  State: {state}\n"
            ev_index += f"  SHA-256: {sha_hash or 'Not yet hashed'}\n"
            ev_index += f"  Controls: {', '.join(sorted(families)) if families else 'None'}\n"
            ev_index += f"  Description: {desc or 'N/A'}\n\n"
        zf.writestr("02_Evidence/EVIDENCE_INDEX.txt", ev_index)

        # 3. Hash manifest
        published = [(fn, h) for _, fn, _, h, s, _, _, _ in evidence if s == "PUBLISHED" and h]
        if published:
            lines = [f"SHA256  {h}  {fn}" for fn, h in published]
            manifest_content = "\n".join(lines)
            manifest_hash = hashlib.sha256(manifest_content.encode()).hexdigest()
            lines.append("---")
            lines.append(f"SHA256  {manifest_hash}  MANIFEST.txt")
            lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
            lines.append(f"Organization: {org_name}")
            lines.append(f"Artifacts: {len(published)}")
            zf.writestr("03_Manifest/HASH_MANIFEST.txt", "\n".join(lines))

        # 4. POA&M Report
        if poam:
            poam_text = f"PLAN OF ACTION & MILESTONES (POA&M)\n"
            poam_text += f"Organization: {org_name}\n"
            poam_text += f"Generated: {datetime.now(timezone.utc).isoformat()}\n"
            poam_text += f"Total Items: {len(poam)}\n"
            poam_text += "=" * 80 + "\n\n"

            for pid, ctrl_id, weakness, plan, status, risk, deadline, ctitle, pts, fam in poam:
                poam_text += f"ID: {pid}\n"
                poam_text += f"Control: {ctrl_id} — {ctitle} ({pts}pts)\n"
                poam_text += f"Family: {fam}  |  Status: {status}  |  Risk: {risk}\n"
                poam_text += f"Weakness: {weakness}\n"
                poam_text += f"Remediation: {plan}\n"
                poam_text += f"Deadline: {deadline}\n"
                poam_text += "-" * 40 + "\n\n"

            zf.writestr("04_POAM/POAM_Report.txt", poam_text)

        # 5. Audit log
        if audit_log:
            audit_text = f"AUDIT LOG EXPORT\n"
            audit_text += f"Generated: {datetime.now(timezone.utc).isoformat()}\n"
            audit_text += f"Total Entries: {len(audit_log)}\n"
            audit_text += "=" * 80 + "\n\n"

            for aid, ts, actor, atype, action, ttype, tid, details, ehash in audit_log:
                audit_text += f"#{aid} | {ts} | {actor} ({atype})\n"
                audit_text += f"  Action: {action} | Target: {ttype}:{tid}\n"
                audit_text += f"  Hash: {ehash or 'N/A'}\n"
                if details:
                    d = details if isinstance(details, dict) else json.loads(details) if details else {}
                    audit_text += f"  Details: {json.dumps(d)}\n"
                audit_text += "\n"

            zf.writestr("05_Audit/Audit_Log_Export.txt", audit_text)

        # 6. Scoring breakdown
        scoring_text = f"SPRS SCORING BREAKDOWN\n"
        scoring_text += f"Organization: {org_name}\n"
        scoring_text += f"Generated: {datetime.now(timezone.utc).isoformat()}\n"
        scoring_text += "=" * 80 + "\n\n"
        scoring_text += f"SPRS Score (Raw):         {max(raw_score, -203)}/110\n"
        scoring_text += f"SPRS Score (Conditional): {max(conditional_score, -203)}/110\n"
        scoring_text += f"POA&M Threshold:          88/110\n\n"
        scoring_text += f"Implemented:              {met}\n"
        scoring_text += f"Partially Implemented:    {partial}\n"
        scoring_text += f"Not Implemented:          {not_impl}\n"
        scoring_text += f"No SSP:                   {no_ssp}\n"
        scoring_text += f"Active POA&M Items:       {len(poam_controls)}\n"
        zf.writestr("06_Scoring/SPRS_Breakdown.txt", scoring_text)

        # 0. Index
        index_text = f"""CMMC LEVEL 2 ASSESSMENT BINDER
Organization: {org_name}
Generated: {datetime.now(timezone.utc).isoformat()}
Platform: CMMC Compliance Platform v0.9.0

{'=' * 60}

CONTENTS:
  00_INDEX.txt                 This file
  01_SSP/                      System Security Plan
  02_Evidence/                 Evidence artifacts by control family
  03_Manifest/                 SHA-256 hash manifest (eMASS format)
  04_POAM/                     Plan of Action & Milestones
  05_Audit/                    Hash-chained audit log
  06_Scoring/                  SPRS scoring breakdown

SUMMARY:
  SPRS Score:          {max(conditional_score, -203)}/110 (conditional)
  Raw Score:           {max(raw_score, -203)}/110
  Controls Assessed:   {met + partial + not_impl}/{met + partial + not_impl + no_ssp}
  Evidence Artifacts:  {len(evidence)}
  POA&M Items:         {len(poam)}
  Audit Log Entries:   {len(audit_log)}

NOTE: All published evidence artifacts include SHA-256 hashes
computed at publish time. The hash manifest in 03_Manifest/
can be used for eMASS upload and C3PAO assessment verification.
"""
        zf.writestr("00_INDEX.txt", index_text)

    print(f"Evidence binder created: {zip_path}")
    print(f"  SSP sections: {len(ssp_sections)}")
    print(f"  Evidence files: {len(evidence)}")
    print(f"  POA&M items: {len(poam)}")
    print(f"  Audit entries: {len(audit_log)}")

    return zip_path


if __name__ == "__main__":
    path = generate_binder()
    print(f"\nDone: {path}")
