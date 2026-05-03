"""Connector orchestrator.

run_connector() is the single entry point. It loads the connector
record, decrypts credentials, instantiates the connector class from
the registry, calls test_connection() then iterates pull(), turning
each PulledEvidence into a DRAFT evidence_artifact linked to the
declared controls. All actions write to audit_log via the existing
upload_evidence / link_evidence_to_controls path.

NOTE on dedup: this is the connector's responsibility. Two runs of
the same connector against the same upstream state will produce
duplicate evidence_artifacts unless pull() filters by content hash.
hash_dict() in src.evidence.hasher is available for this purpose.
"""

from __future__ import annotations

import logging
import time

from sqlalchemy.orm import Session

from src.connectors import registry as reg
from src.connectors import storage as cstore
from src.evidence.storage import upload_evidence, link_evidence_to_controls

logger = logging.getLogger(__name__)


def run_connector(
    db: Session,
    connector_id: str,
    org_id: str,
    triggered_by: str = "manual",
    triggered_by_user_id: str | None = None,
) -> dict:
    """Execute one pull cycle. Returns a summary dict.

    triggered_by: "manual" | "schedule" | "api" — free-form provenance tag.
    Returns: the same dict shape as cstore.get_connector_run for the run row.
    """
    # 1. Load connector + decrypt credentials.
    connector_row = cstore.get_connector(db, connector_id, org_id, include_credentials=True)
    if connector_row is None:
        raise KeyError(f"Connector {connector_id} not found in org {org_id}")

    type_name = connector_row["type"]
    config = connector_row.get("config") or {}
    credentials = connector_row.get("credentials") or {}

    # 2. Open a run row in RUNNING state.
    run_id = cstore.create_connector_run(
        db, connector_id, org_id,
        triggered_by=triggered_by,
        triggered_by_user_id=triggered_by_user_id,
    )

    actor = f"connector:{type_name}:{connector_id}"
    started = time.time()
    evidence_ids: list[str] = []
    errors: list[str] = []

    try:
        # 3. Resolve and instantiate.
        try:
            cls = reg.get_connector_class(type_name)
        except KeyError as e:
            cstore.update_connector_run(
                db, run_id,
                status="FAILED",
                error_message=str(e),
                summary={"errors": [str(e)], "evidence_ids": [], "duration_seconds": 0.0},
                finished=True,
            )
            cstore.update_connector_status(db, connector_id, org_id,
                                           status="ERROR", last_status="FAILED")
            raise

        connector = cls(config=config, credentials=credentials)

        # 4. Probe.
        ok, msg = connector.test_connection()
        if not ok:
            cstore.update_connector_run(
                db, run_id,
                status="FAILED",
                error_message=f"test_connection failed: {msg}",
                summary={"errors": [msg], "evidence_ids": [], "duration_seconds": time.time() - started},
                finished=True,
            )
            cstore.update_connector_status(db, connector_id, org_id,
                                           status="ERROR", last_status="FAILED")
            return cstore.get_connector_run(db, run_id, org_id) or {}

        # 5. Pull and ingest.
        for item in connector.pull():
            try:
                result = upload_evidence(
                    db=db,
                    org_id=org_id,
                    filename=item.filename,
                    file_bytes=item.content,
                    uploaded_by=actor,
                    description=item.description,
                    source_system=f"connector:{type_name}",
                    actor_type="connector",
                )
                artifact_id = result["artifact_id"]
                evidence_ids.append(artifact_id)
                if item.control_ids:
                    link_evidence_to_controls(
                        db=db,
                        artifact_id=artifact_id,
                        control_ids=item.control_ids,
                        mapped_by="connector",
                    )
            except Exception as e:
                logger.warning("connector item ingestion failed: %s", e, exc_info=True)
                errors.append(f"{item.filename}: {e}")

        # 6. Final status.
        from datetime import datetime, timezone
        duration = time.time() - started
        if errors and not evidence_ids:
            final = "FAILED"
        elif errors:
            final = "PARTIAL"
        else:
            final = "SUCCESS"

        cstore.update_connector_run(
            db, run_id,
            status=final,
            evidence_artifacts_created=len(evidence_ids),
            error_message="; ".join(errors) if errors else None,
            summary={
                "evidence_ids": evidence_ids,
                "errors": errors,
                "duration_seconds": round(duration, 3),
            },
            finished=True,
        )
        cstore.update_connector_status(
            db, connector_id, org_id,
            status="ACTIVE" if final == "SUCCESS" else "ERROR",
            last_status=final,
            last_run_at=datetime.now(timezone.utc),
        )

    except Exception as e:
        logger.exception("connector run failed catastrophically")
        cstore.update_connector_run(
            db, run_id,
            status="FAILED",
            error_message=str(e),
            summary={
                "evidence_ids": evidence_ids,
                "errors": errors + [f"fatal: {e}"],
                "duration_seconds": round(time.time() - started, 3),
            },
            finished=True,
        )
        cstore.update_connector_status(db, connector_id, org_id,
                                       status="ERROR", last_status="FAILED")
        raise

    return cstore.get_connector_run(db, run_id, org_id) or {}
