"""
Evidence state machine with tamper-evident audit logging.
States: DRAFT → REVIEWED → APPROVED → PUBLISHED (terminal, immutable).

Every state transition writes a hash-chained entry to the audit_log table.
"""
import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.evidence.hasher import hash_file


# ── Valid transitions (UPPERCASE to match Postgres enum) ─────────────────
VALID_TRANSITIONS = {
    "DRAFT":     ["REVIEWED"],
    "REVIEWED":  ["APPROVED", "DRAFT"],
    "APPROVED":  ["PUBLISHED", "REVIEWED"],
    "PUBLISHED": [],
}


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


# ── Audit log hash-chaining ─────────────────────────────────────────────

def _compute_entry_hash(
    actor: str,
    actor_type: str,
    action: str,
    target_type: str,
    target_id: str,
    details: dict,
    prev_hash: str,
    timestamp: str,
) -> str:
    """Compute SHA-256 hash for an audit log entry (hash-chain link)."""
    payload = json.dumps(
        {
            "actor": actor,
            "actor_type": actor_type,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "details": details,
            "prev_hash": prev_hash,
            "timestamp": timestamp,
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _get_prev_hash(db: Session) -> str:
    """Get the entry_hash of the most recent audit log entry."""
    row = db.execute(
        text("SELECT entry_hash FROM audit_log ORDER BY id DESC LIMIT 1"),
    ).fetchone()
    return row[0] if row else "GENESIS"


def create_audit_entry(
    db: Session,
    actor: str,
    actor_type: str,
    action: str,
    target_type: str,
    target_id: str,
    details: dict,
) -> None:
    """
    Insert a hash-chained audit log entry.
    Matches audit_log columns: id, timestamp, actor, actor_type, action,
    target_type, target_id, details, prev_hash, entry_hash.
    """
    prev_hash = _get_prev_hash(db)
    now = datetime.now(timezone.utc).isoformat()

    entry_hash = _compute_entry_hash(
        actor=actor,
        actor_type=actor_type,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        prev_hash=prev_hash,
        timestamp=now,
    )

    db.execute(
        text(
            """
            INSERT INTO audit_log
                (timestamp, actor, actor_type, action, target_type, target_id,
                 details, prev_hash, entry_hash)
            VALUES
                (:timestamp, :actor, :actor_type, :action, :target_type, :target_id,
                 CAST(:details AS json), :prev_hash, :entry_hash)
            """
        ),
        {
            "timestamp": now,
            "actor": actor,
            "actor_type": actor_type,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "details": json.dumps(details),
            "prev_hash": prev_hash,
            "entry_hash": entry_hash,
        },
    )


# ── Core state machine ──────────────────────────────────────────────────

def transition_evidence(
    db: Session,
    artifact_id: str,
    new_state: str,
    actor: str,
    comment: str = "",
) -> dict:
    """
    Transition an evidence artifact to a new state.

    - Validates the transition is allowed
    - At PUBLISHED: computes SHA-256 hash, marks artifact immutable
    - Writes timestamp fields (reviewed_at, approved_at, published_at)
    - Creates a hash-chained audit log entry

    Returns dict with artifact info and the new state.
    """
    # Normalize to uppercase to match Postgres enum
    new_state = new_state.upper()

    # 1. Fetch current artifact — FOR UPDATE prevents concurrent transition races
    row = db.execute(
        text(
            "SELECT id, org_id, filename, file_path, state::text, sha256_hash "
            "FROM evidence_artifacts WHERE id = :id FOR UPDATE"
        ),
        {"id": artifact_id},
    ).fetchone()

    if not row:
        raise ValueError(f"Artifact not found: {artifact_id}")

    current_state = row[4]
    org_id = row[1]
    file_path = row[3]

    # 2. Validate transition
    if current_state == "PUBLISHED":
        raise StateTransitionError("Published artifacts are immutable — no further transitions allowed.")

    allowed = VALID_TRANSITIONS.get(current_state, [])
    if new_state not in allowed:
        raise StateTransitionError(
            f"Cannot transition from '{current_state}' to '{new_state}'. "
            f"Allowed: {allowed}"
        )

    # 3. Build the UPDATE dynamically based on target state
    now = datetime.now(timezone.utc)
    update_fields = {"state": new_state, "updated_at": now}
    set_clauses = ["state = :state", "updated_at = :updated_at"]

    if new_state == "REVIEWED":
        update_fields["reviewed_at"] = now
        update_fields["reviewed_by"] = actor
        set_clauses += ["reviewed_at = :reviewed_at", "reviewed_by = :reviewed_by"]

    elif new_state == "APPROVED":
        update_fields["approved_at"] = now
        update_fields["approved_by"] = actor
        set_clauses += ["approved_at = :approved_at", "approved_by = :approved_by"]

    elif new_state == "PUBLISHED":
        sha256 = hash_file(file_path)
        update_fields["sha256_hash"] = sha256
        update_fields["published_at"] = now
        set_clauses += ["sha256_hash = :sha256_hash", "published_at = :published_at"]

    update_fields["id"] = artifact_id
    set_sql = ", ".join(set_clauses)

    db.execute(
        text(f"UPDATE evidence_artifacts SET {set_sql} WHERE id = :id"),
        update_fields,
    )

    # 4. Audit log entry (hash-chained)
    details = {
        "from_state": current_state,
        "to_state": new_state,
        "comment": comment,
        "org_id": org_id,
    }
    if new_state == "PUBLISHED":
        details["sha256_hash"] = update_fields["sha256_hash"]

    create_audit_entry(
        db=db,
        actor=actor,
        actor_type="user",
        action=f"evidence.{new_state}",
        target_type="evidence_artifact",
        target_id=artifact_id,
        details=details,
    )

    db.commit()

    return {
        "artifact_id": artifact_id,
        "filename": row[2],
        "previous_state": current_state,
        "new_state": new_state,
        "actor": actor,
        "timestamp": now.isoformat(),
        "sha256_hash": update_fields.get("sha256_hash"),
    }


# ── Audit chain verification ────────────────────────────────────────────

def verify_audit_chain(db: Session, org_id: str = None) -> dict:
    """
    Verify the integrity of the hash-chained audit log.
    Returns {valid: bool, entries_checked: int, first_broken: int|None}.
    """
    rows = db.execute(
        text(
            "SELECT id, actor, actor_type, action, target_type, target_id, "
            "details, prev_hash, entry_hash, timestamp "
            "FROM audit_log ORDER BY id ASC"
        ),
    ).fetchall()

    if not rows:
        return {"valid": True, "entries_checked": 0, "first_broken": None}

    expected_prev = "GENESIS"
    for row in rows:
        (rid, r_actor, r_actor_type, r_action, r_ttype, r_tid,
         r_details, r_prev, r_hash, r_timestamp) = row

        if r_prev != expected_prev:
            return {"valid": False, "entries_checked": rid, "first_broken": rid}

        computed = _compute_entry_hash(
            actor=r_actor,
            actor_type=r_actor_type,
            action=r_action,
            target_type=r_ttype,
            target_id=r_tid,
            details=r_details if isinstance(r_details, dict) else json.loads(r_details or "{}"),
            prev_hash=r_prev,
            timestamp=r_timestamp.isoformat() if hasattr(r_timestamp, "isoformat") else str(r_timestamp),
        )
        if computed != r_hash:
            return {"valid": False, "entries_checked": rid, "first_broken": rid}

        expected_prev = r_hash

    return {"valid": True, "entries_checked": len(rows), "first_broken": None}