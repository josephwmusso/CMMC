"""
src/api/ssp_routes.py

FastAPI routes for SSP generation.

Endpoints:
  POST /api/ssp/generate          — Generate SSP for a single control
  POST /api/ssp/generate-full     — Generate full SSP (all 110 controls)
  GET  /api/ssp/download/{filename} — Download generated SSP document
  GET  /api/ssp/status             — Check generation status
"""

import os
import uuid
import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.agents.llm_client import get_llm
from src.agents.ssp_generator_v2 import SSPGenerator
from src.agents.ssp_prompts_v2 import DEMO_ORG_PROFILE
from src.ssp.docx_export import export_ssp_to_docx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ssp", tags=["SSP Generation"])

# In-memory job tracker (replace with Postgres/Redis in production)
_jobs: dict = {}

EXPORT_DIR = os.path.join("data", "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------
class OrgProfileInput(BaseModel):
    org_name: str = Field(default="Apex Defense Solutions")
    system_name: str = Field(default="Apex Secure Enclave (ASE)")
    system_description: str = Field(default="")
    employee_count: int = Field(default=45)
    facility_type: str = Field(default="Single office with dedicated server room")
    tools_description: str = Field(default="")
    network_description: str = Field(default="")
    org_id: str = Field(default="default-org")
    use_demo_profile: bool = Field(
        default=True,
        description="If true, uses the built-in Apex Defense demo profile for any empty fields.",
    )

    def to_dict(self) -> dict:
        """Convert to dict, filling in demo defaults for empty fields if use_demo_profile is True."""
        d = self.model_dump()
        if d.pop("use_demo_profile", False):
            for key, demo_val in DEMO_ORG_PROFILE.items():
                if not d.get(key):
                    d[key] = demo_val
        return d


class SingleControlRequest(BaseModel):
    control_id: str = Field(..., json_schema_extra={"example": "AC.L2-3.1.1"})
    org_profile: OrgProfileInput = Field(default_factory=OrgProfileInput)


class FullSSPRequest(BaseModel):
    org_profile: OrgProfileInput = Field(default_factory=OrgProfileInput)
    control_ids: Optional[list[str]] = Field(
        default=None,
        description="Specific controls to generate. If null, generates all 110.",
    )
    export_docx: bool = Field(default=True, description="Also export to Word doc.")


class ControlResult(BaseModel):
    control_id: str
    status: str
    narrative: str
    evidence_artifacts: list[str]
    gaps: list[str]
    generation_time_sec: float
    error: Optional[str] = None


class JobStatus(BaseModel):
    job_id: str
    status: str  # pending | running | completed | failed
    progress: str
    controls_done: int
    controls_total: int
    docx_path: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Single control generation (synchronous — fast enough for one control)
# ---------------------------------------------------------------------------
@router.post("/generate", response_model=ControlResult)
def generate_single_control(req: SingleControlRequest, db: Session = Depends(get_db)):
    """Generate SSP narrative for a single NIST 800-171 control."""
    llm = get_llm()
    generator = SSPGenerator(llm=llm)
    org = req.org_profile.to_dict()

    result = generator.generate_single_control(
        control_id=req.control_id,
        org_profile=org,
        db=db,
    )

    return ControlResult(
        control_id=result.control_id,
        status=result.status,
        narrative=result.narrative,
        evidence_artifacts=result.evidence_artifacts,
        gaps=result.gaps,
        generation_time_sec=round(result.generation_time_sec, 2),
        error=result.error,
    )


# ---------------------------------------------------------------------------
# Full SSP generation (async via BackgroundTasks — takes minutes)
# ---------------------------------------------------------------------------
def _run_full_ssp(job_id: str, org_profile: dict, control_ids: Optional[list[str]], export_docx: bool):
    """Background task that generates the full SSP."""
    from src.db.session import SessionLocal

    db = SessionLocal()
    try:
        _jobs[job_id]["status"] = "running"

        llm = get_llm()
        generator = SSPGenerator(llm=llm)

        def progress_cb(current, total, control_id):
            _jobs[job_id]["controls_done"] = current
            _jobs[job_id]["controls_total"] = total
            _jobs[job_id]["progress"] = f"{current}/{total} — {control_id}"

        results = generator.generate_full_ssp(
            org_profile=org_profile,
            db=db,
            control_ids=control_ids,
            progress_callback=progress_cb,
        )

        # Export to Word
        docx_path = None
        if export_docx:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"SSP_{org_profile.get('org_name', 'org').replace(' ', '_')}_{timestamp}.docx"
            docx_path = os.path.join(EXPORT_DIR, filename)
            export_ssp_to_docx(results, org_profile, docx_path)
            _jobs[job_id]["docx_path"] = filename

        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["completed_at"] = datetime.datetime.utcnow().isoformat()

        logger.info(f"Job {job_id} completed. DOCX: {docx_path}")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)
    finally:
        db.close()


@router.post("/generate-full", response_model=JobStatus)
def generate_full_ssp(req: FullSSPRequest, background_tasks: BackgroundTasks):
    """Start full SSP generation as a background job.

    Returns a job_id — poll GET /api/ssp/status?job_id=... for progress.
    """
    job_id = str(uuid.uuid4())[:8]
    org = req.org_profile.to_dict()

    _jobs[job_id] = {
        "status": "pending",
        "progress": "Starting...",
        "controls_done": 0,
        "controls_total": 0,
        "docx_path": None,
        "started_at": datetime.datetime.utcnow().isoformat(),
        "completed_at": None,
        "error": None,
    }

    background_tasks.add_task(
        _run_full_ssp,
        job_id=job_id,
        org_profile=org,
        control_ids=req.control_ids,
        export_docx=req.export_docx,
    )

    return JobStatus(job_id=job_id, **_jobs[job_id])


# ---------------------------------------------------------------------------
# Status & download
# ---------------------------------------------------------------------------
@router.post("/generate-full-temporal", response_model=JobStatus)
async def generate_full_ssp_temporal(req: FullSSPRequest):
    """Start full SSP generation as a durable Temporal workflow.

    Returns a workflow_id — track progress in Temporal UI at http://localhost:8080
    or poll GET /api/ssp/status?job_id=... (backed by Temporal query).
    """
    import asyncio
    from temporalio.client import Client
    from src.workflows.ssp_workflow import SSPGenerationWorkflow, SSPWorkflowInput, TASK_QUEUE
    from configs.settings import TEMPORAL_HOST

    org = req.org_profile.to_dict()
    workflow_id = f"ssp-{org.get('org_id', 'default')}-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    client = await Client.connect(TEMPORAL_HOST)
    inp = SSPWorkflowInput(
        org_id=org.get("org_id", "default-org"),
        org_name=org.get("org_name", "Organization"),
        system_name=org.get("system_name", "Information System"),
        system_description=org.get("system_description", ""),
        employee_count=org.get("employee_count", 50),
        facility_type=org.get("facility_type", ""),
        tools_description=org.get("tools_description", ""),
        network_description=org.get("network_description", ""),
        control_ids=req.control_ids,
        export_docx=req.export_docx,
    )

    handle = await client.start_workflow(
        SSPGenerationWorkflow.run,
        inp,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    _jobs[workflow_id] = {
        "status": "running",
        "progress": f"Temporal workflow started: {workflow_id}",
        "controls_done": 0,
        "controls_total": len(req.control_ids) if req.control_ids else 110,
        "docx_path": None,
        "started_at": datetime.datetime.utcnow().isoformat(),
        "completed_at": None,
        "error": None,
        "temporal_ui": f"http://localhost:8080/namespaces/default/workflows/{workflow_id}",
    }

    logger.info(f"Temporal workflow started: {workflow_id}")
    return JobStatus(job_id=workflow_id, **{k: v for k, v in _jobs[workflow_id].items() if k != "temporal_ui"})


@router.get("/status", response_model=JobStatus)
def get_job_status(job_id: str):
    """Check the status of an SSP generation job."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return JobStatus(job_id=job_id, **_jobs[job_id])


@router.get("/exports")
def list_exports():
    """List available SSP Word documents in the exports directory."""
    docx_files = sorted(
        [f for f in os.listdir(EXPORT_DIR) if f.endswith(".docx")],
        reverse=True,
    )
    return {"files": docx_files, "count": len(docx_files)}


@router.get("/export-latest")
def export_latest(db: Session = Depends(get_db)):
    """Generate a fresh DOCX from the current ssp_sections in the DB and return it.

    This is the primary download endpoint — it always builds from live DB data.
    """
    from sqlalchemy import text
    from src.agents.ssp_generator_v2 import SSPControlResult

    rows = db.execute(text("""
        SELECT ss.control_id, ss.implementation_status, ss.narrative,
               ss.evidence_refs, ss.gaps, c.title, c.family_abbrev
        FROM ssp_sections ss
        JOIN controls c ON c.id = ss.control_id
        WHERE ss.org_id = :org_id
        ORDER BY ss.control_id
    """), {"org_id": "9de53b587b23450b87af"}).fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="No SSP sections in database. Run Generate SSP first.",
        )

    results = []
    for r in rows:
        result = SSPControlResult(
            control_id=r[0],
            status=r[1] or "Not Assessed",
            narrative=r[2] or "",
        )
        result.evidence_artifacts = r[3] if isinstance(r[3], list) else []
        result.gaps = r[4] if isinstance(r[4], list) else []
        results.append(result)

    org_profile = DEMO_ORG_PROFILE
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"SSP_Apex_Defense_Solutions_{timestamp}.docx"
    filepath = os.path.join(EXPORT_DIR, filename)

    try:
        export_ssp_to_docx(results, org_profile, filepath)
    except Exception as e:
        logger.error(f"DOCX export failed: {e}")
        raise HTTPException(status_code=500, detail=f"DOCX generation failed: {e}")

    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )


@router.get("/export-pdf")
def export_pdf():
    """Generate a fresh PDF from the current ssp_sections in the DB.

    Uses fpdf2 (pure Python) — no external dependencies like Word or LibreOffice.
    """
    from src.ssp.pdf_export import generate_ssp_pdf

    org_id = "9de53b587b23450b87af"
    try:
        filepath = generate_ssp_pdf(org_id)
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    filename = os.path.basename(filepath)
    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename=filename,
    )


@router.get("/narrative/{control_id}")
def get_narrative(control_id: str, db: Session = Depends(get_db)):
    """Get the SSP narrative for a single control."""
    from sqlalchemy import text as sa_text

    row = db.execute(sa_text("""
        SELECT narrative, implementation_status
        FROM ssp_sections
        WHERE control_id = :cid AND org_id = :oid
    """), {"cid": control_id, "oid": "9de53b587b23450b87af"}).fetchone()

    if not row:
        return {"control_id": control_id, "narrative": None, "implementation_status": None}

    return {
        "control_id": control_id,
        "narrative": row[0],
        "implementation_status": row[1],
    }


@router.get("/download/{filename}")
def download_ssp(filename: str):
    """Download a previously generated SSP Word document by filename."""
    safe_name = os.path.basename(filename)
    filepath = os.path.join(EXPORT_DIR, safe_name)
    if not os.path.abspath(filepath).startswith(os.path.abspath(EXPORT_DIR)):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=safe_name,
    )
