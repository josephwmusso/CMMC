"""
configs/settings.py

Central configuration. All components read from here.
Environment variables override defaults for deployment.
"""

import os
from dotenv import load_dotenv

# Load .env file if present (dev). In production, env vars are set directly.
load_dotenv()

# ---------------------------------------------------------------------------
# LLM Configuration
# ---------------------------------------------------------------------------
# During development: use Claude API
# In production: swap to vLLM endpoint (same OpenAI-compatible interface)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")  # "anthropic" or "openai_compatible"
LLM_API_KEY = os.getenv("ANTHROPIC_API_KEY", "your-key-here")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")

# For sovereign deployment (vLLM):
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:8000/v1")
# To switch to vLLM, set these env vars:
#   LLM_PROVIDER=openai_compatible
#   LLM_BASE_URL=http://localhost:8000/v1
#   LLM_MODEL=meta-llama/Llama-3.3-70B-Instruct

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cmmc:localdev@localhost:5432/cmmc")
# Render uses postgres:// scheme — SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ---------------------------------------------------------------------------
# Qdrant
# ---------------------------------------------------------------------------
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_URL = os.getenv("QDRANT_URL", "").strip() or None
if QDRANT_URL is None and QDRANT_HOST != "localhost":
    QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_PORT}"
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "nist_compliance")

# ---------------------------------------------------------------------------
# Temporal
# ---------------------------------------------------------------------------
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "").strip() or None

# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------
EVIDENCE_DIR = os.getenv("EVIDENCE_DIR", os.path.join("data", "evidence"))
HASH_ALGORITHM = "sha256"

# ---------------------------------------------------------------------------
# Embedding model
# ---------------------------------------------------------------------------
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

# ---------------------------------------------------------------------------
# SSP Export
# ---------------------------------------------------------------------------
SSP_EXPORT_DIR = os.getenv("SSP_EXPORT_DIR", os.path.join("data", "exports"))

# ---------------------------------------------------------------------------
# Auth / JWT
# ---------------------------------------------------------------------------
# Module-level constants (no Settings class) to match the rest of this file.
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))          # 24 h access
JWT_REFRESH_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))    # 7 d refresh

# Anonymous demo bypass: when true, missing Authorization headers fall back
# to the built-in demo user so the frontend works without a real login.
ALLOW_ANONYMOUS = os.getenv("ALLOW_ANONYMOUS", "true").lower() == "true"

# Warn once at import time if a production-style deployment forgot to set
# a real secret.
if not ALLOW_ANONYMOUS and JWT_SECRET_KEY == "dev-secret-change-in-production":
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "ALLOW_ANONYMOUS=false but JWT_SECRET_KEY is the dev default — "
        "set JWT_SECRET_KEY to a real secret for production.",
    )
