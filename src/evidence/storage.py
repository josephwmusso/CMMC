"""
Evidence file storage — handles upload, path management, and metadata persistence.
Files stored in data/evidence/{org_id}/{artifact_id}_{filename}.
"""
import os
import uuid
import mimetypes
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def upload_evidence(
    db: Session,
    org_id: str,
    filename: str,
    file_bytes: bytes,
    uploaded_by: str,
    actor_type: str = "user",
    description: str = "",
    source_system: str = "manual",
    evidence_dir: str = os.path.join("data", "evidence"),
) -> dict:
    """
    Store an evidence file and create the evidence_artifacts DB record.
    Returns dict with artifact metadata including the generated ID.
    """
    artifact_id = f"EVD-{uuid.uuid4().hex[:12].upper()}"

    # Org-scoped directory
    org_dir = os.path.join(evidence_dir, org_id)
    _ensure_dir(org_dir)

    # Safe filename: {artifact_id}_{original_name}
    safe_name = f"{artifact_id}_{filename}"
    file_path = os.path.join(org_dir, safe_name)

    # Write file
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Detect MIME type
    mime_type, _ = mimetypes.guess_type(filename)
    mime_type = mime_type or "application/octet-stream"

    now = datetime.now(timezone.utc)

    # Insert into evidence_artifacts — using ACTUAL column names
    db.execute(
        text(
            """
            INSERT INTO evidence_artifacts
                (id, org_id, filename, file_path, file_size_bytes, mime_type,
                 state, owner, description, source_system,
                 created_at, updated_at)
            VALUES
                (:id, :org_id, :filename, :file_path, :file_size_bytes, :mime_type,
                 'DRAFT', :owner, :description, :source_system,
                 :created_at, :updated_at)
            """
        ),
        {
            "id": artifact_id,
            "org_id": org_id,
            "filename": filename,
            "file_path": file_path,
            "file_size_bytes": len(file_bytes),
            "mime_type": mime_type,
            "owner": uploaded_by,
            "description": description,
            "source_system": source_system,
            "created_at": now,
            "updated_at": now,
        },
    )
    # Genesis audit entry — every artifact starts its chain at creation
    from src.evidence.state_machine import create_audit_entry
    create_audit_entry(
        db=db,
        actor=uploaded_by,
        actor_type=actor_type,
        action="evidence.created",
        target_type="evidence_artifact",
        target_id=artifact_id,
        details={"filename": filename, "org_id": org_id, "description": description},
    )

    db.commit()

    return {
        "artifact_id": artifact_id,
        "filename": filename,
        "file_path": file_path,
        "file_size": len(file_bytes),
        "mime_type": mime_type,
        "state": "draft",
        "uploaded_by": uploaded_by,
        "created_at": now.isoformat(),
    }


def link_evidence_to_controls(
    db: Session,
    artifact_id: str,
    control_ids: list[str],
    objective_ids: list[str] | None = None,
    mapped_by: str = "manual",
) -> int:
    """
    Link an evidence artifact to one or more controls/objectives
    via the evidence_control_map table.
    Returns count of links created.
    """
    # Defensive guard: evidence_control_map.control_id is NOT NULL in the
    # schema, but the objective-only INSERT branch below does not supply it.
    # No current caller exercises this path (PulledEvidence only carries
    # control_ids; the runner never passes objective_ids). Convert a future
    # regression from a Postgres FK error into a clear application error.
    # Backlog: Phase 5.2.bug-1.
    if not control_ids and objective_ids:
        raise ValueError(
            "control_ids required: objective-only linkage path is not yet "
            "supported (NOT NULL constraint on evidence_control_map.control_id). "
            "Track via backlog item Phase 5.2.bug-1."
        )

    count = 0
    for control_id in control_ids:
        link_id = f"ECM-{uuid.uuid4().hex[:12].upper()}"
        db.execute(
            text(
                """
                INSERT INTO evidence_control_map (id, evidence_id, control_id, mapped_by)
                VALUES (:id, :evidence_id, :control_id, :mapped_by)
                ON CONFLICT DO NOTHING
                """
            ),
            {"id": link_id, "evidence_id": artifact_id, "control_id": control_id,
             "mapped_by": mapped_by},
        )
        count += 1

    if objective_ids:
        for obj_id in objective_ids:
            link_id = f"ECM-{uuid.uuid4().hex[:12].upper()}"
            db.execute(
                text(
                    """
                    INSERT INTO evidence_control_map (id, evidence_id, objective_id, mapped_by)
                    VALUES (:id, :evidence_id, :objective_id, :mapped_by)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"id": link_id, "evidence_id": artifact_id, "objective_id": obj_id,
                 "mapped_by": mapped_by},
            )
            count += 1

    db.commit()
    return count


def get_artifact(db: Session, artifact_id: str) -> dict | None:
    """Fetch a single artifact's metadata."""
    row = db.execute(
        text("SELECT * FROM evidence_artifacts WHERE id = :id"),
        {"id": artifact_id},
    ).fetchone()
    if not row:
        return None
    # Map actual DB columns to our dict keys
    columns = [
        "id", "org_id", "filename", "file_path", "file_size_bytes", "mime_type",
        "sha256_hash", "hash_algorithm", "state", "evidence_type", "source_system",
        "description", "owner", "created_at", "updated_at", "reviewed_at",
        "reviewed_by", "approved_at", "approved_by", "published_at", "metadata_json",
    ]
    d = dict(zip(columns, row))
    # Alias for consistency in our code
    d["file_size"] = d["file_size_bytes"]
    d["uploaded_by"] = d["owner"]
    return d


def list_artifacts(
    db: Session,
    org_id: str,
    state: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """List artifacts for an org, optionally filtered by state."""
    query = "SELECT * FROM evidence_artifacts WHERE org_id = :org_id"
    params: dict = {"org_id": org_id, "limit": limit}

    if state:
        query += " AND state = :state"
        params["state"] = state.upper()
    query += " ORDER BY created_at DESC LIMIT :limit"

    rows = db.execute(text(query), params).fetchall()
    columns = [
        "id", "org_id", "filename", "file_path", "file_size_bytes", "mime_type",
        "sha256_hash", "hash_algorithm", "state", "evidence_type", "source_system",
        "description", "owner", "created_at", "updated_at", "reviewed_at",
        "reviewed_by", "approved_at", "approved_by", "published_at", "metadata_json",
    ]
    results = []
    for r in rows:
        d = dict(zip(columns, r))
        d["file_size"] = d["file_size_bytes"]
        d["uploaded_by"] = d["owner"]
        results.append(d)
    return results


def get_published_artifacts(db: Session, org_id: str) -> list[dict]:
    """Get all published (hashed, immutable) artifacts for manifest generation."""
    return list_artifacts(db, org_id, state="published", limit=10000)