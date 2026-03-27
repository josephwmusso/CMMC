"""
src/workflows/ssp_workflow.py

Temporal workflow + activities for SSP generation.

Architecture:
  - SSPGenerationWorkflow: orchestrates generation of all 110 controls
  - generate_ssp_control_activity: one activity per control (LLM call + DB persist)
  - export_ssp_docx_activity: runs after all controls complete, exports Word doc

The workflow fans out control generation as individual activities so Temporal
can retry failed LLM calls, checkpoint progress, and resume from any failure.

Task queue: "cmmc-ssp"
"""

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from temporalio import activity, workflow
from temporalio.common import RetryPolicy

logger = logging.getLogger(__name__)

TASK_QUEUE = "cmmc-ssp"


# ---------------------------------------------------------------------------
# Shared input/output types
# ---------------------------------------------------------------------------

@dataclass
class SSPWorkflowInput:
    org_id: str
    org_name: str
    system_name: str
    system_description: str
    employee_count: int
    facility_type: str
    tools_description: str
    network_description: str
    control_ids: Optional[list] = None   # None = all 110
    export_docx: bool = True


@dataclass
class SSPControlActivityInput:
    control_id: str
    org_profile: dict


@dataclass
class SSPControlActivityResult:
    control_id: str
    status: str
    narrative: str
    gaps: list
    evidence_artifacts: list
    generation_time_sec: float
    error: Optional[str] = None


@dataclass
class SSPWorkflowResult:
    org_id: str
    controls_total: int
    controls_succeeded: int
    controls_failed: int
    docx_path: Optional[str]
    statuses: dict   # e.g. {"Implemented": 60, "Partially Implemented": 30, ...}


# ---------------------------------------------------------------------------
# Activities (run in the worker process, can use blocking I/O)
# ---------------------------------------------------------------------------

@activity.defn(name="generate_ssp_control")
async def generate_ssp_control_activity(inp: SSPControlActivityInput) -> SSPControlActivityResult:
    """Generate + persist SSP narrative for a single control."""
    import asyncio
    import sys
    import os

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

    from src.agents.ssp_generator_v2 import SSPGenerator
    from src.agents.llm_client import get_llm
    from src.db.session import SessionLocal

    db = SessionLocal()
    try:
        llm = get_llm()
        generator = SSPGenerator(llm=llm)

        # Run the blocking LLM call in a thread pool so Temporal's event loop stays free
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: generator.generate_single_control(
                control_id=inp.control_id,
                org_profile=inp.org_profile,
                db=db,
            ),
        )

        return SSPControlActivityResult(
            control_id=result.control_id,
            status=result.status,
            narrative=result.narrative,
            gaps=result.gaps,
            evidence_artifacts=result.evidence_artifacts,
            generation_time_sec=round(result.generation_time_sec, 2),
            error=result.error,
        )
    finally:
        db.close()


@activity.defn(name="get_all_control_ids")
async def get_all_control_ids_activity(org_id: str) -> list:
    """Fetch the list of all 110 control IDs from Postgres."""
    import sys
    import os

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

    from src.db.session import SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    try:
        rows = db.execute(text("SELECT id FROM controls ORDER BY id")).fetchall()
        return [r[0] for r in rows]
    finally:
        db.close()


@activity.defn(name="export_ssp_docx")
async def export_ssp_docx_activity(inp: dict) -> str:
    """Export completed SSP results to a Word document. Returns the file path."""
    import asyncio
    import sys
    import os
    import datetime

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

    from src.ssp.docx_export import export_ssp_to_docx
    from src.agents.ssp_generator_v2 import SSPControlResult

    results = [
        SSPControlResult(
            control_id=r["control_id"],
            status=r["status"],
            narrative=r["narrative"],
            gaps=r["gaps"],
            evidence_artifacts=r["evidence_artifacts"],
            generation_time_sec=r["generation_time_sec"],
            error=r.get("error"),
        )
        for r in inp["results"]
    ]

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    org_name_slug = inp["org_profile"].get("org_name", "org").replace(" ", "_")
    filename = f"SSP_{org_name_slug}_{timestamp}.docx"
    export_dir = os.path.join("data", "exports")
    os.makedirs(export_dir, exist_ok=True)
    docx_path = os.path.join(export_dir, filename)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: export_ssp_to_docx(results, inp["org_profile"], docx_path),
    )

    return docx_path


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------

@workflow.defn(name="SSPGenerationWorkflow")
class SSPGenerationWorkflow:
    """
    Orchestrates full SSP generation for an organization.

    Steps:
      1. Fetch control ID list from Postgres (or use caller-supplied list)
      2. For each control: run generate_ssp_control activity (retried up to 3x)
      3. Collect results, tally statuses
      4. Optionally export Word doc

    The workflow is durable — if the worker crashes mid-way, Temporal replays
    from the last completed activity checkpoint.
    """

    @workflow.run
    async def run(self, inp: SSPWorkflowInput) -> SSPWorkflowResult:
        logger = workflow.logger

        org_profile = {
            "org_id": inp.org_id,
            "org_name": inp.org_name,
            "system_name": inp.system_name,
            "system_description": inp.system_description,
            "employee_count": inp.employee_count,
            "facility_type": inp.facility_type,
            "tools_description": inp.tools_description,
            "network_description": inp.network_description,
        }

        # Step 1: Get control list
        if inp.control_ids:
            control_ids = inp.control_ids
        else:
            control_ids = await workflow.execute_activity(
                get_all_control_ids_activity,
                inp.org_id,
                start_to_close_timeout=timedelta(seconds=30),
            )

        total = len(control_ids)
        logger.info(f"SSPGenerationWorkflow starting: {total} controls for org={inp.org_id}")

        # Step 2: Generate each control (sequential to respect API rate limits)
        results = []
        for control_id in control_ids:
            result = await workflow.execute_activity(
                generate_ssp_control_activity,
                SSPControlActivityInput(
                    control_id=control_id,
                    org_profile=org_profile,
                ),
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=5),
                    backoff_coefficient=2.0,
                ),
            )
            results.append(result)

        # Step 3: Tally
        succeeded = sum(1 for r in results if not r.error)
        failed = sum(1 for r in results if r.error)
        statuses: dict = {}
        for r in results:
            if not r.error:
                statuses[r.status] = statuses.get(r.status, 0) + 1

        # Step 4: Export docx
        docx_path = None
        if inp.export_docx and succeeded > 0:
            serializable_results = [
                {
                    "control_id": r.control_id,
                    "status": r.status,
                    "narrative": r.narrative,
                    "gaps": r.gaps,
                    "evidence_artifacts": r.evidence_artifacts,
                    "generation_time_sec": r.generation_time_sec,
                    "error": r.error,
                }
                for r in results
                if not r.error
            ]
            docx_path = await workflow.execute_activity(
                export_ssp_docx_activity,
                {"results": serializable_results, "org_profile": org_profile},
                start_to_close_timeout=timedelta(minutes=2),
            )

        logger.info(
            f"SSPGenerationWorkflow complete: {succeeded}/{total} succeeded, "
            f"statuses={statuses}, docx={docx_path}"
        )

        return SSPWorkflowResult(
            org_id=inp.org_id,
            controls_total=total,
            controls_succeeded=succeeded,
            controls_failed=failed,
            docx_path=docx_path,
            statuses=statuses,
        )
