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
from src.api.auth import get_current_user
from src.utils.service_check import is_qdrant_available, is_llm_available

# Lazy imports — SSPGenerator connects to Qdrant on init, which crashes on Render
# from src.agents.llm_client import get_llm
# from src.agents.ssp_generator_v2 import SSPGenerator
# from src.agents.ssp_prompts_v2 import DEMO_ORG_PROFILE
# from src.ssp.docx_export import export_ssp_to_docx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ssp", tags=["SSP Generation"])

# Database-backed job tracker (persists across workers/restarts)
EXPORT_DIR = os.path.join("data", "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


def _ensure_jobs_table():
    """Create ssp_jobs table if it doesn't exist."""
    from sqlalchemy import text
    from src.db.session import engine
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ssp_jobs (
                job_id VARCHAR(20) PRIMARY KEY,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                progress TEXT NOT NULL DEFAULT 'Starting...',
                controls_done INTEGER NOT NULL DEFAULT 0,
                controls_total INTEGER NOT NULL DEFAULT 0,
                docx_path TEXT,
                started_at TIMESTAMPTZ,
                completed_at TIMESTAMPTZ,
                error TEXT
            )
        """))

_ensure_jobs_table()


def _get_job(job_id: str) -> dict | None:
    from sqlalchemy import text
    from src.db.session import engine
    with engine.connect() as conn:
        row = conn.execute(text("SELECT * FROM ssp_jobs WHERE job_id = :jid"), {"jid": job_id}).fetchone()
        if not row:
            return None
        return dict(row._mapping)


def _set_job(job_id: str, **kwargs):
    from sqlalchemy import text
    from src.db.session import engine
    with engine.begin() as conn:
        existing = conn.execute(text("SELECT 1 FROM ssp_jobs WHERE job_id = :jid"), {"jid": job_id}).fetchone()
        if existing:
            sets = ", ".join(f"{k} = :{k}" for k in kwargs)
            conn.execute(text(f"UPDATE ssp_jobs SET {sets} WHERE job_id = :jid"), {"jid": job_id, **kwargs})
        else:
            cols = ", ".join(["job_id"] + list(kwargs.keys()))
            vals = ", ".join([":jid"] + [f":{k}" for k in kwargs])
            conn.execute(text(f"INSERT INTO ssp_jobs ({cols}) VALUES ({vals})"), {"jid": job_id, **kwargs})


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------
class OrgProfileInput(BaseModel):
    org_name: str = Field(default="Organization")
    system_name: str = Field(default="Information System")
    system_description: str = Field(default="")
    employee_count: int = Field(default=0)
    facility_type: str = Field(default="")
    tools_description: str = Field(default="")
    network_description: str = Field(default="")
    org_id: str = Field(default="default-org")
    use_demo_profile: bool = Field(
        default=True,
        description="If true, uses the built-in Apex Defense demo profile for any empty fields.",
    )

    def to_dict(self) -> dict:
        """Convert to dict. No demo fallback — all generators read from company_profiles."""
        d = self.model_dump()
        d.pop("use_demo_profile", None)
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
    status: str  # pending | running | completed | failed | cancelled
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
def generate_single_control(
    req: SingleControlRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate SSP narrative for a single NIST 800-171 control."""
    if not is_llm_available():
        raise HTTPException(503, "SSP generation requires an LLM API key, which is not configured.")
    from src.agents.ssp_generator_v2 import SSPGenerator
    from src.agents.org_profile import build_org_profile, CompanyProfileMissing
    try:
        org = build_org_profile(current_user["org_id"], db)
    except CompanyProfileMissing:
        raise HTTPException(400, "Your organization must complete onboarding before generating an SSP.")
    generator = SSPGenerator(org_profile=org)

    result_data = generator.generate_section(req.control_id)
    parsed = result_data["parsed"]

    # Persist to DB with flag-and-preserve metadata
    generator.persist_section(
        parsed,
        original_narrative=result_data.get("original_narrative"),
        detector_findings=result_data.get("detector_findings"),
    )

    return ControlResult(
        control_id=parsed.get("control_id", req.control_id),
        status=parsed.get("implementation_status", "Not Assessed"),
        narrative=parsed.get("narrative", ""),
        evidence_artifacts=[
            e.get("artifact_title") or e.get("description") or str(e)
            if isinstance(e, dict) else str(e)
            for e in parsed.get("evidence_references", [])
        ],
        gaps=[g.get("description", "") for g in parsed.get("gaps", [])],
        generation_time_sec=0.0,
        error=None,
    )


# ---------------------------------------------------------------------------
# Full SSP generation (async via BackgroundTasks — takes minutes)
# ---------------------------------------------------------------------------
def _run_full_ssp(job_id: str, org_profile: dict, control_ids: Optional[list[str]], export_docx: bool):
    """Background task that generates the full SSP."""
    from src.db.session import SessionLocal

    db = SessionLocal()
    try:
        _set_job(job_id, status="running")

        from src.agents.ssp_generator_v2 import SSPGenerator, SSPControlResult
        from sqlalchemy import text
        generator = SSPGenerator(org_profile=org_profile)

        # Get all control IDs to generate
        all_control_ids = control_ids
        if not all_control_ids:
            rows = db.execute(text("SELECT id FROM controls ORDER BY id")).fetchall()
            all_control_ids = [r[0] for r in rows]

        total = len(all_control_ids)
        _set_job(job_id, controls_total=total)

        results = []
        cancelled = False
        for i, cid in enumerate(all_control_ids):
            # Cooperative cancellation — caller can POST /api/ssp/cancel?job_id=...
            current = _get_job(job_id)
            if current and current.get("status") == "cancelled":
                logger.info(f"Job {job_id} cancelled at {i}/{total}")
                cancelled = True
                break

            try:
                result_data = generator.generate_section(cid)
                parsed = result_data["parsed"]
                generator.persist_section(parsed)
                results.append(SSPControlResult(
                    control_id=cid,
                    status=parsed.get("implementation_status", "Not Assessed"),
                    narrative=parsed.get("narrative", ""),
                ))
            except Exception as e:
                logger.error(f"Failed to generate {cid}: {e}")
                results.append(SSPControlResult(control_id=cid, error=str(e)))

            _set_job(job_id, controls_done=i+1, progress=f"{i+1}/{total} — {cid}")

        if cancelled:
            _set_job(job_id, completed_at=datetime.datetime.utcnow().isoformat())
            return

        # Export to Word
        docx_path = None
        if export_docx:
            try:
                from src.ssp.docx_export import export_ssp_to_docx
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"SSP_{org_profile.get('org_name', 'org').replace(' ', '_')}_{timestamp}.docx"
                docx_path = os.path.join(EXPORT_DIR, filename)
                export_ssp_to_docx(results, org_profile, docx_path)
                _set_job(job_id, docx_path=filename)
            except Exception as e:
                logger.error(f"DOCX export failed: {e}")

        _set_job(job_id, status="completed", completed_at=datetime.datetime.utcnow().isoformat())

        logger.info(f"Job {job_id} completed. DOCX: {docx_path}")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        _set_job(job_id, status="failed", error=str(e))
    finally:
        db.close()


@router.post("/generate-full", response_model=JobStatus)
def generate_full_ssp(
    req: FullSSPRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Start full SSP generation as a background job.

    org_id is authoritative from the JWT — any org_id in the request body
    is ignored (or validated for SUPERADMIN). Returns a job_id.
    """
    if not is_llm_available():
        raise HTTPException(503, "SSP generation requires an LLM API key, which is not configured.")
    from src.agents.org_profile import build_org_profile, CompanyProfileMissing
    try:
        org = build_org_profile(current_user["org_id"], db)
    except CompanyProfileMissing:
        raise HTTPException(400, "Your organization must complete onboarding before generating an SSP.")
    job_id = str(uuid.uuid4())[:8]

    started = datetime.datetime.utcnow().isoformat()
    _set_job(job_id, org_id=current_user["org_id"], status="pending",
             progress="Starting...", controls_done=0, controls_total=0,
             started_at=started)

    background_tasks.add_task(
        _run_full_ssp,
        job_id=job_id,
        org_profile=org,
        control_ids=req.control_ids,
        export_docx=req.export_docx,
    )

    return JobStatus(job_id=job_id, status="pending", progress="Starting...",
                     controls_done=0, controls_total=0, started_at=started)


# ---------------------------------------------------------------------------
# Status & download
# ---------------------------------------------------------------------------
@router.post("/generate-full-temporal", response_model=JobStatus)
async def generate_full_ssp_temporal(
    req: FullSSPRequest,
    current_user: dict = Depends(get_current_user),
):
    """Start full SSP generation as a durable Temporal workflow.

    org_id is taken from the JWT (body org_id ignored for non-superadmins).
    Returns a workflow_id — track progress in Temporal UI or poll
    GET /api/ssp/status?job_id=...
    """
    try:
        from temporalio.client import Client
        from src.workflows.ssp_workflow import SSPGenerationWorkflow, SSPWorkflowInput, TASK_QUEUE
        from configs.settings import TEMPORAL_HOST
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="Temporal is not available in this deployment. Use /api/ssp/generate-full instead.",
        )

    from src.agents.org_profile import build_org_profile, CompanyProfileMissing
    try:
        org = build_org_profile(current_user["org_id"], db)
    except CompanyProfileMissing:
        raise HTTPException(400, "Organization must complete onboarding before SSP generation.")
    workflow_id = f"ssp-{org['org_id']}-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

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

    total = len(req.control_ids) if req.control_ids else 110
    started = datetime.datetime.utcnow().isoformat()
    _set_job(workflow_id, org_id=current_user["org_id"], status="running",
             progress=f"Temporal workflow started: {workflow_id}",
             controls_done=0, controls_total=total, started_at=started)

    logger.info(f"Temporal workflow started: {workflow_id}")
    return JobStatus(job_id=workflow_id, status="running", progress=f"Temporal workflow started: {workflow_id}",
                     controls_done=0, controls_total=total, started_at=started)


def _owned_job_or_404(job_id: str, caller: dict) -> dict:
    """Fetch a job and 404 if it belongs to another org (unless SUPERADMIN)."""
    job = _get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    job_org = job.get("org_id")
    # caller.role is read off the dict so this works under ALLOW_ANONYMOUS too.
    if job_org and job_org != caller["org_id"] and caller.get("role") != "SUPERADMIN":
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@router.get("/status", response_model=JobStatus)
def get_job_status(job_id: str, current_user: dict = Depends(get_current_user)):
    """Check the status of an SSP generation job."""
    job = _owned_job_or_404(job_id, current_user)

    return JobStatus(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        controls_done=job["controls_done"],
        controls_total=job["controls_total"],
        docx_path=job.get("docx_path"),
        started_at=str(job["started_at"]) if job.get("started_at") else None,
        completed_at=str(job["completed_at"]) if job.get("completed_at") else None,
        error=job.get("error"),
    )


@router.post("/cancel", response_model=JobStatus)
def cancel_job(job_id: str, current_user: dict = Depends(get_current_user)):
    """Request cancellation of a running SSP generation job.

    Cooperative: the background loop checks this flag between controls, so
    cancellation takes effect within the current control iteration (~10–20s).
    No-op if the job is already completed / failed / cancelled.
    """
    job = _owned_job_or_404(job_id, current_user)

    if job["status"] not in ("pending", "running"):
        return JobStatus(
            job_id=job["job_id"],
            status=job["status"],
            progress=job["progress"],
            controls_done=job["controls_done"],
            controls_total=job["controls_total"],
            docx_path=job.get("docx_path"),
            started_at=str(job["started_at"]) if job.get("started_at") else None,
            completed_at=str(job["completed_at"]) if job.get("completed_at") else None,
            error=job.get("error"),
        )

    _set_job(job_id, status="cancelled", progress=f"Cancelled at {job.get('progress', '')}")
    job = _get_job(job_id)
    return JobStatus(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        controls_done=job["controls_done"],
        controls_total=job["controls_total"],
        docx_path=job.get("docx_path"),
        started_at=str(job["started_at"]) if job.get("started_at") else None,
        completed_at=str(job["completed_at"]) if job.get("completed_at") else None,
        error=job.get("error"),
    )


@router.get("/exports")
def list_exports(current_user: dict = Depends(get_current_user)):
    """List SSP DOCX exports visible to the caller.

    Pulls filenames from ssp_jobs filtered by org_id so a user can only see
    their org's exports. Also cross-checks the exports directory so we
    don't show rows for files that were wiped by a deploy.
    """
    from src.db.session import engine
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT docx_path FROM ssp_jobs
            WHERE org_id = :org_id AND docx_path IS NOT NULL
        """), {"org_id": current_user["org_id"]}).fetchall()
    files = sorted({r[0] for r in rows if r[0]}, reverse=True)
    # Keep only those still on disk (filesystem may have been wiped on Render).
    if os.path.isdir(EXPORT_DIR):
        on_disk = set(os.listdir(EXPORT_DIR))
        files = [f for f in files if f in on_disk]
    return {"files": files, "count": len(files)}


@router.get("/export-latest")
def export_latest(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
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
    """), {"org_id": current_user["org_id"]}).fetchall()

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

    from src.agents.org_profile import build_org_profile, CompanyProfileMissing
    try:
        org_profile = build_org_profile(current_user["org_id"], db)
    except CompanyProfileMissing:
        raise HTTPException(400, "Organization must complete onboarding before exporting SSP.")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    org_slug = org_profile.get("name", "Organization").replace(" ", "_")[:30]
    filename = f"SSP_{org_slug}_{timestamp}.docx"
    filepath = os.path.join(EXPORT_DIR, filename)

    try:
        from src.ssp.docx_export import export_ssp_to_docx
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
def export_pdf(current_user: dict = Depends(get_current_user)):
    """Generate a fresh PDF from the current ssp_sections in the DB.

    Uses fpdf2 (pure Python) — no external dependencies like Word or LibreOffice.
    """
    from src.ssp.pdf_export import generate_ssp_pdf

    org_id = current_user["org_id"]
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
def get_narrative(control_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Get the SSP narrative for a single control."""
    from sqlalchemy import text as sa_text

    row = db.execute(sa_text("""
        SELECT narrative, implementation_status, review_status,
               original_narrative IS NOT NULL AS has_original,
               detector_findings, flagged_at
        FROM ssp_sections
        WHERE control_id = :cid AND org_id = :oid
        ORDER BY version DESC LIMIT 1
    """), {"cid": control_id, "oid": current_user["org_id"]}).fetchone()

    if not row:
        return {"control_id": control_id, "narrative": None, "implementation_status": None}

    return {
        "control_id": control_id,
        "narrative": row[0],
        "implementation_status": row[1],
        "review_status": row[2] or "CLEAN",
        "has_original_narrative": bool(row[3]),
        "detector_findings": row[4] if row[2] and row[2] != "CLEAN" else None,
        "flagged_at": row[5].isoformat() if row[5] else None,
    }


@router.get("/sections/{control_id}/original-narrative")
def get_original_narrative(
    control_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve the preserved original narrative before detector conversion."""
    from sqlalchemy import text as sa_text
    row = db.execute(sa_text("""
        SELECT original_narrative, detector_findings
        FROM ssp_sections
        WHERE control_id = :cid AND org_id = :oid AND original_narrative IS NOT NULL
        ORDER BY version DESC LIMIT 1
    """), {"cid": control_id, "oid": current_user["org_id"]}).fetchone()
    if not row:
        raise HTTPException(404, "No preserved original narrative for this control")
    return {
        "control_id": control_id,
        "original_narrative": row[0],
        "detector_findings": row[1],
    }


@router.post("/sections/{control_id}/review")
def review_section(
    control_id: str,
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Accept or reject a flagged SSP section."""
    from sqlalchemy import text as sa_text

    action = (body.get("action") or "").upper()
    if action not in ("ACCEPT", "REJECT"):
        raise HTTPException(400, "action must be ACCEPT or REJECT")

    now = datetime.datetime.now(datetime.timezone.utc)

    if action == "ACCEPT":
        db.execute(sa_text("""
            UPDATE ssp_sections SET review_status = 'REVIEWED_ACCEPTED',
                reviewed_at = :now, reviewed_by = :by
            WHERE control_id = :cid AND org_id = :oid
        """), {"cid": control_id, "oid": current_user["org_id"],
               "now": now, "by": current_user["id"]})
    else:
        # REJECT: restore original narrative
        db.execute(sa_text("""
            UPDATE ssp_sections SET
                narrative = COALESCE(original_narrative, narrative),
                original_narrative = NULL,
                review_status = 'REVIEWED_REJECTED',
                reviewed_at = :now, reviewed_by = :by
            WHERE control_id = :cid AND org_id = :oid
        """), {"cid": control_id, "oid": current_user["org_id"],
               "now": now, "by": current_user["id"]})

    db.commit()
    return {"control_id": control_id, "review_status": f"REVIEWED_{action}D"}


@router.get("/download/{filename}")
def download_ssp(filename: str, current_user: dict = Depends(get_current_user)):
    """Download an SSP DOCX, but only if it belongs to the caller's org.

    The filename itself is not trusted for tenant scoping — we look it up
    in ssp_jobs (org_id-filtered) and 404 if no matching record exists.
    """
    safe_name = os.path.basename(filename)
    filepath = os.path.join(EXPORT_DIR, safe_name)
    if not os.path.abspath(filepath).startswith(os.path.abspath(EXPORT_DIR)):
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Ownership check — is there an ssp_jobs row for this filename + org?
    from src.db.session import engine
    if current_user.get("role") != "SUPERADMIN":
        with engine.connect() as conn:
            owner_row = conn.execute(text("""
                SELECT 1 FROM ssp_jobs
                WHERE docx_path = :fn AND org_id = :oid
                LIMIT 1
            """), {"fn": safe_name, "oid": current_user["org_id"]}).fetchone()
        if not owner_row:
            raise HTTPException(status_code=404, detail="File not found")

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=safe_name,
    )
