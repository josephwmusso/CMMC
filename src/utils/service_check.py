"""Service availability checks for graceful degradation."""
import os


def is_qdrant_available() -> bool:
    return os.environ.get("QDRANT_AVAILABLE", "false") == "true"


def is_temporal_available() -> bool:
    return os.environ.get("TEMPORAL_AVAILABLE", "false") == "true"


def is_llm_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())


def get_deployment_type() -> str:
    if os.environ.get("RENDER"):
        return "render"
    return "local"
