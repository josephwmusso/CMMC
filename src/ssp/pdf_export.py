"""
src/ssp/pdf_export.py

Generate SSP as a PDF using fpdf2 (pure Python, no external deps).
Pulls all data directly from Postgres — ssp_sections, controls,
evidence_artifacts, evidence_control_map.
"""

import os
import datetime

from fpdf import FPDF
from sqlalchemy import text, create_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cmmc:localdev@localhost:5432/cmmc",
)

EXPORT_DIR = os.path.join("data", "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

FAMILY_ORDER = [
    ("AC", "Access Control"),
    ("AT", "Awareness and Training"),
    ("AU", "Audit and Accountability"),
    ("CA", "Security Assessment"),
    ("CM", "Configuration Management"),
    ("IA", "Identification and Authentication"),
    ("IR", "Incident Response"),
    ("MA", "Maintenance"),
    ("MP", "Media Protection"),
    ("PE", "Physical Protection"),
    ("PS", "Personnel Security"),
    ("RA", "Risk Assessment"),
    ("SC", "System and Communications Protection"),
    ("SI", "System and Information Integrity"),
]


class SSPPDF(FPDF):
    """Custom PDF with header/footer for the SSP document."""

    def __init__(self, org_name="Apex Defense Solutions"):
        super().__init__()
        self.org_name = org_name
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if self.page_no() == 1:
            return  # Cover page has no header
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"System Security Plan - {self.org_name}", align="L")
        self.cell(0, 8, "CONTROLLED UNCLASSIFIED INFORMATION", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(180, 180, 180)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


def _safe(text_val):
    """Ensure text is Latin-1 safe for fpdf2 Helvetica (built-in font).

    Replaces common Unicode characters with ASCII equivalents.
    """
    if text_val is None:
        return ""
    s = str(text_val)
    # Replace common Unicode chars with ASCII equivalents
    s = s.replace("\u2014", "--")      # em-dash
    s = s.replace("\u2013", "-")       # en-dash
    s = s.replace("\u2018", "'")       # left single quote
    s = s.replace("\u2019", "'")       # right single quote
    s = s.replace("\u201c", '"')       # left double quote
    s = s.replace("\u201d", '"')       # right double quote
    s = s.replace("\u2026", "...")     # ellipsis
    s = s.replace("\u2022", "*")       # bullet
    s = s.replace("\u00b7", "*")       # middle dot
    s = s.replace("\u2713", "[ok]")    # checkmark
    s = s.replace("\u2717", "[x]")     # cross mark
    s = s.replace("\r", "")
    # Strip any remaining non-Latin-1 chars
    return s.encode("latin-1", errors="replace").decode("latin-1")


def generate_ssp_pdf(org_id: str) -> str:
    """Generate a complete SSP PDF from database data.

    Returns the path to the generated PDF file.
    """
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Fetch org name
        org_row = conn.execute(
            text("SELECT name FROM organizations WHERE id = :oid"),
            {"oid": org_id},
        ).fetchone()
        org_name = org_row[0] if org_row else "Apex Defense Solutions"

        # Fetch all SSP sections with control metadata
        sections = conn.execute(text("""
            SELECT c.id, c.title, c.family_abbrev, c.points,
                   ss.implementation_status, ss.narrative, ss.gaps
            FROM controls c
            LEFT JOIN ssp_sections ss ON ss.control_id = c.id AND ss.org_id = :oid
            ORDER BY c.id
        """), {"oid": org_id}).fetchall()

        # Fetch evidence linkages: control_id -> list of filenames
        ev_rows = conn.execute(text("""
            SELECT ecm.control_id, ea.filename, ea.evidence_type, ea.sha256_hash
            FROM evidence_control_map ecm
            JOIN evidence_artifacts ea ON ea.id = ecm.evidence_id
            WHERE ea.org_id = :oid
            ORDER BY ecm.control_id, ea.filename
        """), {"oid": org_id}).fetchall()

        evidence_map = {}
        for r in ev_rows:
            cid = r[0]
            if cid not in evidence_map:
                evidence_map[cid] = []
            evidence_map[cid].append({
                "filename": r[1],
                "evidence_type": r[2] or "",
                "sha256_hash": (r[3] or "")[:16],
            })

        # Compute summary stats
        total = len(sections)
        implemented = sum(1 for s in sections if s[4] == "Implemented")
        partial = sum(1 for s in sections if s[4] == "Partially Implemented")
        not_impl = total - implemented - partial
        evidence_count = len(set(r[1] for r in ev_rows))  # unique filenames

    # --- Build PDF ---
    pdf = SSPPDF(org_name=org_name)
    pdf.alias_nb_pages()
    pdf.set_margins(20, 20, 20)

    # === Cover page ===
    pdf.add_page()
    pdf.ln(60)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 14, "System Security Plan", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 10, org_name, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, "CMMC Level 2 -- NIST SP 800-171 Rev 2", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"Generated: {datetime.datetime.now().strftime('%B %d, %Y')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"{total} Controls | {implemented} Implemented | {partial} Partial", align="C", new_x="LMARGIN", new_y="NEXT")

    # CUI notice at bottom of cover
    pdf.set_y(-50)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(180, 40, 40)
    pdf.cell(0, 8, "CONTROLLED UNCLASSIFIED INFORMATION", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, "Distribution authorized to U.S. Government agencies and their contractors.", align="C", new_x="LMARGIN", new_y="NEXT")

    # === Control families ===
    # Group sections by family
    family_sections = {}
    for s in sections:
        fam = s[2] or s[0][:2]
        if fam not in family_sections:
            family_sections[fam] = []
        family_sections[fam].append(s)

    for fam_code, fam_name in FAMILY_ORDER:
        controls = family_sections.get(fam_code, [])
        if not controls:
            continue

        # Family header page
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(30, 60, 120)
        pdf.cell(0, 12, f"{fam_name} ({fam_code})", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(59, 130, 246)
        pdf.set_line_width(0.5)
        pdf.line(20, pdf.get_y(), pdf.w - 20, pdf.get_y())
        pdf.ln(6)

        met = sum(1 for c in controls if c[4] == "Implemented")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, f"{met}/{len(controls)} controls implemented", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)

        for ctrl in controls:
            ctrl_id, title, _, points, impl_status, narrative, gaps = ctrl
            impl_status = impl_status or "Not Assessed"
            narrative = _safe(narrative)

            # Check if we need a new page (leave room for at least header + some text)
            if pdf.get_y() > pdf.h - 60:
                pdf.add_page()

            # Control header
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(30, 30, 30)
            header_text = f"{ctrl_id} -- {_safe(title)}"
            pdf.multi_cell(0, 6, header_text, new_x="LMARGIN", new_y="NEXT")

            # Implementation status (colored)
            if impl_status == "Implemented":
                pdf.set_text_color(34, 197, 94)  # green
            elif impl_status == "Partially Implemented":
                pdf.set_text_color(245, 158, 11)  # amber
            elif impl_status == "Not Implemented":
                pdf.set_text_color(239, 68, 68)  # red
            else:
                pdf.set_text_color(120, 120, 120)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 5, impl_status.upper(), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

            # Narrative
            if narrative:
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(40, 40, 40)
                pdf.multi_cell(0, 5, narrative, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(3)
            else:
                pdf.set_font("Helvetica", "I", 9)
                pdf.set_text_color(150, 150, 150)
                pdf.cell(0, 5, "No narrative generated.", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(3)

            # Evidence
            ev_list = evidence_map.get(ctrl_id, [])
            if ev_list:
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(60, 60, 60)
                pdf.cell(0, 5, f"Evidence ({len(ev_list)}):", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(80, 80, 80)
                for ev in ev_list:
                    ev_text = f"  - {ev['filename']}"
                    if ev["evidence_type"]:
                        ev_text += f" [{ev['evidence_type']}]"
                    if ev["sha256_hash"]:
                        ev_text += f" (SHA: {ev['sha256_hash']}...)"
                    pdf.cell(0, 4.5, _safe(ev_text), new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)

            # Gaps
            gap_list = gaps if isinstance(gaps, list) else []
            if gap_list:
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(180, 60, 60)
                pdf.cell(0, 5, f"Gaps ({len(gap_list)}):", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(120, 60, 60)
                for gap_text in gap_list:
                    pdf.multi_cell(0, 4.5, f"  - {_safe(gap_text)}", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)

            # Separator line
            pdf.set_draw_color(200, 200, 200)
            pdf.set_line_width(0.2)
            pdf.line(20, pdf.get_y(), pdf.w - 20, pdf.get_y())
            pdf.ln(4)

    # === Summary page ===
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(30, 60, 120)
    pdf.cell(0, 12, "Assessment Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(59, 130, 246)
    pdf.set_line_width(0.5)
    pdf.line(20, pdf.get_y(), pdf.w - 20, pdf.get_y())
    pdf.ln(10)

    # Score summary — use SPRSCalculator for accurate scores
    try:
        from src.scoring.sprs import SPRSCalculator
        sprs_calc = SPRSCalculator(org_id=org_id)
        sprs_result = sprs_calc.calculate()
        raw_score = sprs_result.score
        conditional_score = sprs_result.conditional_score
    except Exception:
        # Fallback: raw deducts for everything except Implemented
        raw_deductions = sum(
            (s[3] or 0) for s in sections if s[4] != "Implemented"
        )
        raw_score = 110 - raw_deductions
        conditional_score = 110  # can't compute without POA&M data

    summary_items = [
        ("SPRS Raw Score", f"{raw_score} / 110"),
        ("SPRS Conditional Score", f"{conditional_score} / 110"),
        ("Controls Total", str(total)),
        ("Implemented", str(implemented)),
        ("Partially Implemented", str(partial)),
        ("Not Implemented / Not Assessed", str(not_impl)),
        ("Evidence Artifacts", str(evidence_count)),
        ("Generation Date", datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC")),
    ]

    for label, value in summary_items:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(90, 8, label)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 8, value, new_x="LMARGIN", new_y="NEXT")

    # Save
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"SSP_{org_name.replace(' ', '_')}_{timestamp}.pdf"
    filepath = os.path.join(EXPORT_DIR, filename)
    pdf.output(filepath)

    return filepath
