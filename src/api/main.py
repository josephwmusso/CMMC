"""
src/api/main.py
FastAPI application entry point.
Run with: uvicorn src.api.main:app --reload --port 8000
"""
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.auth import router as auth_router
from src.api.ssp_routes import router as ssp_router
from src.api.evidence_routes import router as evidence_router
from src.api.scoring_routes import router as scoring_router
from src.api.intake_routes import router as intake_router
from src.api.document_routes import router as document_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="CMMC Compliance Platform API",
    description="Sovereign CMMC compliance AI platform for defense contractors.",
    version="0.9.0",
)

ALLOWED_ORIGINS = [
    os.getenv("FRONTEND_URL", "http://localhost:8501"),
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "https://intranest.ai",
    "https://www.intranest.ai",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(ssp_router)
app.include_router(evidence_router)
app.include_router(scoring_router)
app.include_router(intake_router)
app.include_router(document_router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.9.0"}


# ── Serve React frontend in production ────────────────────────────────────────
# This must be AFTER all API routes so /api/* takes priority.
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
