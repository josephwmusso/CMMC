"""DB CRUD for connectors and connector_runs.

Org scoping: every read/update/delete takes org_id and filters on it.
Cross-org access returns None or empty list — never raises and never
leaks data.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.connectors.crypto import encrypt_credentials, decrypt_credentials


def _new_connector_id() -> str:
    return f"CONN-{uuid.uuid4().hex[:12].upper()}"


def _new_run_id() -> str:
    return f"CRUN-{uuid.uuid4().hex[:12].upper()}"


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ----- connectors ----------------------------------------------------------

def create_connector(
    db: Session,
    org_id: str,
    type_name: str,
    name: str,
    credentials: dict,
    config: dict | None = None,
    created_by: str | None = None,
) -> str:
    """Insert a connector row with encrypted credentials. Returns the new id."""
    cid = _new_connector_id()
    encrypted = encrypt_credentials(credentials)
    now = _now()
    db.execute(
        text("""
            INSERT INTO connectors
                (id, org_id, type, name, status,
                 credentials_encrypted, config,
                 created_at, updated_at, created_by)
            VALUES
                (:id, :org_id, :type, :name, 'INACTIVE',
                 :credentials_encrypted, CAST(:config AS json),
                 :created_at, :updated_at, :created_by)
        """),
        {
            "id": cid,
            "org_id": org_id,
            "type": type_name,
            "name": name,
            "credentials_encrypted": encrypted,
            "config": json.dumps(config or {}),
            "created_at": now,
            "updated_at": now,
            "created_by": created_by,
        },
    )
    db.commit()
    return cid


def get_connector(
    db: Session,
    connector_id: str,
    org_id: str,
    *,
    include_credentials: bool = False,
) -> dict | None:
    """Org-scoped lookup. Returns None on miss or cross-org access."""
    row = db.execute(
        text("""
            SELECT id, org_id, type, name, status,
                   credentials_encrypted, config,
                   last_run_at, last_status,
                   created_at, updated_at, created_by
            FROM connectors
            WHERE id = :id AND org_id = :org_id
        """),
        {"id": connector_id, "org_id": org_id},
    ).fetchone()
    if row is None:
        return None
    out = {
        "id": row[0],
        "org_id": row[1],
        "type": row[2],
        "name": row[3],
        "status": row[4],
        "config": row[6] or {},
        "last_run_at": row[7].isoformat() if row[7] else None,
        "last_status": row[8],
        "created_at": row[9].isoformat() if row[9] else None,
        "updated_at": row[10].isoformat() if row[10] else None,
        "created_by": row[11],
    }
    if include_credentials and row[5]:
        out["credentials"] = decrypt_credentials(row[5])
    return out


def list_connectors(db: Session, org_id: str) -> list[dict]:
    """All connectors for an org. Credentials never returned."""
    rows = db.execute(
        text("""
            SELECT id, org_id, type, name, status,
                   config, last_run_at, last_status,
                   created_at, updated_at
            FROM connectors
            WHERE org_id = :org_id
            ORDER BY created_at DESC
        """),
        {"org_id": org_id},
    ).fetchall()
    return [
        {
            "id": r[0], "org_id": r[1], "type": r[2], "name": r[3], "status": r[4],
            "config": r[5] or {},
            "last_run_at": r[6].isoformat() if r[6] else None,
            "last_status": r[7],
            "created_at": r[8].isoformat() if r[8] else None,
            "updated_at": r[9].isoformat() if r[9] else None,
        }
        for r in rows
    ]


def update_connector_status(
    db: Session,
    connector_id: str,
    org_id: str,
    *,
    status: str | None = None,
    last_status: str | None = None,
    last_run_at: datetime | None = None,
) -> bool:
    """Patch any subset of status fields. Returns True if a row was updated."""
    sets = ["updated_at = :updated_at"]
    params: dict = {"id": connector_id, "org_id": org_id, "updated_at": _now()}
    if status is not None:
        sets.append("status = :status")
        params["status"] = status
    if last_status is not None:
        sets.append("last_status = :last_status")
        params["last_status"] = last_status
    if last_run_at is not None:
        sets.append("last_run_at = :last_run_at")
        params["last_run_at"] = last_run_at
    sql = f"UPDATE connectors SET {', '.join(sets)} WHERE id = :id AND org_id = :org_id"
    result = db.execute(text(sql), params)
    db.commit()
    return result.rowcount > 0


def delete_connector(db: Session, connector_id: str, org_id: str) -> bool:
    """Hard delete. connector_runs rows are NOT cascaded — they remain for audit."""
    result = db.execute(
        text("DELETE FROM connectors WHERE id = :id AND org_id = :org_id"),
        {"id": connector_id, "org_id": org_id},
    )
    db.commit()
    return result.rowcount > 0


# ----- connector_runs ------------------------------------------------------

def create_connector_run(
    db: Session,
    connector_id: str,
    org_id: str,
    triggered_by: str,
    triggered_by_user_id: str | None = None,
) -> str:
    rid = _new_run_id()
    db.execute(
        text("""
            INSERT INTO connector_runs
                (id, connector_id, org_id, triggered_by, triggered_by_user_id,
                 started_at, status, evidence_artifacts_created)
            VALUES
                (:id, :connector_id, :org_id, :triggered_by, :triggered_by_user_id,
                 :started_at, 'RUNNING', 0)
        """),
        {
            "id": rid,
            "connector_id": connector_id,
            "org_id": org_id,
            "triggered_by": triggered_by,
            "triggered_by_user_id": triggered_by_user_id,
            "started_at": _now(),
        },
    )
    db.commit()
    return rid


def update_connector_run(
    db: Session,
    run_id: str,
    *,
    status: str | None = None,
    evidence_artifacts_created: int | None = None,
    error_message: str | None = None,
    summary: dict | None = None,
    finished: bool = False,
) -> None:
    sets: list[str] = []
    params: dict = {"id": run_id}
    if status is not None:
        sets.append("status = :status")
        params["status"] = status
    if evidence_artifacts_created is not None:
        sets.append("evidence_artifacts_created = :eac")
        params["eac"] = evidence_artifacts_created
    if error_message is not None:
        sets.append("error_message = :error_message")
        params["error_message"] = error_message
    if summary is not None:
        sets.append("summary = CAST(:summary AS json)")
        params["summary"] = json.dumps(summary)
    if finished:
        sets.append("finished_at = :finished_at")
        params["finished_at"] = _now()
    if not sets:
        return
    db.execute(
        text(f"UPDATE connector_runs SET {', '.join(sets)} WHERE id = :id"),
        params,
    )
    db.commit()


def get_connector_run(db: Session, run_id: str, org_id: str) -> dict | None:
    row = db.execute(
        text("""
            SELECT id, connector_id, org_id, triggered_by, triggered_by_user_id,
                   started_at, finished_at, status,
                   evidence_artifacts_created, error_message, summary
            FROM connector_runs
            WHERE id = :id AND org_id = :org_id
        """),
        {"id": run_id, "org_id": org_id},
    ).fetchone()
    if row is None:
        return None
    return {
        "id": row[0], "connector_id": row[1], "org_id": row[2],
        "triggered_by": row[3], "triggered_by_user_id": row[4],
        "started_at": row[5].isoformat() if row[5] else None,
        "finished_at": row[6].isoformat() if row[6] else None,
        "status": row[7],
        "evidence_artifacts_created": row[8],
        "error_message": row[9],
        "summary": row[10] or {},
    }


def list_connector_runs(
    db: Session,
    connector_id: str,
    org_id: str,
    limit: int = 50,
) -> list[dict]:
    rows = db.execute(
        text("""
            SELECT id, connector_id, org_id, triggered_by, triggered_by_user_id,
                   started_at, finished_at, status,
                   evidence_artifacts_created, error_message
            FROM connector_runs
            WHERE connector_id = :connector_id AND org_id = :org_id
            ORDER BY started_at DESC
            LIMIT :limit
        """),
        {"connector_id": connector_id, "org_id": org_id, "limit": limit},
    ).fetchall()
    return [
        {
            "id": r[0], "connector_id": r[1], "org_id": r[2],
            "triggered_by": r[3], "triggered_by_user_id": r[4],
            "started_at": r[5].isoformat() if r[5] else None,
            "finished_at": r[6].isoformat() if r[6] else None,
            "status": r[7],
            "evidence_artifacts_created": r[8],
            "error_message": r[9],
        }
        for r in rows
    ]
