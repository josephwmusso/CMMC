"""
src/workflows/trigger_ssp.py

CLI helper to kick off SSPGenerationWorkflow via Temporal.

Usage:
    cd D:/cmmc-platform
    .\venv\Scripts\Activate.ps1
    python -m src.workflows.trigger_ssp
    python -m src.workflows.trigger_ssp --org-id 9de53b587b23450b87af --controls AC.L2-3.1.1 AC.L2-3.1.2
"""

import asyncio
import argparse
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from temporalio.client import Client

from src.workflows.ssp_workflow import (
    TASK_QUEUE,
    SSPGenerationWorkflow,
    SSPWorkflowInput,
)
from src.agents.ssp_prompts_v2 import DEMO_ORG_PROFILE


async def trigger(org_id: str, control_ids: list | None, export_docx: bool):
    from configs.settings import TEMPORAL_HOST

    client = await Client.connect(TEMPORAL_HOST)

    inp = SSPWorkflowInput(
        org_id=org_id,
        org_name=DEMO_ORG_PROFILE["org_name"],
        system_name=DEMO_ORG_PROFILE["system_name"],
        system_description=DEMO_ORG_PROFILE["system_description"],
        employee_count=DEMO_ORG_PROFILE["employee_count"],
        facility_type=DEMO_ORG_PROFILE["facility_type"],
        tools_description=DEMO_ORG_PROFILE["tools_description"],
        network_description=DEMO_ORG_PROFILE["network_description"],
        control_ids=control_ids or None,
        export_docx=export_docx,
    )

    handle = await client.start_workflow(
        SSPGenerationWorkflow.run,
        inp,
        id=f"ssp-{org_id}-{asyncio.get_event_loop().time():.0f}",
        task_queue=TASK_QUEUE,
    )

    print(f"Workflow started: {handle.id}")
    print(f"Track at: http://localhost:8080/namespaces/default/workflows/{handle.id}")
    print("Waiting for result (Ctrl+C to detach)...")

    result = await handle.result()
    print(f"\nDone: {result.controls_succeeded}/{result.controls_total} controls generated")
    print(f"Statuses: {result.statuses}")
    if result.docx_path:
        print(f"Word doc: {result.docx_path}")
    if result.controls_failed:
        print(f"WARNING: {result.controls_failed} controls failed")


def main():
    parser = argparse.ArgumentParser(description="Trigger SSP generation workflow")
    parser.add_argument("--org-id", default="9de53b587b23450b87af")
    parser.add_argument("--controls", nargs="*", help="Specific control IDs (default: all 110)")
    parser.add_argument("--no-docx", action="store_true", help="Skip Word doc export")
    args = parser.parse_args()

    asyncio.run(trigger(args.org_id, args.controls, not args.no_docx))


if __name__ == "__main__":
    main()
