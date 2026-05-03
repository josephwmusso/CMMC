"""REST API for the Phase 5.1 connector framework.

Endpoints:
    GET    /api/connectors/types               — list registered connector types (any user)
    GET    /api/connectors/                    — list this org's connectors (any user)
    POST   /api/connectors/                    — create connector (admin)
    GET    /api/connectors/{id}                — get one connector (any user, org-scoped)
    DELETE /api/connectors/{id}                — delete connector (admin)
    POST   /api/connectors/{id}/test           — call test_connection() without creating a run (admin)
    POST   /api/connectors/{id}/run            — trigger a manual run (admin)
    GET    /api/connectors/{id}/runs           — list runs for one connector (any user)
    GET    /api/connectors/runs/{run_id}       — get one run (any user, org-scoped)

Org scoping rule: org_id is ALWAYS extracted from current_user["org_id"].
Never trusted from query params or request body.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.auth import get_current_user, require_admin_dep
from src.connectors import registry as reg
from src.connectors import storage as cstore
from src.connectors.runner import run_connector
from src.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/connectors", tags=["connectors"])


# ----- request bodies ------------------------------------------------------

class CreateConnectorBody(BaseModel):
    type: str = Field(..., description="Registered connector type_name")
    name: str = Field(..., min_length=1, max_length=255)
    credentials: dict[str, Any] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)


# ----- read endpoints ------------------------------------------------------

@router.get("/types")
def list_connector_types(
    current_user: dict = Depends(get_current_user),
):
    """All registered connector types. No org scoping needed — this is a class-level catalog."""
    return {"types": reg.list_types()}


@router.get("/")
def list_org_connectors(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    items = cstore.list_connectors(db, current_user["org_id"])
    return {"count": len(items), "connectors": items}


@router.get("/{connector_id}")
def get_one_connector(
    connector_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    row = cstore.get_connector(db, connector_id, current_user["org_id"])
    if row is None:
        raise HTTPException(status_code=404, detail="Connector not found")
    return row


@router.get("/{connector_id}/runs")
def list_runs_for_connector(
    connector_id: str,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Verify the connector belongs to the caller's org first.
    if cstore.get_connector(db, connector_id, current_user["org_id"]) is None:
        raise HTTPException(status_code=404, detail="Connector not found")
    runs = cstore.list_connector_runs(db, connector_id, current_user["org_id"], limit=limit)
    return {"count": len(runs), "runs": runs}


@router.get("/runs/{run_id}")
def get_one_run(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    run = cstore.get_connector_run(db, run_id, current_user["org_id"])
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


# ----- mutating endpoints (admin only) -------------------------------------

@router.post("/", status_code=201)
def create_one_connector(
    body: CreateConnectorBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin_dep),
):
    # Validate the type is registered before persisting.
    try:
        reg.get_connector_class(body.type)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Unknown connector type: {body.type}")

    try:
        cid = cstore.create_connector(
            db,
            org_id=current_user["org_id"],
            type_name=body.type,
            name=body.name,
            credentials=body.credentials,
            config=body.config,
            created_by=current_user.get("id"),
        )
    except Exception as e:
        # Likely the unique (org_id, type, name) collision.
        logger.warning("create_connector failed: %s", e)
        raise HTTPException(status_code=409, detail=f"Could not create connector: {e}")

    row = cstore.get_connector(db, cid, current_user["org_id"])
    return row


@router.delete("/{connector_id}", status_code=204)
def delete_one_connector(
    connector_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin_dep),
):
    deleted = cstore.delete_connector(db, connector_id, current_user["org_id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Connector not found")
    return None


@router.post("/{connector_id}/test")
def test_one_connector(
    connector_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin_dep),
):
    """Call test_connection() without creating a run. Useful from the UI on save."""
    row = cstore.get_connector(db, connector_id, current_user["org_id"], include_credentials=True)
    if row is None:
        raise HTTPException(status_code=404, detail="Connector not found")
    try:
        cls = reg.get_connector_class(row["type"])
    except KeyError:
        raise HTTPException(status_code=500, detail=f"Connector type not registered: {row['type']}")
    try:
        instance = cls(config=row.get("config") or {}, credentials=row.get("credentials") or {})
        ok, msg = instance.test_connection()
    except Exception as e:
        logger.exception("test_connection raised")
        return {"ok": False, "message": f"Internal error during test: {e}"}
    return {"ok": bool(ok), "message": msg or ""}


@router.post("/{connector_id}/run", status_code=202)
def trigger_one_run(
    connector_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin_dep),
):
    """Trigger a manual run. Synchronous in 5.1 — returns the run summary on completion."""
    if cstore.get_connector(db, connector_id, current_user["org_id"]) is None:
        raise HTTPException(status_code=404, detail="Connector not found")
    try:
        result = run_connector(
            db=db,
            connector_id=connector_id,
            org_id=current_user["org_id"],
            triggered_by="api",
            triggered_by_user_id=current_user.get("id"),
        )
    except Exception as e:
        # The runner already wrote a FAILED row before re-raising. Surface 500.
        logger.exception("connector run raised")
        raise HTTPException(status_code=500, detail=f"Run failed: {e}")
    return result
