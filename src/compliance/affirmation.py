"""
src/compliance/affirmation.py

Annual senior-official affirmation per 32 CFR 170.22. Tracks, records,
and generates PDF certificates for each affirmation. No LLM — pure
date math + fpdf2 PDF generation.

Status derivation (from ``expires_at`` of latest affirmation):
  CURRENT        — expires_at > now + 30 days
  DUE_SOON       — now + 30 days >= expires_at > now
  OVERDUE        — expires_at <= now
  NEVER_AFFIRMED — no affirmation exists
"""
from __future__ import annotations

import hashlib
import io
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_DUE_SOON_DAYS = 30


def _gen_id(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()[:20]


def _audit(db: Session, *, actor: str, action: str, target_id: str, details: dict) -> None:
    try:
        from src.evidence.state_machine import create_audit_entry
        create_audit_entry(
            db=db, actor=actor, actor_type="user", action=action,
            target_type="affirmation", target_id=target_id, details=details,
        )
    except Exception:
        logger.exception("audit %s failed", action)


def _safe_user_fk(db: Session, uid: Optional[str]) -> Optional[str]:
    if not uid:
        return None
    r = db.execute(text("SELECT 1 FROM users WHERE id = :id"), {"id": uid}).fetchone()
    return uid if r else None


# ── Status ────────────────────────────────────────────────────────────────

def _derive_status(expires_at: Optional[datetime]) -> tuple[str, Optional[int]]:
    """Return (status_str, days_until_expiry)."""
    if expires_at is None:
        return ("NEVER_AFFIRMED", None)
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    delta = (expires_at - now).days
    if delta > _DUE_SOON_DAYS:
        return ("CURRENT", delta)
    if delta > 0:
        return ("DUE_SOON", delta)
    return ("OVERDUE", delta)


def _blocking_conditions(org_id: str, db: Session) -> list[str]:
    conditions: list[str] = []
    snap = db.execute(text(
        "SELECT 1 FROM assessment_snapshots WHERE org_id = :o LIMIT 1"
    ), {"o": org_id}).fetchone()
    if not snap:
        conditions.append("No assessment snapshot exists. Run an Assessment Simulation before affirming.")
    ssp = db.execute(text("""
        SELECT 1 FROM ssp_sections
        WHERE org_id = :o AND narrative IS NOT NULL AND narrative <> ''
        LIMIT 1
    """), {"o": org_id}).fetchone()
    if not ssp:
        conditions.append("SSP has no narrative sections. Generate SSP before affirming.")
    cage = db.execute(text(
        "SELECT cage_code FROM company_profiles WHERE org_id = :o"
    ), {"o": org_id}).fetchone()
    if not cage or not cage.cage_code:
        conditions.append("No CAGE code recorded. Required for regulatory compliance.")
    return conditions


def get_affirmation_status(org_id: str, db: Session) -> dict:
    row = db.execute(text("""
        SELECT id, affirmed_at, affirmed_by_name, affirmed_by_title,
               sprs_score_snapshot, expires_at
        FROM affirmations
        WHERE org_id = :o
        ORDER BY affirmed_at DESC LIMIT 1
    """), {"o": org_id}).fetchone()

    if not row:
        return {
            "status":               "NEVER_AFFIRMED",
            "latest_affirmation":   None,
            "next_due_date":        None,
            "days_until_due":       None,
            "can_affirm":           True,
            "blocking_conditions":  _blocking_conditions(org_id, db),
        }

    status, days = _derive_status(row.expires_at)
    return {
        "status": status,
        "latest_affirmation": {
            "id":                  row.id,
            "affirmed_at":         row.affirmed_at.isoformat() if row.affirmed_at else None,
            "affirmed_by_name":    row.affirmed_by_name,
            "affirmed_by_title":   row.affirmed_by_title,
            "sprs_score_snapshot": row.sprs_score_snapshot,
            "expires_at":          row.expires_at.isoformat() if row.expires_at else None,
            "days_until_expiry":   days,
        },
        "next_due_date":        row.expires_at.isoformat() if row.expires_at else None,
        "days_until_due":       days,
        "can_affirm":           True,
        "blocking_conditions":  _blocking_conditions(org_id, db),
    }


# ── Create ────────────────────────────────────────────────────────────────

def create_affirmation(
    org_id: str, db: Session, *,
    user_id: str, user_email: str, user_name: str,
    affirmer_title: str,
    attestation_text: Optional[str] = None,
    material_changes: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> dict:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=365)

    # SPRS score
    from src.scoring.sprs import SPRSCalculator
    sprs = SPRSCalculator(org_id).calculate()

    # SSP version
    ssp_row = db.execute(text(
        "SELECT ssp_version FROM company_profiles WHERE org_id = :o"
    ), {"o": org_id}).fetchone()
    ssp_version = (ssp_row.ssp_version if ssp_row and ssp_row.ssp_version
                   else f"v1.0-{now.strftime('%Y%m%d')}")

    # Latest assessment snapshot
    snap = db.execute(text("""
        SELECT id FROM assessment_snapshots
        WHERE org_id = :o ORDER BY created_at DESC LIMIT 1
    """), {"o": org_id}).fetchone()
    snap_id = snap.id if snap else None

    # Open POA&M count
    poam_ct = db.execute(text("""
        SELECT COUNT(*) FROM poam_items WHERE org_id = :o AND status = 'OPEN'
    """), {"o": org_id}).scalar() or 0

    aff_id = _gen_id(f"aff:{org_id}:{now.isoformat()}")
    safe_user = _safe_user_fk(db, user_id)

    db.execute(text("""
        INSERT INTO affirmations
            (id, org_id, affirmed_at, affirmed_by, affirmed_by_name,
             affirmed_by_title, affirmed_by_email,
             sprs_score_snapshot, ssp_version_snapshot, assessment_snapshot_id,
             attestation_text, open_poam_count, material_changes,
             ip_address, expires_at)
        VALUES
            (:id, :o, :now, :by, :name,
             :title, :email,
             :sprs, :ssp_ver, :snap_id,
             :attest, :poam, :changes,
             :ip, :expires)
    """), {
        "id":      aff_id,
        "o":       org_id,
        "now":     now,
        "by":      safe_user or user_id,
        "name":    user_name,
        "title":   affirmer_title,
        "email":   user_email,
        "sprs":    sprs.score,
        "ssp_ver": ssp_version,
        "snap_id": snap_id,
        "attest":  attestation_text,
        "poam":    poam_ct,
        "changes": material_changes,
        "ip":      ip_address,
        "expires": expires,
    })
    db.commit()

    # Generate certificate + compute hash
    org_profile = _load_org_profile(org_id, db)
    aff_dict = _fetch_affirmation(aff_id, db)
    pdf_bytes = generate_certificate_pdf(aff_dict, org_profile, db)
    cert_hash = hashlib.sha256(pdf_bytes).hexdigest()

    db.execute(text("""
        UPDATE affirmations SET certificate_hash = :h WHERE id = :id
    """), {"h": cert_hash, "id": aff_id})
    db.commit()

    _audit(
        db, actor=safe_user or user_id, action="AFFIRMATION_CREATED",
        target_id=aff_id,
        details={
            "org_id":        org_id,
            "sprs_score":    sprs.score,
            "expires_at":    expires.isoformat(),
            "affirmer":      user_name,
            "affirmer_title": affirmer_title,
        },
    )
    db.commit()

    aff_dict["certificate_hash"] = cert_hash
    return aff_dict, pdf_bytes


# ── Helpers ───────────────────────────────────────────────────────────────

def _load_org_profile(org_id: str, db: Session) -> dict:
    row = db.execute(text("""
        SELECT company_name, cage_code, uei
        FROM company_profiles WHERE org_id = :o
    """), {"o": org_id}).fetchone()
    if row:
        return {"name": row.company_name, "cage_code": row.cage_code, "uei": row.uei}
    org = db.execute(text("SELECT name FROM organizations WHERE id = :o"), {"o": org_id}).fetchone()
    return {"name": org.name if org else org_id, "cage_code": None, "uei": None}


def _fetch_affirmation(aff_id: str, db: Session) -> dict:
    row = db.execute(text("SELECT * FROM affirmations WHERE id = :id"), {"id": aff_id}).fetchone()
    if not row:
        return {}
    d = dict(row._mapping)
    for k, v in d.items():
        if isinstance(v, datetime):
            d[k] = v.isoformat()
    return d


def list_affirmations(org_id: str, db: Session, limit: int = 50) -> list[dict]:
    rows = db.execute(text("""
        SELECT id, affirmed_at, affirmed_by_name, affirmed_by_title,
               affirmed_by_email, sprs_score_snapshot, ssp_version_snapshot,
               open_poam_count, expires_at, certificate_hash
        FROM affirmations
        WHERE org_id = :o
        ORDER BY affirmed_at DESC
        LIMIT :lim
    """), {"o": org_id, "lim": limit}).fetchall()
    result = []
    for r in rows:
        d = dict(r._mapping)
        status, days = _derive_status(r.expires_at)
        d["status"] = status
        d["days_until_expiry"] = days
        for k, v in d.items():
            if isinstance(v, datetime):
                d[k] = v.isoformat()
        result.append(d)
    return result


def get_affirmation(aff_id: str, org_id: str, db: Session) -> Optional[dict]:
    d = _fetch_affirmation(aff_id, db)
    if not d or d.get("org_id") != org_id:
        return None
    status, days = _derive_status(
        datetime.fromisoformat(d["expires_at"]) if isinstance(d.get("expires_at"), str) else d.get("expires_at")
    )
    d["status"] = status
    d["days_until_expiry"] = days
    return d


# ── Certificate PDF ───────────────────────────────────────────────────────

def generate_certificate_pdf(aff: dict, org_profile: dict, db: Session) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    org_name = org_profile.get("name", "Organization")

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "ANNUAL CMMC COMPLIANCE AFFIRMATION", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Per 32 CFR 170.22", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, org_name, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    if org_profile.get("cage_code"):
        pdf.cell(0, 6, f"CAGE Code: {org_profile['cage_code']}", new_x="LMARGIN", new_y="NEXT")
    if org_profile.get("uei"):
        pdf.cell(0, 6, f"UEI: {org_profile['uei']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "AFFIRMATION", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    name  = aff.get("affirmed_by_name", "Authorized Official")
    title = aff.get("affirmed_by_title", "Senior Official")
    score = aff.get("sprs_score_snapshot", "N/A")
    ssp_v = aff.get("ssp_version_snapshot", "current")
    poam  = aff.get("open_poam_count", 0)

    pdf.set_font("Helvetica", "", 10)
    lines = [
        f"I, {name}, in my capacity as {title}, affirm that on behalf of {org_name}:",
        "",
        f"1. The System Security Plan (version {ssp_v}) is current and accurately",
        "   reflects the organization's security posture.",
        f"2. The SPRS self-assessment score of {score} of 110 remains accurate.",
        f"3. Open POA&M items ({poam}) are being actively remediated per schedule.",
        "4. No material changes to the organization's CUI scope, systems, or",
        "   processes have occurred that would invalidate the assessment.",
    ]
    for line in lines:
        pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")

    if aff.get("attestation_text"):
        pdf.ln(4)
        pdf.set_font("Helvetica", "I", 9)
        text_lines = aff["attestation_text"][:500]
        for i in range(0, len(text_lines), 95):
            pdf.cell(0, 5, text_lines[i:i+95], new_x="LMARGIN", new_y="NEXT")

    if aff.get("material_changes"):
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, "Material changes disclosed:", new_x="LMARGIN", new_y="NEXT")
        mc = aff["material_changes"][:500]
        for i in range(0, len(mc), 95):
            pdf.cell(0, 5, f"  {mc[i:i+95]}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)
    pdf.set_font("Helvetica", "", 10)

    affirmed_at = aff.get("affirmed_at", "")
    if isinstance(affirmed_at, datetime):
        affirmed_at = affirmed_at.strftime("%Y-%m-%d %H:%M UTC")
    elif isinstance(affirmed_at, str) and len(affirmed_at) > 19:
        affirmed_at = affirmed_at[:19].replace("T", " ") + " UTC"

    expires_at = aff.get("expires_at", "")
    if isinstance(expires_at, datetime):
        expires_at = expires_at.strftime("%Y-%m-%d")
    elif isinstance(expires_at, str):
        expires_at = expires_at[:10]

    details = [
        f"Affirmed by:  {name}",
        f"Title:        {title}",
        f"Email:        {aff.get('affirmed_by_email', '')}",
        f"Date:         {affirmed_at}",
        f"Expires:      {expires_at} (365 days)",
        "",
        f"Affirmation ID:  {aff.get('id', '')}",
        f"IP Address:      {aff.get('ip_address', 'N/A')}",
    ]
    for d in details:
        pdf.cell(0, 6, d, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, "This affirmation must be retained for 6 years per CMMC record retention requirements.",
             new_x="LMARGIN", new_y="NEXT")

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()
