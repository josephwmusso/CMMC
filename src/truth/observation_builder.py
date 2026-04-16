"""
src/truth/observation_builder.py

Deterministic builders that produce Observation rows from structured
evidence sources. No LLM involvement — every observation_text is a
template fill over real column values so rebuilds are reproducible.

Sources:
  - SCAN_FINDING       ← scan_findings (+ scan_imports for date)
  - BASELINE_DEVIATION ← baseline_deviations (+ baseline_items)
  - INTAKE_RESPONSE    ← intake_responses (answer_value / answer_details)
  - EVIDENCE_ARTIFACT  ← evidence_artifacts (+ evidence_control_map)
  - CONTRADICTION      ← intake_contradictions

Each builder returns a list of observation dicts — the orchestrator
``build_all_observations`` handles the DELETE-then-INSERT transaction.
IDs are ``_gen_id(f"obs:{source_type}:{source_id}")`` so re-running
against the same source data yields the same rows.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


SOURCE_TYPES = (
    "SCAN_FINDING",
    "BASELINE_DEVIATION",
    "INTAKE_RESPONSE",
    "EVIDENCE_ARTIFACT",
    "CONTRADICTION",
)


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


def _as_list(val: Any) -> list:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(v) for v in val if v]
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return [str(v) for v in parsed if v] if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []


# ── 1. scan_findings ───────────────────────────────────────────────────────

def build_scan_observations(org_id: str, db: Session) -> list[dict]:
    """One observation per OPEN scan_finding. Controls pulled from the
    finding's own mapped_control_ids (what the Nessus parser decided)."""
    rows = db.execute(text("""
        SELECT sf.id, sf.host_ip, sf.port, sf.plugin_id, sf.plugin_name,
               sf.severity_label, sf.synopsis, sf.mapped_control_ids,
               si.scan_date
        FROM scan_findings sf
        LEFT JOIN scan_imports si ON si.id = sf.scan_import_id
        WHERE sf.org_id = :o AND sf.status = 'OPEN'
    """), {"o": org_id}).fetchall()

    out: list[dict] = []
    for r in rows:
        synopsis = (r.synopsis or r.plugin_name or "").strip()
        host = r.host_ip or "?"
        port = r.port if r.port else 0
        obs_text = (
            f"Nessus scan identified {r.severity_label} finding: "
            f"{synopsis[:200]} on host {host}:{port} (plugin {r.plugin_id})"
        )[:2000]
        out.append({
            "id":               _gen_id(f"obs:SCAN_FINDING:{r.id}"),
            "observation_text": obs_text,
            "source_type":      "SCAN_FINDING",
            "source_id":        r.id,
            "control_ids":      _as_list(r.mapped_control_ids) or None,
            "observation_type": "TECHNICAL",
            "confidence":       1.0,
            "observed_at":      r.scan_date,
        })
    return out


# ── 2. baseline_deviations ────────────────────────────────────────────────

def build_deviation_observations(org_id: str, db: Session) -> list[dict]:
    """One observation per OPEN baseline_deviation."""
    rows = db.execute(text("""
        SELECT bd.id, bd.actual_value, bd.detected_at,
               bi.title, bi.expected_value, bi.cis_id, bi.severity,
               bi.control_ids
        FROM baseline_deviations bd
        JOIN baseline_items bi ON bd.baseline_item_id = bi.id
        WHERE bd.org_id = :o AND bd.status = 'OPEN'
    """), {"o": org_id}).fetchall()

    out: list[dict] = []
    for r in rows:
        title = (r.title or "").strip()
        actual = (r.actual_value or "unknown").strip()
        expected = (r.expected_value or "unknown").strip()
        obs_text = (
            f"Baseline deviation: {title[:200]} — actual: {actual[:200]}, "
            f"expected: {expected[:200]} (CIS {r.cis_id or '?'}, {r.severity or 'MEDIUM'})"
        )[:2000]
        out.append({
            "id":               _gen_id(f"obs:BASELINE_DEVIATION:{r.id}"),
            "observation_text": obs_text,
            "source_type":      "BASELINE_DEVIATION",
            "source_id":        r.id,
            "control_ids":      list(r.control_ids) if r.control_ids else None,
            "observation_type": "TECHNICAL",
            "confidence":       1.0,
            "observed_at":      r.detected_at,
        })
    return out


# ── 3. intake_responses ───────────────────────────────────────────────────

def _intake_observation_type(question_id: str, module_id: Optional[int]) -> str:
    """Best-effort classification by Module family (from intake_modules):
       - Module 0 tech-stack + Modules 3/7 (CM/IA/SC) → TECHNICAL
       - Modules 2/4/5/6/8 (AT/AU/IR/MA/MP/PE/PS/RA/CA/SI) → OPERATIONAL
       - Module 1 (AC) straddles — default OPERATIONAL
    """
    if question_id:
        qid = question_id.lower()
        # m0_* tool-stack questions stay TECHNICAL.
        if qid.startswith("m0_") and any(tok in qid for tok in (
            "identity_provider", "email_platform", "edr", "firewall",
            "siem", "training_tool", "remote_workers", "wireless",
        )):
            return "TECHNICAL"
        if qid.startswith("m0_") and any(tok in qid for tok in (
            "existing_docs", "ssp", "poam", "prior_assessment", "dfars", "cui_",
        )):
            return "POLICY"
    TECHNICAL_MODULES = {3, 7}
    POLICY_MODULES    = {6}  # RA/CA — policy-heavy
    if module_id in TECHNICAL_MODULES:
        return "TECHNICAL"
    if module_id in POLICY_MODULES:
        return "POLICY"
    return "OPERATIONAL"


def build_intake_observations(org_id: str, db: Session) -> list[dict]:
    """One observation per intake response with a non-empty answer_value."""
    rows = db.execute(text("""
        SELECT id, module_id, question_id, control_ids, answer_value,
               answer_details, answered_at
        FROM intake_responses
        WHERE org_id = :o
          AND answer_value IS NOT NULL
          AND answer_value <> ''
    """), {"o": org_id}).fetchall()

    out: list[dict] = []
    for r in rows:
        qid     = (r.question_id or "").strip()
        answer  = (r.answer_value or "").strip()
        details = r.answer_details
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except json.JSONDecodeError:
                details = {}
        if not isinstance(details, dict):
            details = {}

        # Prefer the free-text classification's SSP-ready narrative when
        # we have one — that's richer and already deduplicated.
        narrative = None
        if details.get("source") == "free_text":
            narrative = (details.get("classification") or {}).get("ssp_narrative_context")
        if narrative:
            obs_text = f"Organization self-reports ({qid}): {narrative}"
        else:
            obs_text = f"Organization self-reports ({qid}): {answer}"
        obs_text = obs_text[:2000]

        obs_type = _intake_observation_type(qid, r.module_id)

        out.append({
            "id":               _gen_id(f"obs:INTAKE_RESPONSE:{r.id}"),
            "observation_text": obs_text,
            "source_type":      "INTAKE_RESPONSE",
            "source_id":        r.id,
            "control_ids":      _as_list(r.control_ids) or None,
            "observation_type": obs_type,
            "confidence":       0.7,
            "observed_at":      r.answered_at,
        })
    return out


# ── 4. evidence_artifacts ─────────────────────────────────────────────────

_STATE_CONFIDENCE = {
    "PUBLISHED": 1.0,
    "APPROVED":  0.9,
    "REVIEWED":  0.7,
    "DRAFT":     0.5,
}


def _evidence_observation_type(evidence_type: Optional[str]) -> str:
    et = (evidence_type or "").upper()
    if "POLICY" in et or "PROCEDURE" in et:
        return "POLICY"
    if "TRAINING" in et or "INCIDENT" in et or "AUDIT_LOG" in et or "REVIEW" in et:
        return "OPERATIONAL"
    return "TECHNICAL"


def build_evidence_observations(org_id: str, db: Session) -> list[dict]:
    """One observation per evidence_artifact. Controls pulled from
    evidence_control_map; confidence ladder driven by state."""
    rows = db.execute(text("""
        SELECT ea.id, ea.filename, ea.state, ea.evidence_type,
               ea.source_system, ea.created_at, ea.updated_at,
               ARRAY(
                   SELECT DISTINCT ecm.control_id
                   FROM evidence_control_map ecm
                   WHERE ecm.evidence_id = ea.id
               ) AS ctrl_ids
        FROM evidence_artifacts ea
        WHERE ea.org_id = :o
    """), {"o": org_id}).fetchall()

    out: list[dict] = []
    for r in rows:
        state      = (r.state or "DRAFT").upper()
        etype      = (r.evidence_type or "").strip() or "UNKNOWN"
        source_sys = (r.source_system or "").strip() or "manual"
        filename   = (r.filename or "").strip() or "(unnamed)"
        obs_text = (
            f"Evidence artifact '{filename[:200]}' exists in {state} state "
            f"(type: {etype}, source: {source_sys})"
        )[:2000]
        observed_at = r.updated_at or r.created_at
        out.append({
            "id":               _gen_id(f"obs:EVIDENCE_ARTIFACT:{r.id}"),
            "observation_text": obs_text,
            "source_type":      "EVIDENCE_ARTIFACT",
            "source_id":        r.id,
            "control_ids":      list(r.ctrl_ids) if r.ctrl_ids else None,
            "observation_type": _evidence_observation_type(etype),
            "confidence":       _STATE_CONFIDENCE.get(state, 0.5),
            "observed_at":      observed_at,
        })
    return out


# ── 5. intake_contradictions ──────────────────────────────────────────────

def build_contradiction_observations(org_id: str, db: Session) -> list[dict]:
    """One observation per OPEN intake_contradiction."""
    rows = db.execute(text("""
        SELECT id, family, severity, description, affected_control_ids, detected_at
        FROM intake_contradictions
        WHERE org_id = :o AND status = 'OPEN'
    """), {"o": org_id}).fetchall()

    out: list[dict] = []
    for r in rows:
        sev  = (r.severity or "MEDIUM").upper()
        desc = (r.description or "").strip()
        obs_text = f"OPEN contradiction ({sev}): {desc[:300]}"[:2000]
        out.append({
            "id":               _gen_id(f"obs:CONTRADICTION:{r.id}"),
            "observation_text": obs_text,
            "source_type":      "CONTRADICTION",
            "source_id":        r.id,
            "control_ids":      _as_list(r.affected_control_ids) or None,
            "observation_type": "TECHNICAL",
            "confidence":       0.9,
            "observed_at":      r.detected_at,
        })
    return out


# ── Orchestrator ──────────────────────────────────────────────────────────

_BUILDERS = {
    "SCAN_FINDING":       build_scan_observations,
    "BASELINE_DEVIATION": build_deviation_observations,
    "INTAKE_RESPONSE":    build_intake_observations,
    "EVIDENCE_ARTIFACT":  build_evidence_observations,
    "CONTRADICTION":      build_contradiction_observations,
}


def _insert_observations(db: Session, org_id: str, observations: list[dict]) -> int:
    """Batch-insert observations. Uses ON CONFLICT to be re-run safe
    within a single transaction where IDs might collide."""
    inserted = 0
    for obs in observations:
        db.execute(text("""
            INSERT INTO observations
                (id, org_id, observation_text, source_type, source_id,
                 control_ids, observation_type, confidence, observed_at, notes)
            VALUES
                (:id, :org_id, :text, :stype, :sid,
                 :cids, :otype, :conf, :observed, NULL)
            ON CONFLICT (id) DO UPDATE SET
                observation_text = EXCLUDED.observation_text,
                control_ids      = EXCLUDED.control_ids,
                observation_type = EXCLUDED.observation_type,
                confidence       = EXCLUDED.confidence,
                observed_at      = EXCLUDED.observed_at
        """), {
            "id":       obs["id"],
            "org_id":   org_id,
            "text":     obs["observation_text"],
            "stype":    obs["source_type"],
            "sid":      obs.get("source_id"),
            "cids":     obs.get("control_ids"),
            "otype":    obs.get("observation_type", "TECHNICAL"),
            "conf":     obs.get("confidence", 1.0),
            "observed": obs.get("observed_at"),
        })
        inserted += 1
    return inserted


def build_observations_for_source(
    org_id: str, source_type: str, db: Session, user_id: Optional[str] = None,
) -> dict:
    """Rebuild observations for one source type only."""
    st = source_type.upper()
    builder = _BUILDERS.get(st)
    if builder is None:
        raise ValueError(f"Unknown source_type {source_type}; must be one of {sorted(_BUILDERS)}")

    db.execute(text("""
        DELETE FROM observations
        WHERE org_id = :o AND source_type = :st
    """), {"o": org_id, "st": st})

    built = builder(org_id, db)
    inserted = _insert_observations(db, org_id, built)
    db.commit()

    _audit(
        db,
        actor=_safe_user_fk(db, user_id) or "system",
        action="OBSERVATIONS_BUILT",
        target_id=org_id,
        details={"source_type": st, "count": inserted, "scope": "single_source"},
    )
    db.commit()

    return {"source_type": st, "count": inserted}


def build_all_observations(
    org_id: str, db: Session, user_id: Optional[str] = None,
) -> dict:
    """Full rebuild — wipes all observations for the org, then runs
    every builder. Idempotent: deterministic IDs mean reruns produce
    the same row set for the same source data.
    """
    db.execute(text("DELETE FROM observations WHERE org_id = :o"), {"o": org_id})

    by_source: dict[str, int] = {}
    by_type:   dict[str, int] = {}
    total = 0

    for st, builder in _BUILDERS.items():
        try:
            built = builder(org_id, db)
        except Exception:
            logger.exception("builder %s failed", st)
            built = []
        inserted = _insert_observations(db, org_id, built)
        by_source[st] = inserted
        for obs in built:
            ot = obs.get("observation_type", "TECHNICAL")
            by_type[ot] = by_type.get(ot, 0) + 1
        total += inserted

    db.commit()

    _audit(
        db,
        actor=_safe_user_fk(db, user_id) or "system",
        action="OBSERVATIONS_BUILT",
        target_id=org_id,
        details={"scope": "all", "total": total, "by_source_type": by_source},
    )
    db.commit()

    return {
        "total":               total,
        "by_source_type":      by_source,
        "by_observation_type": by_type,
    }
