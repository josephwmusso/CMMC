"""
src/exports/binder.py

C3PAO-ready evidence binder export. Returns an in-memory ZIP containing:

  00_README.md               — cover letter + structure guide
  01_SSP/                    — SSP text summary (per-control narratives)
  02_POAM/                   — POA&M text report
  03_SPRS_Scorecard.pdf      — one-page SPRS breakdown (fpdf2)
  04_Manifest.json           — SHA-256 manifest + package hash
  05_Manifest.csv            — same manifest in CSV for spreadsheets
  06_Audit_Log.json          — append-only hash-chained audit export
  07_Assessment_Snapshot.json— latest truth-model simulation (if any)
  by_family/{family}/        — per-family summary + per-control markdown
  raw/                       — machine-readable JSON exports

All file I/O is in-memory (io.BytesIO). No temp files on disk —
compatible with Render free-tier ephemeral storage constraints.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
import os
import zipfile
from datetime import datetime, timezone
from typing import Optional

from configs.settings import APP_VERSION

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


NIST_FAMILIES = {
    "AC": "Access_Control",
    "AT": "Awareness_and_Training",
    "AU": "Audit_and_Accountability",
    "CA": "Security_Assessment",
    "CM": "Configuration_Management",
    "IA": "Identification_and_Authentication",
    "IR": "Incident_Response",
    "MA": "Maintenance",
    "MP": "Media_Protection",
    "PE": "Physical_Protection",
    "PS": "Personnel_Security",
    "RA": "Risk_Assessment",
    "SC": "System_and_Communications_Protection",
    "SI": "System_and_Information_Integrity",
}


def _gen_id(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()[:20]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ── Data loaders ──────────────────────────────────────────────────────────

def _load_org_profile(org_id: str, db: Session) -> dict:
    row = db.execute(text(
        "SELECT name, cage_code FROM organizations WHERE id = :o"
    ), {"o": org_id}).fetchone()
    return {"name": row.name if row else org_id, "cage_code": row.cage_code if row else ""}


def _load_ssp_sections(org_id: str, db: Session) -> list:
    return db.execute(text("""
        SELECT DISTINCT ON (s.control_id)
               s.id, s.control_id, s.implementation_status, s.narrative,
               c.title, c.points, SPLIT_PART(s.control_id, '.', 1) AS family
        FROM ssp_sections s
        JOIN controls c ON c.id = s.control_id
        WHERE s.org_id = :o
        ORDER BY s.control_id, s.version DESC
    """), {"o": org_id}).fetchall()


def _load_evidence(org_id: str, db: Session) -> list:
    return db.execute(text("""
        SELECT ea.id, ea.filename, ea.file_path, ea.sha256_hash, ea.state,
               ea.evidence_type, ea.source_system, ea.description, ea.mime_type
        FROM evidence_artifacts ea
        WHERE ea.org_id = :o
        ORDER BY ea.filename
    """), {"o": org_id}).fetchall()


def _load_evidence_control_links(org_id: str, db: Session) -> dict:
    rows = db.execute(text("""
        SELECT ecm.evidence_id, ecm.control_id
        FROM evidence_control_map ecm
        JOIN evidence_artifacts ea ON ea.id = ecm.evidence_id
        WHERE ea.org_id = :o
    """), {"o": org_id}).fetchall()
    links: dict[str, list[str]] = {}
    for r in rows:
        links.setdefault(r.evidence_id, []).append(r.control_id)
    return links


def _load_poam(org_id: str, db: Session) -> list:
    return db.execute(text("""
        SELECT p.id, p.control_id, p.weakness_description, p.remediation_plan,
               p.status, p.risk_level, p.scheduled_completion, p.source_type,
               c.title AS control_title, c.points
        FROM poam_items p
        JOIN controls c ON c.id = p.control_id
        WHERE p.org_id = :o
        ORDER BY c.points DESC, p.control_id
    """), {"o": org_id}).fetchall()


def _load_audit_log(db: Session) -> list:
    return db.execute(text("""
        SELECT id, timestamp, actor, actor_type, action, target_type,
               target_id, details, entry_hash
        FROM audit_log ORDER BY id ASC
    """)).fetchall()


def _load_latest_snapshot(org_id: str, db: Session):
    return db.execute(text("""
        SELECT * FROM assessment_snapshots
        WHERE org_id = :o ORDER BY created_at DESC LIMIT 1
    """), {"o": org_id}).fetchone()


def _load_claims(org_id: str, db: Session) -> list:
    return db.execute(text("""
        SELECT id, control_id, claim_text, claim_type, verification_status,
               confidence, source_sentence
        FROM claims WHERE org_id = :o ORDER BY control_id
    """), {"o": org_id}).fetchall()


def _load_observations(org_id: str, db: Session) -> list:
    return db.execute(text("""
        SELECT id, observation_text, source_type, source_id, control_ids,
               observation_type, confidence, observed_at
        FROM observations WHERE org_id = :o ORDER BY source_type
    """), {"o": org_id}).fetchall()


def _load_resolutions(org_id: str, db: Session) -> list:
    return db.execute(text("""
        SELECT r.id, r.claim_id, r.observation_id, r.relationship,
               r.confidence, r.reasoning, r.model_used
        FROM resolutions r WHERE r.org_id = :o ORDER BY r.relationship
    """), {"o": org_id}).fetchall()


def _load_objectives(control_id: str, db: Session) -> list:
    return db.execute(text("""
        SELECT id, description
        FROM assessment_objectives WHERE control_id = :c ORDER BY id
    """), {"c": control_id}).fetchall()


def _get_evidence_file_content(file_path: Optional[str]) -> Optional[bytes]:
    if not file_path:
        return None
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                return f.read()
    except Exception:
        logger.debug("Could not read evidence file: %s", file_path)
    return None


# ── SPRS scorecard PDF (fpdf2) ────────────────────────────────────────────

def _generate_sprs_pdf(org_id: str, org_name: str, db: Session) -> bytes:
    from src.scoring.sprs import SPRSCalculator
    try:
        from fpdf import FPDF
    except ImportError:
        return b"fpdf2 not available"

    calc = SPRSCalculator(org_id)
    result = calc.calculate()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"SPRS Scorecard - {org_name}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Generated: {now_str}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 36)
    pdf.cell(0, 20, f"{result.score} / {result.max_score}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "Range: -203 to 110  |  POA&M eligible: 88+  |  Certification target: 95+",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Control Status Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"  MET: {result.met_count}   NOT MET: {result.not_met_count}   "
                    f"PARTIAL: {result.partial_count}   NOT ASSESSED: {result.not_assessed_count}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    w1 = {1: 0, 3: 0, 5: 0}
    for c in result.controls:
        w1[c.points] = w1.get(c.points, 0) + 1
    pdf.cell(0, 6, f"  Weight distribution:  1-point: {w1.get(1,0)}  |  3-point: {w1.get(3,0)}  |  5-point: {w1.get(5,0)}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Family breakdown table
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Family Breakdown", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 9)
    col_w = [20, 60, 20, 20, 20, 20]
    headers = ["Family", "Name", "Total", "MET", "NOT MET", "PARTIAL"]
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 7, h, border=1)
    pdf.ln()

    family_data: dict[str, dict] = {}
    for c in result.controls:
        fam = c.family_abbrev or c.control_id.split(".")[0]
        bucket = family_data.setdefault(fam, {"total": 0, "met": 0, "not_met": 0, "partial": 0})
        bucket["total"] += 1
        sl = c.status_label.upper()
        if sl == "MET":
            bucket["met"] += 1
        elif sl in ("NOT MET", "NOT_MET"):
            bucket["not_met"] += 1
        elif sl in ("PARTIAL", "PARTIALLY MET"):
            bucket["partial"] += 1

    pdf.set_font("Helvetica", "", 9)
    for fam in sorted(family_data):
        d = family_data[fam]
        fname = NIST_FAMILIES.get(fam, fam)[:30]
        pdf.cell(col_w[0], 6, fam, border=1)
        pdf.cell(col_w[1], 6, fname, border=1)
        pdf.cell(col_w[2], 6, str(d["total"]), border=1, align="C")
        pdf.cell(col_w[3], 6, str(d["met"]), border=1, align="C")
        pdf.cell(col_w[4], 6, str(d["not_met"]), border=1, align="C")
        pdf.cell(col_w[5], 6, str(d["partial"]), border=1, align="C")
        pdf.ln()

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# ── Per-control markdown ──────────────────────────────────────────────────

def _generate_control_md(
    section, claims: list, resolutions: list,
    ev_links: dict, evidence_map: dict, poam_items: list,
    objectives: list,
) -> str:
    lines = [
        f"# {section.control_id} — {section.title}",
        f"",
        f"**Weight:** {section.points} points  ",
        f"**SSP Status:** {section.implementation_status}",
        "",
    ]

    if objectives:
        lines.append("## Assessment Objectives")
        for o in objectives:
            lines.append(f"- **{o.id}**: {o.description}")
        lines.append("")

    if section.narrative:
        lines.append("## SSP Narrative")
        lines.append(section.narrative)
        lines.append("")

    ctrl_claims = [c for c in claims if c.control_id == section.control_id]
    if ctrl_claims:
        lines.append("## Extracted Claims")
        for c in ctrl_claims:
            lines.append(f"- [{c.verification_status}] ({c.claim_type}) {c.claim_text}")
        lines.append("")

    ctrl_res = [r for r in resolutions if any(
        cl.id == r.claim_id for cl in ctrl_claims
    )]
    if ctrl_res:
        v = sum(1 for r in ctrl_res if r.relationship == "SUPPORTS")
        x = sum(1 for r in ctrl_res if r.relationship == "CONTRADICTS")
        u = sum(1 for r in ctrl_res if r.relationship == "UNRELATED")
        lines.append(f"## Resolution Summary")
        lines.append(f"SUPPORTS: {v}  |  CONTRADICTS: {x}  |  UNRELATED: {u}")
        lines.append("")

    ctrl_ev_ids = ev_links.get(section.control_id, [])
    if ctrl_ev_ids:
        lines.append("## Linked Evidence")
        for eid in ctrl_ev_ids:
            ev = evidence_map.get(eid)
            if ev:
                lines.append(f"- {ev.filename}  (state: {ev.state}, hash: {ev.sha256_hash or 'N/A'})")
        lines.append("")

    ctrl_poam = [p for p in poam_items if p.control_id == section.control_id]
    if ctrl_poam:
        lines.append("## Open POA&M Items")
        for p in ctrl_poam:
            lines.append(f"- [{p.status}] {p.weakness_description[:200]}")
        lines.append("")

    return "\n".join(lines)


# ── Family summary markdown ──────────────────────────────────────────────

def _generate_family_summary_md(
    family_code: str, sections: list, ev_links: dict,
) -> str:
    family_name = NIST_FAMILIES.get(family_code, family_code)
    lines = [
        f"# {family_code} — {family_name}",
        "",
        f"Controls in family: {len(sections)}",
        "",
        "| Control | Status | Weight | Evidence |",
        "|---------|--------|--------|----------|",
    ]
    for s in sections:
        ev_count = len(ev_links.get(s.control_id, []))
        lines.append(f"| {s.control_id} | {s.implementation_status} | {s.points}pt | {ev_count} artifacts |")
    lines.append("")
    return "\n".join(lines)


# ── README ────────────────────────────────────────────────────────────────

def _generate_readme(org_name: str, org_id: str, control_count: int,
                     evidence_count: int, created_at: str) -> str:
    return f"""# CMMC Level 2 Assessment Binder

**Organization:** {org_name}
**Org ID:** {org_id}
**Generated:** {created_at}
**Platform:** Intranest v{APP_VERSION}

---

## Contents

| Path | Description |
|------|-------------|
| `00_README.md` | This file |
| `01_SSP/` | System Security Plan (text summary, per-control narratives) |
| `02_POAM/` | Plan of Action & Milestones report |
| `03_SPRS_Scorecard.pdf` | One-page SPRS score breakdown |
| `04_Manifest.json` | SHA-256 hash manifest for all published evidence |
| `05_Manifest.csv` | Same manifest in CSV format |
| `06_Audit_Log.json` | Append-only hash-chained audit log |
| `07_Assessment_Snapshot.json` | Latest truth-model simulation results |
| `by_family/{{FAMILY}}/` | Per-family summary + per-control markdown with claims/evidence |
| `raw/` | Machine-readable JSON exports (claims, observations, resolutions, evidence index) |

## Recommended Review Order

1. **README** (this file) — understand structure
2. **SPRS Scorecard** — overall score and family breakdown
3. **SSP** — control-by-control implementation narratives
4. **by_family/** — deep-dive per control: objectives, claims, evidence, POA&M
5. **POA&M** — remediation plans for open gaps
6. **Manifest** — verify evidence integrity

## Integrity Verification

Every published evidence artifact has a SHA-256 hash computed at publish time.
The manifest lists each artifact's hash. The **package_hash** at the top of
`04_Manifest.json` is the SHA-256 of all individual hashes sorted alphabetically
and concatenated. To verify:

1. For each file listed in the manifest, compute its SHA-256 and compare.
2. Sort all hashes alphabetically, concatenate, and SHA-256 the result.
3. Compare with `package_hash` in the manifest.

Any discrepancy indicates the package or its contents have been modified since export.

---

*This package was generated by Intranest. Evidence integrity is verified via
SHA-256 hash manifest. {control_count} controls assessed, {evidence_count}
evidence artifacts included.*
"""


# ── Manifest builders ─────────────────────────────────────────────────────

def _build_manifest_entries(evidence: list, ev_links: dict) -> list[dict]:
    entries = []
    for ev in evidence:
        if not ev.sha256_hash:
            continue
        controls = ev_links.get(ev.id, [])
        entries.append({
            "evidence_id": ev.id,
            "filename":    ev.filename or "(unnamed)",
            "sha256":      ev.sha256_hash,
            "state":       ev.state,
            "type":        ev.evidence_type,
            "controls":    sorted(controls),
        })
    entries.sort(key=lambda e: e["sha256"])
    return entries


def _compute_package_hash(entries: list[dict]) -> str:
    concat = "".join(e["sha256"] for e in entries)
    return hashlib.sha256(concat.encode()).hexdigest()


# ── SSP text summary ──────────────────────────────────────────────────────

def _generate_ssp_text(org_name: str, sections: list) -> str:
    lines = [
        f"SYSTEM SECURITY PLAN — TEXT SUMMARY",
        f"Organization: {org_name}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Controls: {len(sections)}/110",
        "=" * 80, "",
    ]
    current_fam = None
    for s in sections:
        fam = s.family
        if fam != current_fam:
            current_fam = fam
            fname = NIST_FAMILIES.get(fam, fam)
            lines += ["", "=" * 70, f"  {fam} - {fname}", "=" * 70, ""]
        lines.append(f"--- {s.control_id} - {s.title} ({s.points}pts, {s.implementation_status}) ---")
        lines.append(s.narrative or "No narrative generated.")
        lines.append("")
    return "\n".join(lines)


# ── POA&M text report ─────────────────────────────────────────────────────

def _generate_poam_text(org_name: str, poam: list) -> str:
    lines = [
        "PLAN OF ACTION & MILESTONES (POA&M)",
        f"Organization: {org_name}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Total Items: {len(poam)}",
        "=" * 80, "",
    ]
    for p in poam:
        lines += [
            f"ID: {p.id}",
            f"Control: {p.control_id} - {p.control_title} ({p.points}pts)",
            f"Status: {p.status}  |  Risk: {p.risk_level}  |  Source: {p.source_type or 'ASSESSMENT'}",
            f"Weakness: {p.weakness_description}",
            f"Remediation: {p.remediation_plan}",
            f"Deadline: {p.scheduled_completion}",
            "-" * 40, "",
        ]
    return "\n".join(lines)


# ── Main builder ──────────────────────────────────────────────────────────

def build_binder(org_id: str, db: Session, user_id: Optional[str] = None) -> bytes:
    """Build the full C3PAO-ready ZIP in memory and return the bytes."""
    now = datetime.now(timezone.utc)
    now_str = now.strftime("%Y-%m-%d %H:%M UTC")

    profile = _load_org_profile(org_id, db)
    org_name = profile["name"]

    sections     = _load_ssp_sections(org_id, db)
    evidence     = _load_evidence(org_id, db)
    ev_ctrl      = _load_evidence_control_links(org_id, db)
    poam         = _load_poam(org_id, db)
    audit_rows   = _load_audit_log(db)
    snapshot_row = _load_latest_snapshot(org_id, db)
    claims       = _load_claims(org_id, db)
    observations = _load_observations(org_id, db)
    resolutions  = _load_resolutions(org_id, db)

    # Reverse mapping: control_id → [evidence_ids]
    ctrl_ev: dict[str, list[str]] = {}
    for eid, cids in ev_ctrl.items():
        for cid in cids:
            ctrl_ev.setdefault(cid, []).append(eid)

    evidence_map = {e.id: e for e in evidence}

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:

        # 00 README
        readme = _generate_readme(org_name, org_id, len(sections), len(evidence), now_str)
        zf.writestr("00_README.md", readme)

        # 01 SSP
        if sections:
            zf.writestr("01_SSP/SSP_Text_Summary.txt", _generate_ssp_text(org_name, sections))

        # 02 POAM
        if poam:
            zf.writestr("02_POAM/POAM_Report.txt", _generate_poam_text(org_name, poam))
        else:
            zf.writestr("02_POAM/NO_POAM_ITEMS.txt", "No POA&M items exist for this organization.\n")

        # 03 SPRS Scorecard PDF
        try:
            pdf_bytes = _generate_sprs_pdf(org_id, org_name, db)
            zf.writestr("03_SPRS_Scorecard.pdf", pdf_bytes)
        except Exception:
            logger.exception("SPRS PDF generation failed")
            zf.writestr("03_SPRS_Scorecard_UNAVAILABLE.txt", "SPRS scorecard generation failed.\n")

        # 04/05 Manifest
        manifest_entries = _build_manifest_entries(evidence, ev_ctrl)
        pkg_hash = _compute_package_hash(manifest_entries) if manifest_entries else None
        manifest_obj = {
            "generated_at":   now.isoformat(),
            "organization":   org_name,
            "org_id":         org_id,
            "package_hash":   pkg_hash,
            "artifact_count": len(manifest_entries),
            "entries":        manifest_entries,
        }
        zf.writestr("04_Manifest.json", json.dumps(manifest_obj, indent=2))

        csv_buf = io.StringIO()
        writer = csv.writer(csv_buf)
        writer.writerow(["evidence_id", "filename", "sha256", "state", "type", "controls"])
        for e in manifest_entries:
            writer.writerow([e["evidence_id"], e["filename"], e["sha256"],
                             e["state"], e["type"], ";".join(e["controls"])])
        zf.writestr("05_Manifest.csv", csv_buf.getvalue())

        # 06 Audit log
        audit_data = []
        for a in audit_rows:
            details = a.details
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except Exception:
                    pass
            audit_data.append({
                "id": a.id, "timestamp": str(a.timestamp), "actor": a.actor,
                "actor_type": a.actor_type, "action": a.action,
                "target_type": a.target_type, "target_id": a.target_id,
                "details": details, "entry_hash": a.entry_hash,
            })
        zf.writestr("06_Audit_Log.json", json.dumps(audit_data, indent=2))

        # 07 Assessment snapshot
        if snapshot_row:
            snap = dict(snapshot_row._mapping)
            for k, v in snap.items():
                if isinstance(v, datetime):
                    snap[k] = v.isoformat()
            zf.writestr("07_Assessment_Snapshot.json", json.dumps(snap, indent=2, default=str))
        else:
            zf.writestr("07_Assessment_Snapshot.json",
                         json.dumps({"note": "No assessment simulation has been run yet."}, indent=2))

        # by_family/
        sections_by_fam: dict[str, list] = {}
        for s in sections:
            sections_by_fam.setdefault(s.family, []).append(s)

        for fam_code in sorted(NIST_FAMILIES):
            fam_name = NIST_FAMILIES[fam_code]
            fam_dir = f"by_family/{fam_code}_{fam_name}"
            fam_sections = sections_by_fam.get(fam_code, [])

            summary_md = _generate_family_summary_md(fam_code, fam_sections, ctrl_ev)
            zf.writestr(f"{fam_dir}/_family_summary.md", summary_md)

            for s in fam_sections:
                objectives = _load_objectives(s.control_id, db)
                ctrl_md = _generate_control_md(
                    s, claims, resolutions, ctrl_ev, evidence_map, poam, objectives,
                )
                safe_cid = s.control_id.replace(".", "_")
                zf.writestr(f"{fam_dir}/{safe_cid}/_control.md", ctrl_md)

                # Include linked evidence files
                for eid in ctrl_ev.get(s.control_id, []):
                    ev = evidence_map.get(eid)
                    if not ev:
                        continue
                    content = _get_evidence_file_content(ev.file_path)
                    if content:
                        prefix = (ev.sha256_hash or "")[:8]
                        safe_fn = f"{prefix}_{ev.filename}" if prefix else ev.filename
                        zf.writestr(f"{fam_dir}/{safe_cid}/{safe_fn}", content)

        # raw/
        zf.writestr("raw/claims.json", json.dumps(
            [{"id": c.id, "control_id": c.control_id, "claim_text": c.claim_text,
              "claim_type": c.claim_type, "verification_status": c.verification_status,
              "confidence": c.confidence}
             for c in claims], indent=2))

        zf.writestr("raw/observations.json", json.dumps(
            [{"id": o.id, "observation_text": o.observation_text,
              "source_type": o.source_type, "source_id": o.source_id,
              "control_ids": list(o.control_ids) if o.control_ids else [],
              "observation_type": o.observation_type, "confidence": o.confidence,
              "observed_at": o.observed_at.isoformat() if o.observed_at else None}
             for o in observations], indent=2))

        zf.writestr("raw/resolutions.json", json.dumps(
            [{"id": r.id, "claim_id": r.claim_id, "observation_id": r.observation_id,
              "relationship": r.relationship, "confidence": r.confidence,
              "reasoning": r.reasoning, "model_used": r.model_used}
             for r in resolutions], indent=2))

        zf.writestr("raw/evidence_index.json", json.dumps(
            [{"id": e.id, "filename": e.filename, "state": e.state,
              "evidence_type": e.evidence_type, "source_system": e.source_system,
              "sha256_hash": e.sha256_hash, "description": e.description,
              "controls": ev_ctrl.get(e.id, [])}
             for e in evidence], indent=2))

    return buf.getvalue()


# ── Preview (no generation) ──────────────────────────────────────────────

def preview_binder(org_id: str, db: Session) -> dict:
    ev_count = db.execute(
        text("SELECT COUNT(*) FROM evidence_artifacts WHERE org_id = :o"),
        {"o": org_id},
    ).scalar() or 0
    ctrl_count = db.execute(text("""
        SELECT COUNT(DISTINCT control_id) FROM ssp_sections WHERE org_id = :o
    """), {"o": org_id}).scalar() or 0
    has_snapshot = db.execute(text("""
        SELECT 1 FROM assessment_snapshots WHERE org_id = :o LIMIT 1
    """), {"o": org_id}).fetchone() is not None
    claim_count = db.execute(
        text("SELECT COUNT(*) FROM claims WHERE org_id = :o"), {"o": org_id},
    ).scalar() or 0

    return {
        "evidence_count":          int(ev_count),
        "control_count":           int(ctrl_count),
        "family_count":            14,
        "claim_count":             int(claim_count),
        "has_assessment_snapshot":  has_snapshot,
        "estimated_size_bytes":    max(50_000, int(ev_count) * 20_000 + int(ctrl_count) * 5_000),
    }
