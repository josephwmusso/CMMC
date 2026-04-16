"""
src/api/routes_exports.py

Evidence binder export API (Phase 6.1). The binder ZIP is built
entirely in memory and streamed back — no temp files on disk.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.auth import get_current_user, ADMIN_ROLES
from src.db.session import get_db
from src.exports.binder import build_binder, preview_binder

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/exports", tags=["exports"])


def _gen_id(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()[:20]


def _safe_user_fk(db: Session, uid: str | None) -> str | None:
    if not uid:
        return None
    r = db.execute(text("SELECT 1 FROM users WHERE id = :id"), {"id": uid}).fetchone()
    return uid if r else None


def _audit(db: Session, *, actor: str, action: str, target_id: str, details: dict) -> None:
    try:
        from src.evidence.state_machine import create_audit_entry
        create_audit_entry(
            db=db, actor=actor, actor_type="user", action=action,
            target_type="export_record", target_id=target_id, details=details,
        )
    except Exception:
        logger.exception("audit %s failed", action)


def _require_admin(user: dict) -> None:
    if user.get("role") not in ADMIN_ROLES:
        raise HTTPException(403, "Admin required")


@router.get("/preview")
def export_preview(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Summary of what a binder export would contain, without generating it."""
    return preview_binder(user["org_id"], db)


@router.post("/binder")
def export_binder(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Build and stream the full C3PAO-ready ZIP."""
    _require_admin(user)
    org_id = user["org_id"]
    now = datetime.now(timezone.utc)

    zip_bytes = build_binder(org_id, db, user["id"])

    # Compute package hash from the manifest inside the ZIP
    # (re-parse the manifest we just wrote — simpler than plumbing it out)
    import zipfile, io
    pkg_hash = None
    artifact_count = 0
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            if "04_Manifest.json" in zf.namelist():
                manifest = json.loads(zf.read("04_Manifest.json"))
                pkg_hash = manifest.get("package_hash")
                artifact_count = manifest.get("artifact_count", 0)
    except Exception:
        pass

    # Record the export
    safe_user = _safe_user_fk(db, user["id"])
    org_row = db.execute(
        text("SELECT name FROM organizations WHERE id = :o"), {"o": org_id},
    ).fetchone()
    org_slug = (org_row.name if org_row else org_id).replace(" ", "_")[:30]
    filename = f"intranest_binder_{org_slug}_{now.strftime('%Y%m%d')}.zip"

    export_id = _gen_id(f"export:{org_id}:{now.isoformat()}")
    db.execute(text("""
        INSERT INTO export_records
            (id, org_id, export_type, filename, file_size_bytes,
             package_hash, artifact_count, created_at, created_by)
        VALUES
            (:id, :o, 'BINDER_ZIP', :fn, :sz,
             :hash, :ac, :now, :by)
    """), {
        "id":   export_id,
        "o":    org_id,
        "fn":   filename,
        "sz":   len(zip_bytes),
        "hash": pkg_hash,
        "ac":   artifact_count,
        "now":  now,
        "by":   safe_user,
    })

    _audit(
        db, actor=safe_user or "system", action="BINDER_EXPORTED",
        target_id=export_id,
        details={
            "org_id":         org_id,
            "filename":       filename,
            "size_bytes":     len(zip_bytes),
            "package_hash":   pkg_hash,
            "artifact_count": artifact_count,
        },
    )
    db.commit()

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/history")
def export_history(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Past exports for the org."""
    rows = db.execute(text("""
        SELECT id, export_type, filename, file_size_bytes,
               package_hash, artifact_count, created_at
        FROM export_records
        WHERE org_id = :o
        ORDER BY created_at DESC
    """), {"o": user["org_id"]}).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/{export_id}/receipt")
def export_receipt(
    export_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Metadata for a specific export — used to verify an old package hash."""
    row = db.execute(text("""
        SELECT id, export_type, filename, file_size_bytes,
               package_hash, artifact_count, created_at, created_by
        FROM export_records
        WHERE id = :id AND org_id = :o
    """), {"id": export_id, "o": user["org_id"]}).fetchone()
    if not row:
        raise HTTPException(404, "Export not found")
    return dict(row._mapping)
