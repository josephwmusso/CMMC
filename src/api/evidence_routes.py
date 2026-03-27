"""
FastAPI routes for evidence management.
Upload, state transitions, control mapping, manifest export.

Auth: All write operations and org-scoped reads require a valid JWT.
org_id is ALWAYS extracted from the authenticated token — never trusted from user input.
"""
import os
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.auth import get_current_user, verify_org_access
from src.db.session import get_db
from src.evidence.hasher import generate_manifest, save_manifest, verify_hash
from src.evidence.state_machine import (
    StateTransitionError,
    transition_evidence,
    verify_audit_chain,
)
from src.evidence.storage import (
    get_artifact,
    get_published_artifacts,
    link_evidence_to_controls,
    list_artifacts,
    upload_evidence,
)

router = APIRouter(prefix="/api/evidence", tags=["evidence"])

# ── Upload limits & allowed types ─────────────────────────────────────────────
MAX_EVIDENCE_SIZE_MB = 100

_MAGIC_BYTES: list[tuple[bytes, str]] = [
    (b"%PDF",             "application/pdf"),
    (b"PK\x03\x04",      "application/zip"),
    (b"\xd0\xcf\x11\xe0","application/msword"),
    (b"\xff\xd8\xff",     "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n","image/png"),
    (b"GIF87a",           "image/gif"),
    (b"GIF89a",           "image/gif"),
    (b"BM",               "image/bmp"),
    (b"RIFF",             "image/webp"),
    (b"\x1f\x8b",         "application/gzip"),
]

ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".csv",
    ".png", ".jpg", ".jpeg", ".txt", ".json", ".xml",
    ".md",
}


def _validate_file(filename: str, file_bytes: bytes) -> str:
    """Validate size, extension, and magic bytes. Returns detected MIME type."""
    if len(file_bytes) > MAX_EVIDENCE_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {MAX_EVIDENCE_SIZE_MB}MB limit")
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(415, f"File type '{ext}' not allowed")
    detected_mime = None
    for magic, mime in _MAGIC_BYTES:
        if file_bytes[:len(magic)] == magic:
            detected_mime = mime
            break
    if detected_mime is None and ext in {".txt", ".csv", ".json", ".xml", ".md"}:
        detected_mime = "text/plain"
    if detected_mime is None:
        raise HTTPException(415, "File content does not match any allowed type")
    return detected_mime


# =============================================================================
# FIXED-PATH ROUTES — must be registered BEFORE /{artifact_id} catch-all
# =============================================================================

# ── List all artifacts ────────────────────────────────────────────────────────

@router.get("/")
def list_org_artifacts(
    state: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List artifacts for the authenticated user's organization."""
    artifacts = list_artifacts(db, current_user["org_id"], state=state, limit=limit)
    for a in artifacts:
        for k, v in a.items():
            if hasattr(v, "isoformat"):
                a[k] = v.isoformat()
    return {"count": len(artifacts), "artifacts": artifacts}


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_artifact(
    file: UploadFile = File(...),
    description: str = Form(""),
    source_system: str = Form("manual"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Upload an evidence artifact. org_id comes from JWT — never from request."""
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(400, "Empty file")
    _validate_file(file.filename, file_bytes)

    from configs.settings import EVIDENCE_DIR

    result = upload_evidence(
        db=db,
        org_id=current_user["org_id"],
        filename=file.filename,
        file_bytes=file_bytes,
        uploaded_by=current_user["email"],
        description=description,
        source_system=source_system,
        evidence_dir=EVIDENCE_DIR,
    )
    return result


# ── Manifest generation ───────────────────────────────────────────────────────

@router.post("/manifest/generate")
def generate_hash_manifest(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate a CMMC-format SHA-256 hash manifest for all published artifacts."""
    org_id = current_user["org_id"]
    published = get_published_artifacts(db, org_id)
    if not published:
        raise HTTPException(400, "No published artifacts found. Publish evidence first.")

    artifact_hashes = [
        {
            "filename": a["filename"],
            "sha256": a["sha256_hash"],
            "algorithm": "SHA-256",
            "file_size": a["file_size"],
        }
        for a in published
    ]

    org_row = db.execute(
        text("SELECT name FROM organizations WHERE id = :id"), {"id": org_id}
    ).fetchone()
    org_name = org_row[0] if org_row else org_id

    manifest_text = generate_manifest(artifact_hashes, org_name=org_name)
    from configs.settings import SSP_EXPORT_DIR
    filepath = save_manifest(
        manifest_text,
        output_dir=SSP_EXPORT_DIR,
        org_name=org_name.replace(" ", "_"),
    )
    return {
        "manifest_path": filepath,
        "artifact_count": len(artifact_hashes),
        "manifest_preview": manifest_text[:500],
    }


@router.get("/manifest/download")
def download_manifest(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate and download the manifest as a file."""
    result = generate_hash_manifest(db=db, current_user=current_user)
    return FileResponse(
        result["manifest_path"],
        media_type="text/plain",
        filename=os.path.basename(result["manifest_path"]),
    )


# ── Audit chain verification ─────────────────────────────────────────────────

@router.get("/audit/verify")
def verify_audit(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Verify the integrity of the hash-chained audit log."""
    result = verify_audit_chain(db, current_user["org_id"])
    return result


# ── Evidence by control ────────────────────────────────────────────────────────

@router.get("/by-control/{control_id}")
def get_evidence_by_control(
    control_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get all evidence artifacts linked to a specific control."""
    rows = db.execute(
        text("""
            SELECT ea.id, ea.filename, ea.state, ea.sha256_hash,
                   ea.file_size_bytes, ea.owner, ea.evidence_type,
                   ea.source_system, ea.description, ea.created_at,
                   ecm.objective_id, ecm.relevance_score
            FROM evidence_control_map ecm
            JOIN evidence_artifacts ea ON ea.id = ecm.evidence_id
            WHERE ecm.control_id = :control_id
              AND ea.org_id = :org_id
            ORDER BY ea.filename
        """),
        {"control_id": control_id, "org_id": current_user["org_id"]},
    ).fetchall()

    artifacts = []
    for r in rows:
        art = {
            "id": r[0],
            "filename": r[1],
            "state": r[2],
            "sha256_hash": r[3],
            "file_size_bytes": r[4],
            "owner": r[5],
            "evidence_type": r[6],
            "source_system": r[7],
            "description": r[8],
            "created_at": r[9].isoformat() if r[9] else None,
            "objective_id": r[10],
            "relevance_score": r[11],
        }
        artifacts.append(art)

    return {"control_id": control_id, "count": len(artifacts), "artifacts": artifacts}


# =============================================================================
# PARAMETERIZED ROUTES — /{artifact_id} catch-all MUST come after fixed paths
# =============================================================================

# ── Single artifact detail ────────────────────────────────────────────────────

@router.get("/{artifact_id}")
def get_artifact_detail(
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a single artifact's metadata."""
    artifact = get_artifact(db, artifact_id)
    if not artifact:
        raise HTTPException(404, f"Artifact {artifact_id} not found")
    verify_org_access(artifact["org_id"], current_user)
    for k, v in artifact.items():
        if hasattr(v, "isoformat"):
            artifact[k] = v.isoformat()
    return artifact


# ── State transitions ─────────────────────────────────────────────────────────

@router.post("/{artifact_id}/transition")
def transition_artifact(
    artifact_id: str,
    new_state: str,
    comment: str = "",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Transition an artifact's state. Actor = authenticated user."""
    artifact = get_artifact(db, artifact_id)
    if not artifact:
        raise HTTPException(404, f"Artifact {artifact_id} not found")
    verify_org_access(artifact["org_id"], current_user)

    try:
        result = transition_evidence(
            db=db,
            artifact_id=artifact_id,
            new_state=new_state,
            actor=current_user["email"],
            comment=comment,
        )
        return result
    except StateTransitionError as e:
        raise HTTPException(400, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))


# ── Control mapping ───────────────────────────────────────────────────────────

@router.post("/{artifact_id}/link-controls")
def link_to_controls(
    artifact_id: str,
    control_ids: list[str],
    objective_ids: list[str] | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Link an artifact to one or more controls and objectives."""
    artifact = get_artifact(db, artifact_id)
    if not artifact:
        raise HTTPException(404, f"Artifact {artifact_id} not found")
    verify_org_access(artifact["org_id"], current_user)
    count = link_evidence_to_controls(db, artifact_id, control_ids, objective_ids)
    return {"artifact_id": artifact_id, "links_created": count}


# ── Hash verification ─────────────────────────────────────────────────────────

@router.get("/{artifact_id}/verify")
def verify_artifact_hash(
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Verify a published artifact's file still matches its stored hash."""
    artifact = get_artifact(db, artifact_id)
    if not artifact:
        raise HTTPException(404, f"Artifact {artifact_id} not found")
    verify_org_access(artifact["org_id"], current_user)
    if artifact["state"] != "published":
        raise HTTPException(400, "Only published artifacts have hashes to verify")
    if not artifact["sha256_hash"]:
        raise HTTPException(400, "No hash stored for this artifact")
    is_valid = verify_hash(artifact["file_path"], artifact["sha256_hash"])
    return {
        "artifact_id": artifact_id,
        "filename": artifact["filename"],
        "expected_hash": artifact["sha256_hash"],
        "valid": is_valid,
        "status": "INTACT" if is_valid else "TAMPERED",
    }


# ── Evidence file download ────────────────────────────────────────────────────

@router.get("/{artifact_id}/preview")
def preview_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return file content as text for in-browser preview."""
    import base64

    artifact = get_artifact(db, artifact_id)
    if not artifact:
        raise HTTPException(404, f"Artifact {artifact_id} not found")
    verify_org_access(artifact["org_id"], current_user)

    file_path = artifact["file_path"]
    filename = artifact["filename"]
    ext = os.path.splitext(filename)[1].lower()

    if not os.path.exists(file_path):
        return {"content": None, "content_type": "missing", "filename": filename,
                "message": "File not found on disk"}

    TEXT_EXTS = {".md", ".csv", ".json", ".txt", ".xml", ".log", ".yaml", ".yml", ".ini", ".conf", ".cfg"}
    IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

    if ext in TEXT_EXTS:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            total_lines = len(lines)
            truncated = total_lines > 500
            content = "".join(lines[:500])
            return {"content": content, "content_type": "text", "filename": filename,
                    "lines": total_lines, "truncated": truncated, "ext": ext}
        except Exception as e:
            return {"content": None, "content_type": "error", "filename": filename,
                    "message": str(e)}

    if ext in IMAGE_EXTS:
        try:
            with open(file_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "gif": "image/gif", "bmp": "image/bmp", "webp": "image/webp"}
            return {"content": b64, "content_type": "image", "filename": filename,
                    "mime": mime.get(ext.lstrip("."), "image/png")}
        except Exception as e:
            return {"content": None, "content_type": "error", "filename": filename,
                    "message": str(e)}

    return {"content": None, "content_type": "binary", "filename": filename,
            "message": f"Preview not available for {ext} files"}


@router.get("/{artifact_id}/download")
def download_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Download an individual evidence artifact file. Auth + org scoped."""
    artifact = get_artifact(db, artifact_id)
    if not artifact:
        raise HTTPException(404, f"Artifact {artifact_id} not found")
    verify_org_access(artifact["org_id"], current_user)

    file_path = artifact["file_path"]
    from configs.settings import EVIDENCE_DIR
    evidence_base = os.path.abspath(EVIDENCE_DIR)
    abs_file = os.path.abspath(file_path)
    if not abs_file.startswith(evidence_base):
        raise HTTPException(403, "Access denied")
    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found on disk")
    return FileResponse(file_path, filename=artifact["filename"])
