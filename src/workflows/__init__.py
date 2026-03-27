"""
src/workflows/

Temporal workflow definitions for long-running CMMC platform operations.

Workflows:
  SSPGenerationWorkflow  — generates all 110 SSP control narratives via LLM
  EvidenceReviewWorkflow — routes evidence through approval state machine

Workers:
  worker.py — run this process to register workflows/activities with Temporal

Usage:
    # Start the worker (keep running alongside FastAPI):
    python -m src.workflows.worker

    # Trigger SSP generation via Temporal client:
    python -m src.workflows.trigger_ssp
"""
