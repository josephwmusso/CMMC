"""
src/api/main.py
FastAPI application entry point.
"""
import logging
import os
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CMMC Compliance Platform API",
    description="Sovereign CMMC compliance AI platform for defense contractors.",
    version="0.9.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global exception handler — never return an unhandled 500 ──────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url.path),
        },
    )


# ── Import routers with graceful fallback ─────────────────────────────────────

from src.api.auth import router as auth_router
app.include_router(auth_router)

from src.api.scoring_routes import router as scoring_router
app.include_router(scoring_router)

from src.api.contact_routes import router as contact_router
app.include_router(contact_router)

# These routers may fail to import if dependencies are missing on Render
for router_import in [
    ("src.api.ssp_routes", "ssp"),
    ("src.api.evidence_routes", "evidence"),
    ("src.api.intake_routes", "intake"),
    ("src.api.document_routes", "documents"),
    ("src.api.admin_routes", "admin"),
    ("src.api.onboarding_routes", "onboarding"),
    ("src.api.contradiction_routes", "contradictions"),
    ("src.api.routes_scans", "scans"),
    ("src.baselines.routes", "baselines"),
    ("src.api.routes_claims", "claims"),
    ("src.api.routes_observations", "observations"),
    ("src.api.routes_resolutions", "resolutions"),
    ("src.api.routes_freshness", "freshness"),
    ("src.api.routes_assessments", "assessments"),
    ("src.api.routes_exports", "exports"),
]:
    module_path, name = router_import
    try:
        import importlib
        mod = importlib.import_module(module_path)
        app.include_router(mod.router)
        logger.info(f"Router loaded: {name}")
    except Exception as e:
        logger.warning(f"Router {name} failed to load: {e}")


# ── Health check (no auth required) ──────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.9.0"}


@app.get("/api/health")
def api_health():
    return {
        "status": "ok",
        "version": "0.9.0",
        "services": {
            "postgres": True,
            "qdrant": os.environ.get("QDRANT_AVAILABLE", "false") == "true",
            "temporal": os.environ.get("TEMPORAL_AVAILABLE", "false") == "true",
            "llm": bool(os.environ.get("ANTHROPIC_API_KEY", "").strip()),
        },
        "deployment": "render" if os.environ.get("RENDER") else "local",
    }


@app.get("/debug/tables")
def debug_tables():
    from sqlalchemy import text
    from src.db.session import engine
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")).fetchall()
        tables = [r[0] for r in rows]
        user_count = None
        try:
            user_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
        except Exception as e:
            user_count = f"ERROR: {e}"
        return {"tables": tables, "table_count": len(tables), "user_count": user_count}


# ── Serve React frontend in production ────────────────────────────────────────
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'dist')
if os.path.exists(frontend_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dir, "assets")), name="assets")

    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        file_path = os.path.join(frontend_dir, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dir, "index.html"))
