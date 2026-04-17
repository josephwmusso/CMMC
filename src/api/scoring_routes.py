"""
FastAPI routes for SPRS scoring, gap assessment, and POA&M management.
All routes require JWT auth — org_id is extracted from the token.
All endpoints return valid JSON — never an unhandled 500.
"""
import sys
import os
import logging
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.auth import get_current_user
from src.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scoring", tags=["scoring"])


def _get_org_name(org_id: str, db) -> str:
    row = db.execute(text("SELECT name FROM organizations WHERE id = :o"), {"o": org_id}).fetchone()
    return row[0] if row else "Organization"


def _safe_sprs(org_id: str):
    """Try normal SPRS calculator, fall back to raw SQL."""
    try:
        from src.scoring.sprs import SPRSCalculator
        calc = SPRSCalculator(org_id=org_id)
        return calc.get_score_summary()
    except Exception as e:
        logger.error(f"SPRS calculator failed: {e}")
        return None


def _safe_gaps(org_id: str):
    """Try normal gap engine, fall back to empty."""
    try:
        from src.scoring.gap_assessment import GapAssessmentEngine
        engine = GapAssessmentEngine(org_id=org_id)
        return engine.get_summary()
    except Exception as e:
        logger.error(f"Gap engine failed: {e}")
        return None


def _safe_poam(org_id: str):
    """Try normal POAM generator, fall back to empty."""
    try:
        from src.scoring.poam import POAMGenerator
        gen = POAMGenerator(org_id=org_id)
        return gen.get_poam_summary()
    except Exception as e:
        logger.error(f"POAM generator failed: {e}")
        return None


def _fallback_overview(org_id: str, db: Session):
    """Compute overview from raw SQL when calculators fail."""
    try:
        controls = db.execute(text(
            "SELECT id, family, family_abbrev, title, points, poam_eligible FROM controls"
        )).fetchall()
        total_controls = len(controls)

        # SSP statuses
        try:
            ssp_rows = db.execute(text(
                "SELECT control_id, implementation_status FROM ssp_sections WHERE org_id = :org"
            ), {"org": org_id}).fetchall()
            ssp_map = {r[0]: r[1] for r in ssp_rows}
        except Exception:
            ssp_map = {}

        met_statuses = ("Implemented", "implemented", "MET", "met")
        partial_statuses = ("Partially Implemented", "partially_implemented", "PARTIAL", "partial")

        met = sum(1 for c in controls if ssp_map.get(c[0]) in met_statuses)
        partial = sum(1 for c in controls if ssp_map.get(c[0]) in partial_statuses)
        not_met = total_controls - met - partial
        met_points = sum(c[4] for c in controls if ssp_map.get(c[0]) in met_statuses)
        total_points = sum(c[4] for c in controls)
        raw_score = 110 - (total_points - met_points)

        # Families
        family_map = {}
        for c in controls:
            cid, family, abbrev, title, points, poam_el = c
            if abbrev not in family_map:
                family_map[abbrev] = {"family": family, "family_abbrev": abbrev, "total_controls": 0, "met": 0, "not_met": 0, "partial": 0, "not_assessed": 0, "total_points": 0, "points_lost": 0}
            fm = family_map[abbrev]
            fm["total_controls"] += 1
            fm["total_points"] += points
            status = ssp_map.get(cid, "")
            if status in met_statuses:
                fm["met"] += 1
            elif status in partial_statuses:
                fm["partial"] += 1
            else:
                fm["not_assessed"] += 1
                fm["points_lost"] += points

        # Details list (what SSP page reads)
        details = []
        for c in controls:
            cid, family, abbrev, title, points, poam_el = c
            impl = ssp_map.get(cid)
            details.append({
                "control_id": cid,
                "title": title,
                "family": abbrev,
                "points": points,
                "implementation_status": impl or "Not Assessed",
                "status_label": "MET" if impl in met_statuses else "NOT MET" if impl else "NOT ASSESSED",
                "deduction": 0 if impl in met_statuses else points,
                "on_poam": False,
            })

        # POA&M
        try:
            poam_rows = db.execute(text(
                "SELECT status, COUNT(*) FROM poam_items WHERE org_id = :org GROUP BY status"
            ), {"org": org_id}).fetchall()
            poam_items = []
            try:
                poam_items = db.execute(text(
                    "SELECT p.id, p.control_id, p.weakness_description, p.remediation_plan, p.status, "
                    "p.risk_level, p.scheduled_completion, p.points, c.title, c.family_abbrev "
                    "FROM poam_items p JOIN controls c ON c.id = p.control_id "
                    "WHERE p.org_id = :org ORDER BY p.control_id"
                ), {"org": org_id}).fetchall()
            except Exception:
                pass
            status_counts = {}
            for r in poam_rows:
                status_counts[r[0]] = r[1]
        except Exception:
            poam_items = []
            status_counts = {}

        # Gaps
        gap_details = []
        for c in controls:
            cid, family, abbrev, title, points, poam_el = c
            if ssp_map.get(cid) not in met_statuses:
                severity = "CRITICAL" if points >= 5 else "HIGH" if points >= 3 else "MEDIUM"
                gap_details.append({
                    "control_id": cid, "family": abbrev, "title": title,
                    "points": points, "severity": severity,
                    "gap_type": "NO_SSP" if cid not in ssp_map else "PARTIAL_IMPLEMENTATION",
                    "status": ssp_map.get(cid, "Not Assessed"),
                })

        return {
            "sprs": {
                "score": raw_score,
                "conditional_score": raw_score,
                "max_score": 110,
                "percentage": round((raw_score / 110) * 100, 1) if raw_score > 0 else 0,
                "met": met,
                "not_met": not_met,
                "partial": partial,
                "not_assessed": not_met,
                "total_controls": total_controls,
                "total_deductions": total_points - met_points,
                "poam_eligible": raw_score >= 88,
                "critical_gaps": [d for d in details if d["points"] >= 5 and d["status_label"] != "MET"],
                "families": family_map,
                "details": details,
                "org_name": _get_org_name(org_id, db),
                "total": total_controls,
            },
            "gaps": {
                "gap_count": len(gap_details),
                "gap_details": gap_details,
            },
            "poam": {
                "total_items": sum(status_counts.values()),
                "status_counts": status_counts,
                "items": [
                    {
                        "id": r[0], "control_id": r[1], "weakness_description": r[2],
                        "remediation_plan": r[3], "status": r[4], "risk_level": r[5],
                        "scheduled_completion": str(r[6]) if r[6] else None,
                        "points": r[7], "title": r[8], "family_abbrev": r[9],
                    }
                    for r in poam_items
                ],
            },
        }
    except Exception as e:
        logger.error(f"Fallback overview failed: {e}\n{traceback.format_exc()}")
        return {
            "sprs": {"score": 0, "conditional_score": 0, "max_score": 110, "percentage": 0,
                     "met": 0, "not_met": 0, "partial": 0, "not_assessed": 0,
                     "total_controls": 0, "total_deductions": 0, "poam_eligible": False,
                     "critical_gaps": [], "families": {}, "details": [], "total": 0},
            "gaps": {"gap_count": 0, "gap_details": []},
            "poam": {"total_items": 0, "status_counts": {}, "items": []},
        }


@router.get("/sprs")
def get_sprs_score(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    result = _safe_sprs(current_user["org_id"])
    if result is not None:
        return result
    # Fallback
    overview = _fallback_overview(current_user["org_id"], db)
    return overview["sprs"]


@router.get("/gaps")
def get_gap_assessment(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    result = _safe_gaps(current_user["org_id"])
    if result is not None:
        return result
    overview = _fallback_overview(current_user["org_id"], db)
    return overview["gaps"]


@router.get("/gaps/critical")
def get_critical_gaps(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        from src.scoring.gap_assessment import GapAssessmentEngine
        engine = GapAssessmentEngine(org_id=current_user["org_id"])
        summary = engine.get_summary()
        critical = [g for g in summary.get("gap_details", []) if g.get("severity") == "CRITICAL"]
        return {"count": len(critical), "gaps": critical}
    except Exception as e:
        logger.error(f"Critical gaps failed: {e}")
        return {"count": 0, "gaps": []}


@router.post("/poam/generate")
def generate_poam(current_user: dict = Depends(get_current_user)):
    try:
        from src.scoring.poam import POAMGenerator
        gen = POAMGenerator(org_id=current_user["org_id"])
        created, skipped = gen.generate_from_ssp()
        summary = gen.get_poam_summary()
        return {"created": created, "skipped": skipped, "summary": summary}
    except Exception as e:
        logger.error(f"POA&M generation failed: {e}")
        return {"created": 0, "skipped": 0, "error": str(e),
                "summary": {"total_items": 0, "status_counts": {}, "items": []}}


@router.get("/poam")
def get_poam_summary(current_user: dict = Depends(get_current_user)):
    result = _safe_poam(current_user["org_id"])
    if result is not None:
        return result
    return {"total_items": 0, "status_counts": {}, "items": []}


@router.get("/poam/export-pdf")
def export_poam_pdf(current_user: dict = Depends(get_current_user)):
    try:
        from src.ssp.poam_export import generate_poam_pdf
        filepath = generate_poam_pdf(current_user["org_id"])
        return FileResponse(filepath, media_type="application/pdf", filename=os.path.basename(filepath))
    except Exception as e:
        logger.error(f"POA&M PDF export failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")


@router.get("/poam/export-docx")
def export_poam_docx(current_user: dict = Depends(get_current_user)):
    try:
        from src.ssp.poam_export import generate_poam_docx
        filepath = generate_poam_docx(current_user["org_id"])
        return FileResponse(filepath, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            filename=os.path.basename(filepath))
    except Exception as e:
        logger.error(f"POA&M DOCX export failed: {e}")
        raise HTTPException(status_code=500, detail=f"DOCX generation failed: {e}")


@router.get("/overview")
def get_compliance_overview(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Combined overview: SPRS + gaps + POA&M in one call."""
    org_id = current_user["org_id"]

    # Try normal calculators first
    sprs = _safe_sprs(org_id)
    gaps = _safe_gaps(org_id)
    poam = _safe_poam(org_id)

    if sprs is not None and gaps is not None and poam is not None:
        # Frontend computes totalControls = met + partial + not_met
        # SPRS calculator reports not_assessed separately — merge into not_met for frontend
        sprs["not_met"] = sprs.get("not_met", 0) + sprs.get("not_assessed", 0)
        return {"sprs": sprs, "gaps": gaps, "poam": poam}

    # Fallback to raw SQL
    logger.info("Using fallback overview (one or more calculators failed)")
    return _fallback_overview(org_id, db)
