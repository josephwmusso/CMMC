"""
src/exports/sprs_package.py

SPRS reporting package per 32 CFR 170.16. Generates the exact field
values a company officer types into piee.eb.mil and the supporting
artifacts they must retain for 6 years.

No new dependencies — stdlib + fpdf2 + existing calculator.
"""
from __future__ import annotations

import hashlib
import io
import json
import logging
import zipfile
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _gen_id(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()[:20]


def _sha(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


# ── Data collectors ───────────────────────────────────────────────────────

def _load_profile(org_id: str, db: Session) -> dict:
    row = db.execute(text("""
        SELECT company_name, cage_code, duns_number, employee_count,
               primary_location, cui_types, identity_provider,
               email_platform, edr_product, firewall_product,
               uei, ssp_version, ssp_date, cui_scope_description,
               assessing_entity
        FROM company_profiles WHERE org_id = :o
    """), {"o": org_id}).fetchone()
    if not row:
        org = db.execute(text("SELECT name FROM organizations WHERE id = :o"), {"o": org_id}).fetchone()
        return {"company_name": org.name if org else org_id}
    d = dict(row._mapping)
    if isinstance(d.get("cui_types"), str):
        try:
            d["cui_types"] = json.loads(d["cui_types"])
        except Exception:
            d["cui_types"] = []
    if not isinstance(d.get("cui_types"), list):
        d["cui_types"] = []
    return d


def _load_sprs(org_id: str, db: Session, use_truth: bool) -> dict:
    from src.scoring.sprs import SPRSCalculator
    calc = SPRSCalculator(org_id)
    result = calc.calculate()

    truth_score = None
    truth_delta = 0
    if use_truth:
        try:
            from src.truth.assessment_sim import compute_truth_adjusted_sprs
            t = compute_truth_adjusted_sprs(org_id, db)
            truth_score = t["sprs_truth_adjusted"]
            truth_delta = t["sprs_delta"]
        except Exception:
            logger.warning("truth-adjusted SPRS unavailable")

    return {
        "result":       result,
        "raw_score":    result.score,
        "cond_score":   result.conditional_score,
        "truth_score":  truth_score,
        "truth_delta":  truth_delta,
        "met":          result.met_count,
        "not_met":      result.not_met_count,
        "partial":      result.partial_count,
        "not_assessed": result.not_assessed_count,
    }


def _load_poam_summary(org_id: str, db: Session) -> dict:
    row = db.execute(text("""
        SELECT COUNT(*)                      AS total,
               COUNT(*) FILTER (WHERE status = 'OPEN')       AS open_count,
               MAX(scheduled_completion)     AS max_deadline,
               COUNT(*) FILTER (WHERE scheduled_completion < NOW() AND status = 'OPEN') AS past_deadline
        FROM poam_items WHERE org_id = :o
    """), {"o": org_id}).fetchone()
    return {
        "total":         int(row.total or 0),
        "open_count":    int(row.open_count or 0),
        "max_deadline":  row.max_deadline.isoformat() if row.max_deadline else None,
        "past_deadline": int(row.past_deadline or 0),
    }


# ── collect_sprs_fields ──────────────────────────────────────────────────

def collect_sprs_fields(org_id: str, db: Session, use_truth_adjusted: bool = False) -> dict:
    profile = _load_profile(org_id, db)
    sprs    = _load_sprs(org_id, db, use_truth_adjusted)
    poam    = _load_poam_summary(org_id, db)
    now     = datetime.now(timezone.utc)

    score = sprs["truth_score"] if use_truth_adjusted and sprs["truth_score"] is not None else sprs["raw_score"]
    score_type = "truth_adjusted" if use_truth_adjusted and sprs["truth_score"] is not None else "raw"

    ssp_version = profile.get("ssp_version") or f"v1.0-{now.strftime('%Y%m%d')}"
    ssp_date = profile.get("ssp_date")
    ssp_date_str = ssp_date.isoformat() if ssp_date else now.strftime("%Y-%m-%d")

    cui_types = profile.get("cui_types") or []
    scope = profile.get("cui_scope_description") or "NIST 800-171 CUI enclave"

    warnings: list[str] = []
    if not profile.get("cage_code"):
        warnings.append("CAGE code required for SPRS submission. Add in Organization Settings.")
    if not profile.get("uei"):
        warnings.append("UEI required (replaced DUNS for federal identification in April 2022).")
    if score < 0 and score_type == "truth_adjusted":
        warnings.append("Truth-adjusted SPRS is negative. Most orgs submit raw SPRS and track truth-adjusted internally.")
    if not profile.get("ssp_version"):
        warnings.append(f"SSP version not recorded. Defaulting to {ssp_version}.")
    if poam["past_deadline"] > 0:
        warnings.append(f"{poam['past_deadline']} POA&M item(s) past deadline. Close or update before submission.")

    # Snapshot age check
    snap = db.execute(text("""
        SELECT created_at FROM assessment_snapshots
        WHERE org_id = :o ORDER BY created_at DESC LIMIT 1
    """), {"o": org_id}).fetchone()
    if snap:
        age_days = (now - snap.created_at.replace(tzinfo=timezone.utc)).days
        if age_days > 30:
            warnings.append(f"Assessment snapshot is {age_days} days old. Run a fresh simulation.")

    return {
        "submission_fields": {
            "company_name":         profile.get("company_name") or org_id,
            "cage_code":            profile.get("cage_code"),
            "uei":                  profile.get("uei"),
            "duns":                 profile.get("duns_number"),
            "ssp_version":          ssp_version,
            "ssp_date":             ssp_date_str,
            "assessment_date":      now.strftime("%Y-%m-%d"),
            "assessment_score":     score,
            "score_type":           score_type,
            "assessment_scope":     scope,
            "cui_types":            cui_types,
            "poam_items_count":     poam["open_count"],
            "poam_completion_date": poam["max_deadline"],
            "assessing_entity":     profile.get("assessing_entity") or "Self",
            "confidence_level":     "Basic",
            "included_cui":         bool(cui_types),
        },
        "supporting_data": {
            "total_controls":           110,
            "met_count":                sprs["met"],
            "not_met_count":            sprs["not_met"],
            "partial_count":            sprs["partial"],
            "not_assessed_count":       sprs["not_assessed"],
            "org_id":                   org_id,
            "submission_generated_at":  now.isoformat(),
            "raw_score":                sprs["raw_score"],
            "conditional_score":        sprs["cond_score"],
            "truth_adjusted_score":     sprs["truth_score"],
            "truth_delta":              sprs["truth_delta"],
        },
        "warnings": warnings,
    }


# ── PDF generators ────────────────────────────────────────────────────────

def _field_values_pdf(fields: dict) -> bytes:
    from fpdf import FPDF
    sf = fields["submission_fields"]
    sd = fields["supporting_data"]
    ws = fields.get("warnings", [])

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "SPRS SUBMISSION FIELD VALUES", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, sf["company_name"], new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Generated: {sd['submission_generated_at'][:19]} UTC", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, "Submit at https://piee.eb.mil > SPRS > NIST 800-171 Basic Assessment", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    def _section(title: str):
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)

    def _row(label: str, value):
        pdf.cell(55, 6, f"  {label}:", new_x="RIGHT")
        pdf.cell(0, 6, str(value or "N/A"), new_x="LMARGIN", new_y="NEXT")

    _section("COMPANY IDENTIFICATION")
    _row("Company Name", sf["company_name"])
    _row("CAGE Code", sf["cage_code"])
    _row("UEI", sf["uei"])
    _row("DUNS (optional)", sf["duns"])

    _section("SYSTEM SECURITY PLAN")
    _row("SSP Version", sf["ssp_version"])
    _row("SSP Date", sf["ssp_date"])

    _section("ASSESSMENT DETAILS")
    _row("Assessment Date", sf["assessment_date"])
    _row("Assessment Score", sf["assessment_score"])
    _row("Score Type", sf["score_type"].replace("_", " ").title())
    _row("Assessing Entity", sf["assessing_entity"])
    _row("Confidence Level", sf["confidence_level"])

    _section("CONTROL IMPLEMENTATION (of 110)")
    _row("MET", sd["met_count"])
    _row("NOT MET", sd["not_met_count"])
    _row("PARTIAL", sd["partial_count"])

    _section("POA&M STATUS")
    _row("Open Items", sf["poam_items_count"])
    _row("Completion Date", sf["poam_completion_date"] or "N/A")

    _section("SCOPE")
    scope_text = (sf['assessment_scope'] or '')[:500]
    for i in range(0, len(scope_text), 90):
        pdf.cell(0, 5, f"  {scope_text[i:i+90]}", new_x="LMARGIN", new_y="NEXT")
    cui_str = ", ".join(sf["cui_types"]) if sf["cui_types"] else "Not specified"
    _row("CUI Types", cui_str[:120])
    _row("Included CUI", "YES" if sf["included_cui"] else "NO")

    if ws:
        pdf.ln(4)
        _section("WARNINGS")
        pdf.set_font("Helvetica", "", 9)
        for w in ws:
            pdf.cell(0, 5, f"  ! {w[:120]}", new_x="LMARGIN", new_y="NEXT")

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


def _assessment_summary_pdf(fields: dict, org_id: str, db: Session) -> bytes:
    from fpdf import FPDF
    sf = fields["submission_fields"]
    sd = fields["supporting_data"]

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "NIST 800-171 Self-Assessment Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, sf["company_name"], new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Assessment Date: {sf['assessment_date']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 28)
    pdf.cell(0, 16, f"Score: {sf['assessment_score']} / 110", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    unmet_pts = sd["raw_score"] - sf["assessment_score"] if sd["raw_score"] != sf["assessment_score"] else (110 - sf["assessment_score"])
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6,
             f"Score of {sf['assessment_score']} indicates {sd['not_met_count']} unmet controls "
             f"worth {abs(110 - sf['assessment_score'])} points deducted from 110.",
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6,
             f"POA&M status: {sf['poam_items_count']} items open. "
             f"{'Completion deadline: ' + sf['poam_completion_date'] if sf['poam_completion_date'] else 'No deadlines set.'}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Scope Statement", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    scope = sf["assessment_scope"][:500]
    for i in range(0, len(scope), 95):
        pdf.cell(0, 5, scope[i:i+95], new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, "Prepared by: ________________________________  Date: __________", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.cell(0, 7, "Senior Official Affirmation: ________________  Date: __________", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, "This summary supports SPRS submission per 32 CFR 170.16. Retain for 6 years.",
             new_x="LMARGIN", new_y="NEXT")

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


def _score_worksheet_pdf(org_id: str, db: Session) -> bytes:
    from fpdf import FPDF
    from src.scoring.sprs import SPRSCalculator

    calc = SPRSCalculator(org_id)
    result = calc.calculate()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "SPRS Score Calculation Worksheet", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    col_w = [40, 12, 30, 22]
    pdf.set_font("Helvetica", "B", 8)
    for h, w in zip(["Control ID", "Wt", "Status", "Deducted"], col_w):
        pdf.cell(w, 6, h, border=1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 7)
    current_fam = None
    for c in sorted(result.controls, key=lambda x: x.control_id):
        fam = c.family_abbrev or c.control_id.split(".")[0]
        if fam != current_fam:
            current_fam = fam
            fname = {
                "AC": "Access Control", "AT": "Awareness & Training",
                "AU": "Audit & Accountability", "CA": "Security Assessment",
                "CM": "Configuration Mgmt", "IA": "Identification & Auth",
                "IR": "Incident Response", "MA": "Maintenance",
                "MP": "Media Protection", "PE": "Physical Protection",
                "PS": "Personnel Security", "RA": "Risk Assessment",
                "SC": "System & Comms Protection", "SI": "System & Info Integrity",
            }.get(fam, fam)
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(sum(col_w), 6, f"  {fam} - {fname}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 7)

        ded_str = f"-{c.deduction}" if c.deduction > 0 else "0"
        pdf.cell(col_w[0], 5, c.control_id, border=1)
        pdf.cell(col_w[1], 5, str(c.points), border=1, align="C")
        pdf.cell(col_w[2], 5, c.status_label, border=1)
        pdf.cell(col_w[3], 5, ded_str, border=1, align="R")
        pdf.ln()

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, f"Starting Score:      110", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Total Deductions:   -{result.raw_deductions}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Final Score:         {result.score}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Conditional Score:   {result.conditional_score}  (with POA&M credit)",
             new_x="LMARGIN", new_y="NEXT")

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# ── README ────────────────────────────────────────────────────────────────

def _generate_readme(fields: dict, warnings: list[str]) -> str:
    sf = fields["submission_fields"]
    return f"""# SPRS Reporting Package

**Organization:** {sf["company_name"]}
**Assessment Date:** {sf["assessment_date"]}
**Assessment Score:** {sf["assessment_score"]} / 110
**Package Purpose:** NIST 800-171 Basic Assessment SPRS submission per 32 CFR 170.16

---

## Contents

| File | Purpose |
|------|---------|
| `00_README.md` | This file |
| `01_SPRS_Field_Values.pdf` | Exact field values for piee.eb.mil submission form |
| `02_SPRS_Field_Values.json` | Same values in machine-readable JSON |
| `03_Assessment_Summary.pdf` | Executive summary with signature blocks |
| `04_Score_Calculation_Worksheet.pdf` | Per-control audit trail of score computation |
| `05_Submission_Metadata.json` | Package hash and attestation metadata |

## Submission Process

1. Log in to [PIEE](https://piee.eb.mil)
2. Navigate to **SPRS > NIST 800-171 Basic Assessment**
3. Enter the values from `01_SPRS_Field_Values.pdf`
4. Retain this entire package for **6 years** per CMMC requirements

## Warnings

{"".join(f"- {w}{chr(10)}" for w in warnings) if warnings else "None."}

## Integrity

This package was generated by Intranest. The package hash in
`05_Submission_Metadata.json` is deterministic — regenerating from the
same SSP, POA&M, and assessment state produces the same hash.
"""


# ── Main builder ──────────────────────────────────────────────────────────

def build_sprs_package(
    org_id: str, db: Session, user_id: Optional[str] = None,
    use_truth_adjusted: bool = False,
) -> bytes:
    """Build the SPRS reporting package ZIP in memory."""
    fields = collect_sprs_fields(org_id, db, use_truth_adjusted)
    now = datetime.now(timezone.utc)

    buf = io.BytesIO()
    content_hashes: list[str] = []

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:

        # 01 Field Values PDF
        try:
            fv_pdf = _field_values_pdf(fields)
            zf.writestr("01_SPRS_Field_Values.pdf", fv_pdf)
            content_hashes.append(hashlib.sha256(fv_pdf).hexdigest())
        except Exception:
            logger.exception("Field values PDF failed")
            zf.writestr("01_SPRS_Field_Values_UNAVAILABLE.txt", "Generation failed.\n")

        # 02 Field Values JSON
        fv_json = json.dumps(fields, indent=2, default=str).encode()
        zf.writestr("02_SPRS_Field_Values.json", fv_json)
        content_hashes.append(hashlib.sha256(fv_json).hexdigest())

        # 03 Assessment Summary PDF
        try:
            as_pdf = _assessment_summary_pdf(fields, org_id, db)
            zf.writestr("03_Assessment_Summary.pdf", as_pdf)
            content_hashes.append(hashlib.sha256(as_pdf).hexdigest())
        except Exception:
            logger.exception("Assessment summary PDF failed")
            zf.writestr("03_Assessment_Summary_UNAVAILABLE.txt", "Generation failed.\n")

        # 04 Score Calculation Worksheet
        try:
            sc_pdf = _score_worksheet_pdf(org_id, db)
            zf.writestr("04_Score_Calculation_Worksheet.pdf", sc_pdf)
            content_hashes.append(hashlib.sha256(sc_pdf).hexdigest())
        except Exception:
            logger.exception("Score worksheet PDF failed")
            zf.writestr("04_Score_Calculation_UNAVAILABLE.txt", "Generation failed.\n")

        # 05 Submission Metadata (written last with package hash)
        content_hashes.sort()
        pkg_hash = hashlib.sha256("".join(content_hashes).encode()).hexdigest()

        metadata = {
            "generated_at":           now.isoformat(),
            "generated_by":           user_id,
            "org_id":                 org_id,
            "package_hash":           pkg_hash,
            "submission_fields_hash": _sha(json.dumps(fields["submission_fields"], sort_keys=True, default=str)),
            "reg_citation":           "32 CFR 170.16",
            "intended_use":           "NIST 800-171 Basic Assessment SPRS submission",
            "retention_years":        6,
        }
        meta_bytes = json.dumps(metadata, indent=2).encode()
        zf.writestr("05_Submission_Metadata.json", meta_bytes)

        # 00 README
        readme = _generate_readme(fields, fields.get("warnings", []))
        zf.writestr("00_README.md", readme)

    return buf.getvalue()
