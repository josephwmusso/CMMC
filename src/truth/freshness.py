"""
src/truth/freshness.py

Evidence freshness tracking (Phase 4.4). Pure date-math — no LLM calls.

Evidence has a shelf life that depends on its type: scan reports go stale
in ~90 days, policy documents in ~365. When all observations that SUPPORT
a VERIFIED claim become STALE, the claim itself should flip to STALE.
Freshness is computed on read for evidence/observations; the only stored
side-effect is ``claims.verification_status = 'STALE'``, updated by
``refresh_claim_staleness()``.

Thresholds may be overridden per-org via the ``freshness_thresholds``
table; when absent the module-level ``DEFAULT_FRESHNESS_THRESHOLDS``
dict is used.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ── Default thresholds ────────────────────────────────────────────────────
# (fresh_days, aging_days_start, stale_days_start)
# FRESH:  age <= fresh_days
# AGING:  fresh_days < age <= stale_days
# STALE:  age > stale_days

DEFAULT_FRESHNESS_THRESHOLDS: dict[str, tuple[int, int, int]] = {
    "SCAN_REPORT":       (30,  90,   90),
    "POLICY_DOCUMENT":   (180, 365, 365),
    "SCREENSHOT":        (60,  180, 180),
    "CONFIG_EXPORT":     (60,  180, 180),
    "TRAINING_RECORD":   (180, 365, 365),
    "AUDIT_LOG":         (30,  90,   90),
    "INCIDENT_REPORT":   (365, 730, 730),
    "DEFAULT":           (90,  180, 180),
}

OBSERVATION_TYPE_MAP: dict[str, Optional[str]] = {
    "SCAN_FINDING":       "SCAN_REPORT",
    "BASELINE_DEVIATION": "SCAN_REPORT",
    "EVIDENCE_ARTIFACT":  None,   # look up actual evidence_type
    "INTAKE_RESPONSE":    "DEFAULT",
    "CONTRADICTION":      "DEFAULT",
}

_MATCH_CONFIDENCE = 0.6


def _gen_id(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()[:20]


def _audit(db: Session, *, actor: str, action: str, target_id: str, details: dict) -> None:
    try:
        from src.evidence.state_machine import create_audit_entry
        create_audit_entry(
            db=db, actor=actor, actor_type="user", action=action,
            target_type="organization", target_id=target_id, details=details,
        )
    except Exception:
        logger.exception("audit %s failed", action)


def _safe_user_fk(db: Session, user_id: Optional[str]) -> Optional[str]:
    if not user_id:
        return None
    row = db.execute(text("SELECT 1 FROM users WHERE id = :id"), {"id": user_id}).fetchone()
    return user_id if row else None


# ── Threshold lookup (per-org override > module constant) ─────────────────

def _get_thresholds(db: Session, org_id: Optional[str], evidence_type: str) -> tuple[int, int, int]:
    """Return (fresh_days, aging_start, stale_start) for the evidence_type.
    Checks freshness_thresholds table for per-org overrides first."""
    if org_id:
        try:
            row = db.execute(text("""
                SELECT fresh_days, aging_days, stale_days
                FROM freshness_thresholds
                WHERE org_id = :o AND evidence_type = :et
            """), {"o": org_id, "et": evidence_type.upper()}).fetchone()
            if row:
                return (row.fresh_days, row.aging_days, row.stale_days)
        except Exception:
            pass  # table may not exist on older DBs
    et = evidence_type.upper()
    return DEFAULT_FRESHNESS_THRESHOLDS.get(et, DEFAULT_FRESHNESS_THRESHOLDS["DEFAULT"])


# ── Core freshness calculator ─────────────────────────────────────────────

def get_freshness_status(age_days: Optional[int], evidence_type: str,
                         db: Optional[Session] = None, org_id: Optional[str] = None) -> str:
    """Return 'FRESH', 'AGING', 'STALE', or 'UNKNOWN'."""
    if age_days is None:
        return "UNKNOWN"
    fresh, _aging, stale = _get_thresholds(db, org_id, evidence_type) if db else (
        DEFAULT_FRESHNESS_THRESHOLDS.get(evidence_type.upper(),
                                          DEFAULT_FRESHNESS_THRESHOLDS["DEFAULT"])
    )
    if age_days <= fresh:
        return "FRESH"
    if age_days <= stale:
        return "AGING"
    return "STALE"


def _age_days(observed_at: Optional[datetime]) -> Optional[int]:
    if observed_at is None:
        return None
    now = datetime.now(timezone.utc)
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=timezone.utc)
    return max(0, (now - observed_at).days)


# ── Per-artifact freshness ────────────────────────────────────────────────

def calculate_evidence_freshness(evidence_id: str, db: Session, org_id: Optional[str] = None) -> dict:
    row = db.execute(text("""
        SELECT id, org_id, evidence_type, created_at, updated_at
        FROM evidence_artifacts WHERE id = :id
    """), {"id": evidence_id}).fetchone()
    if not row:
        return {"error": "Evidence artifact not found"}
    observed_at = row.updated_at or row.created_at
    age = _age_days(observed_at)
    etype = (row.evidence_type or "DEFAULT").upper()
    fresh, _aging, stale = _get_thresholds(db, org_id or row.org_id, etype)
    return {
        "evidence_id":    row.id,
        "evidence_type":  etype,
        "age_days":       age,
        "freshness":      get_freshness_status(age, etype, db, org_id or row.org_id),
        "threshold_days": stale,
        "observed_at":    observed_at.isoformat() if observed_at else None,
    }


# ── Per-observation freshness ─────────────────────────────────────────────

def calculate_observation_freshness(observation_id: str, db: Session, org_id: Optional[str] = None) -> dict:
    row = db.execute(text("""
        SELECT id, org_id, source_type, source_id, observed_at
        FROM observations WHERE id = :id
    """), {"id": observation_id}).fetchone()
    if not row:
        return {"error": "Observation not found"}

    etype = _resolve_evidence_type(row.source_type, row.source_id, db)
    age = _age_days(row.observed_at)
    oid = org_id or row.org_id
    fresh, _aging, stale = _get_thresholds(db, oid, etype)
    return {
        "observation_id": row.id,
        "source_type":    row.source_type,
        "evidence_type":  etype,
        "age_days":       age,
        "freshness":      get_freshness_status(age, etype, db, oid),
        "threshold_days": stale,
        "observed_at":    row.observed_at.isoformat() if row.observed_at else None,
    }


def _resolve_evidence_type(source_type: str, source_id: Optional[str], db: Session) -> str:
    """Map observation source_type to an evidence_type for threshold lookup."""
    mapped = OBSERVATION_TYPE_MAP.get(source_type)
    if mapped is not None:
        return mapped

    # EVIDENCE_ARTIFACT → look up actual type
    if source_type == "EVIDENCE_ARTIFACT" and source_id:
        row = db.execute(text(
            "SELECT evidence_type FROM evidence_artifacts WHERE id = :id"
        ), {"id": source_id}).fetchone()
        if row and row.evidence_type:
            return row.evidence_type.upper()
    return "DEFAULT"


# ── Observation freshness for a list (used by resolver + refresh) ─────────

def observation_freshness_status(observation_id: str, db: Session, org_id: Optional[str] = None) -> str:
    """Return just the freshness string for one observation."""
    info = calculate_observation_freshness(observation_id, db, org_id)
    return info.get("freshness", "UNKNOWN")


def all_supporting_observations_stale(
    per_claim_verdicts: list[dict], db: Session, org_id: Optional[str] = None,
) -> bool:
    """Given a list of verdicts (each having 'relationship', 'confidence',
    'observation_id'), return True iff every SUPPORTS verdict with
    confidence >= threshold has a STALE observation.

    Returns False if there are no qualifying supports at all (can't be
    stale if there's nothing to go stale).
    """
    supporting_obs = [
        v["observation_id"]
        for v in per_claim_verdicts
        if v.get("relationship") == "SUPPORTS"
        and v.get("confidence", 0) >= _MATCH_CONFIDENCE
        and v.get("observation_id")
    ]
    if not supporting_obs:
        return False
    for obs_id in supporting_obs:
        fs = observation_freshness_status(obs_id, db, org_id)
        if fs != "STALE":
            return False
    return True


# ── Batch refresh: VERIFIED ↔ STALE ──────────────────────────────────────

def refresh_claim_staleness(org_id: str, db: Session, user_id: Optional[str] = None) -> dict:
    """Walk every VERIFIED and STALE claim. Downgrade VERIFIED→STALE when
    all supporting observations are stale; promote STALE→VERIFIED when at
    least one supporting observation is no longer stale.

    Does NOT touch CONFLICT or UNVERIFIED claims."""
    now = datetime.now(timezone.utc)
    safe_user = _safe_user_fk(db, user_id)

    claims = db.execute(text("""
        SELECT id, verification_status
        FROM claims
        WHERE org_id = :o
          AND verification_status IN ('VERIFIED', 'STALE')
    """), {"o": org_id}).fetchall()

    downgraded  = 0
    promoted    = 0
    no_change   = 0

    for cl in claims:
        # Fetch supporting resolutions for this claim
        supports = db.execute(text("""
            SELECT r.observation_id
            FROM resolutions r
            WHERE r.claim_id = :cid
              AND r.relationship = 'SUPPORTS'
              AND r.confidence >= :thresh
        """), {"cid": cl.id, "thresh": _MATCH_CONFIDENCE}).fetchall()

        if not supports:
            no_change += 1
            continue

        all_stale = True
        for s in supports:
            fs = observation_freshness_status(s.observation_id, db, org_id)
            if fs != "STALE":
                all_stale = False
                break

        if cl.verification_status == "VERIFIED" and all_stale:
            db.execute(text("""
                UPDATE claims
                SET verification_status = 'STALE',
                    verified_at         = :now,
                    verified_by         = :by
                WHERE id = :id AND org_id = :o
            """), {"id": cl.id, "o": org_id, "now": now, "by": safe_user})
            downgraded += 1
        elif cl.verification_status == "STALE" and not all_stale:
            db.execute(text("""
                UPDATE claims
                SET verification_status = 'VERIFIED',
                    verified_at         = :now,
                    verified_by         = :by
                WHERE id = :id AND org_id = :o
            """), {"id": cl.id, "o": org_id, "now": now, "by": safe_user})
            promoted += 1
        else:
            no_change += 1

    db.commit()

    _audit(
        db,
        actor=safe_user or "system",
        action="FRESHNESS_REFRESH",
        target_id=org_id,
        details={
            "claims_checked":     len(claims),
            "downgraded_to_stale": downgraded,
            "promoted_from_stale": promoted,
            "no_change":          no_change,
        },
    )
    db.commit()

    return {
        "claims_checked":      len(claims),
        "downgraded_to_stale": downgraded,
        "promoted_from_stale": promoted,
        "no_change":           no_change,
    }


# ── Summary + stale-item listing ──────────────────────────────────────────

def get_freshness_summary(org_id: str, db: Session) -> dict:
    """Aggregate freshness across evidence and observations."""
    # Evidence
    ev_rows = db.execute(text("""
        SELECT id, evidence_type, created_at, updated_at
        FROM evidence_artifacts WHERE org_id = :o
    """), {"o": org_id}).fetchall()

    ev_total = len(ev_rows)
    ev_fresh = ev_aging = ev_stale = 0
    ev_by_type: dict[str, dict[str, int]] = {}

    for r in ev_rows:
        observed_at = r.updated_at or r.created_at
        age = _age_days(observed_at)
        etype = (r.evidence_type or "DEFAULT").upper()
        fs = get_freshness_status(age, etype, db, org_id)
        if fs == "FRESH":   ev_fresh += 1
        elif fs == "AGING": ev_aging += 1
        elif fs == "STALE": ev_stale += 1
        bucket = ev_by_type.setdefault(etype, {"fresh": 0, "aging": 0, "stale": 0})
        if fs in ("FRESH", "AGING", "STALE"):
            bucket[fs.lower()] += 1

    # Observations
    obs_rows = db.execute(text("""
        SELECT id, source_type, source_id, observed_at
        FROM observations WHERE org_id = :o
    """), {"o": org_id}).fetchall()

    obs_total = len(obs_rows)
    obs_fresh = obs_aging = obs_stale = 0

    for r in obs_rows:
        etype = _resolve_evidence_type(r.source_type, r.source_id, db)
        age = _age_days(r.observed_at)
        fs = get_freshness_status(age, etype, db, org_id)
        if fs == "FRESH":   obs_fresh += 1
        elif fs == "AGING": obs_aging += 1
        elif fs == "STALE": obs_stale += 1

    stale_claims = db.execute(text("""
        SELECT COUNT(*) FROM claims
        WHERE org_id = :o AND verification_status = 'STALE'
    """), {"o": org_id}).scalar() or 0

    return {
        "evidence": {
            "total":   ev_total,
            "fresh":   ev_fresh,
            "aging":   ev_aging,
            "stale":   ev_stale,
            "by_type": ev_by_type,
        },
        "observations": {
            "total": obs_total,
            "fresh": obs_fresh,
            "aging": obs_aging,
            "stale": obs_stale,
        },
        "claims_affected":       int(stale_claims),
        "items_needing_refresh": ev_stale,
    }


def list_stale_items(org_id: str, db: Session) -> list[dict]:
    """Flat list of stale evidence + observations, sorted by age DESC."""
    items: list[dict] = []

    # Stale evidence
    ev_rows = db.execute(text("""
        SELECT ea.id, ea.evidence_type, ea.filename, ea.created_at, ea.updated_at,
               ARRAY(
                   SELECT DISTINCT ecm.control_id
                   FROM evidence_control_map ecm
                   WHERE ecm.evidence_id = ea.id
               ) AS ctrl_ids
        FROM evidence_artifacts ea
        WHERE ea.org_id = :o
    """), {"o": org_id}).fetchall()

    for r in ev_rows:
        observed_at = r.updated_at or r.created_at
        age = _age_days(observed_at)
        etype = (r.evidence_type or "DEFAULT").upper()
        fs = get_freshness_status(age, etype, db, org_id)
        if fs == "STALE":
            items.append({
                "id":                r.id,
                "type":              "evidence",
                "evidence_type":     etype,
                "filename":          r.filename,
                "age_days":          age,
                "freshness":         "STALE",
                "controls_affected": list(r.ctrl_ids) if r.ctrl_ids else [],
            })

    # Stale observations
    obs_rows = db.execute(text("""
        SELECT id, source_type, source_id, observation_text, observed_at
        FROM observations WHERE org_id = :o
    """), {"o": org_id}).fetchall()

    for r in obs_rows:
        etype = _resolve_evidence_type(r.source_type, r.source_id, db)
        age = _age_days(r.observed_at)
        fs = get_freshness_status(age, etype, db, org_id)
        if fs == "STALE":
            items.append({
                "id":               r.id,
                "type":             "observation",
                "source_type":      r.source_type,
                "observation_text": (r.observation_text or "")[:300],
                "age_days":         age,
                "freshness":        "STALE",
            })

    items.sort(key=lambda x: (x.get("age_days") or 0), reverse=True)
    return items
