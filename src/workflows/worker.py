"""
src/workflows/worker.py

Temporal worker process — registers all workflows and activities.

Run alongside FastAPI:
    cd D:/cmmc-platform
    .\venv\Scripts\Activate.ps1
    python -m src.workflows.worker

The worker connects to Temporal at localhost:7233, registers on the
"cmmc-ssp" task queue, and polls for work.
"""

import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from temporalio.client import Client
from temporalio.worker import Worker

from src.workflows.ssp_workflow import (
    TASK_QUEUE,
    SSPGenerationWorkflow,
    generate_ssp_control_activity,
    get_all_control_ids_activity,
    export_ssp_docx_activity,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    from configs.settings import TEMPORAL_HOST

    logger.info(f"Connecting to Temporal at {TEMPORAL_HOST}")
    client = await Client.connect(TEMPORAL_HOST)

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[SSPGenerationWorkflow],
        activities=[
            generate_ssp_control_activity,
            get_all_control_ids_activity,
            export_ssp_docx_activity,
        ],
    )

    logger.info(f"Worker started on task queue '{TASK_QUEUE}'. Waiting for work...")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
