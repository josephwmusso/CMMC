"""
FastAPI routes for SPRS scoring, gap assessment, and POA&M management.
All routes require JWT auth — org_id is extracted from the token.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from src.api.auth import get_current_user

logger = logging.getLogger(__name__)
from src.scoring.sprs import SPRSCalculator
from src.scoring.gap_assessment import GapAssessmentEngine
from src.scoring.poam import POAMGenerator

router = APIRouter(prefix="/api/scoring", tags=["scoring"])


@router.get("/sprs")
def get_sprs_score(current_user: dict = Depends(get_current_user)):
    """Get SPRS score with full breakdown."""
    try:
        calc = SPRSCalculator(org_id=current_user["org_id"])
        return calc.get_score_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gaps")
def get_gap_assessment(current_user: dict = Depends(get_current_user)):
    """Get full gap assessment."""
    try:
        engine = GapAssessmentEngine(org_id=current_user["org_id"])
        return engine.get_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gaps/critical")
def get_critical_gaps(current_user: dict = Depends(get_current_user)):
    """Get only CRITICAL severity gaps (5-point controls)."""
    engine = GapAssessmentEngine(org_id=current_user["org_id"])
    summary = engine.get_summary()
    critical = [g for g in summary["gap_details"] if g["severity"] == "CRITICAL"]
    return {"count": len(critical), "gaps": critical}


@router.post("/poam/generate")
def generate_poam(current_user: dict = Depends(get_current_user)):
    """Auto-generate POA&M items from SSP assessment."""
    try:
        gen = POAMGenerator(org_id=current_user["org_id"])
        created, skipped = gen.generate_from_ssp()
        summary = gen.get_poam_summary()
        return {"created": created, "skipped": skipped, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/poam")
def get_poam_summary(current_user: dict = Depends(get_current_user)):
    """Get current POA&M status."""
    gen = POAMGenerator(org_id=current_user["org_id"])
    return gen.get_poam_summary()


@router.get("/poam/export-pdf")
def export_poam_pdf(current_user: dict = Depends(get_current_user)):
    """Generate and return POA&M as PDF."""
    from src.ssp.poam_export import generate_poam_pdf
    try:
        filepath = generate_poam_pdf(current_user["org_id"])
    except Exception as e:
        logger.error(f"POA&M PDF export failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")
    import os
    return FileResponse(filepath, media_type="application/pdf", filename=os.path.basename(filepath))


@router.get("/poam/export-docx")
def export_poam_docx(current_user: dict = Depends(get_current_user)):
    """Generate and return POA&M as DOCX."""
    from src.ssp.poam_export import generate_poam_docx
    try:
        filepath = generate_poam_docx(current_user["org_id"])
    except Exception as e:
        logger.error(f"POA&M DOCX export failed: {e}")
        raise HTTPException(status_code=500, detail=f"DOCX generation failed: {e}")
    import os
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=os.path.basename(filepath),
    )


@router.get("/overview")
def get_compliance_overview(current_user: dict = Depends(get_current_user)):
    """Combined overview: SPRS + gaps + POA&M in one call."""
    org_id = current_user["org_id"]
    calc = SPRSCalculator(org_id=org_id)
    sprs = calc.get_score_summary()
    engine = GapAssessmentEngine(org_id=org_id)
    gaps = engine.get_summary()
    gen = POAMGenerator(org_id=org_id)
    poam = gen.get_poam_summary()
    return {"sprs": sprs, "gaps": gaps, "poam": poam}
