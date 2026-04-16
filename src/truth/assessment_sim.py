"""
src/truth/assessment_sim.py

Assessment simulation (Phase 4.5). Combines the truth model
(claims / observations / resolutions / freshness) with the existing
SPRS scoring engine to produce a mock C3PAO assessment scorecard.

LLM is used ONLY for `generate_assessor_finding()` (one call per
at-risk control, capped at top_n=10). All scoring and method-coverage
logic is deterministic.
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


# ── Constants ─────────────────────────────────────────────────────────────

METHOD_MAP: dict[str, Optional[str]] = {
    "SCAN_FINDING":       "TEST",
    "BASELINE_DEVIATION": "TEST",
    "INTAKE_RESPONSE":    "INTERVIEW",
    "CONTRADICTION":      None,
}

CONFLICT_PENALTY_MULTIPLIER  = 1.0
STALE_PENALTY_MULTIPLIER     = 0.3

SPRS_FLOOR = -203


# ── Helpers ───────────────────────────────────────────────────────────────

def _gen_id(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()[:20]


def _audit(db: Session, *, actor: str, action: str, target_id: str, details: dict) -> None:
    try:
        from src.evidence.state_machine import create_audit_entry
        create_audit_entry(
            db=db, actor=actor, actor_type="user", action=action,
            target_type="assessment_snapshot", target_id=target_id, details=details,
        )
    except Exception:
        logger.exception("audit %s failed", action)


def _safe_user_fk(db: Session, uid: Optional[str]) -> Optional[str]:
    if not uid:
        return None
    r = db.execute(text("SELECT 1 FROM users WHERE id = :id"), {"id": uid}).fetchone()
    return uid if r else None


def _evidence_method(source_type: str, observation_type: str, source_id: Optional[str], db: Session) -> Optional[str]:
    """For EVIDENCE_ARTIFACT observations, resolve the method from the
    artifact's evidence_type. Others use METHOD_MAP directly."""
    if source_type != "EVIDENCE_ARTIFACT":
        return METHOD_MAP.get(source_type)
    ot = observation_type.upper()
    if ot == "POLICY":
        return "EXAMINE"
    if ot == "OPERATIONAL":
        return "INTERVIEW"
    return "TEST"


# ── Method coverage ───────────────────────────────────────────────────────

def compute_method_coverage(control_id: str, org_id: str, db: Session) -> dict:
    rows = db.execute(text("""
        SELECT id, source_type, observation_type, source_id
        FROM observations
        WHERE org_id = :o AND :c = ANY(control_ids)
    """), {"o": org_id, "c": control_id}).fetchall()

    methods: set[str] = set()
    for r in rows:
        m = _evidence_method(r.source_type, r.observation_type or "TECHNICAL", r.source_id, db)
        if m:
            methods.add(m)

    count = len(methods)
    return {
        "control_id":   control_id,
        "examine":      "EXAMINE"   in methods,
        "interview":    "INTERVIEW" in methods,
        "test":         "TEST"      in methods,
        "method_count": count,
        "coverage_pct": round(count / 3.0 * 100, 1),
    }


# ── Per-control claim counts ─────────────────────────────────────────────

def _claim_counts(control_id: str, org_id: str, db: Session) -> dict:
    rows = db.execute(text("""
        SELECT verification_status, COUNT(*) AS cnt
        FROM claims
        WHERE org_id = :o AND control_id = :c
        GROUP BY verification_status
    """), {"o": org_id, "c": control_id}).fetchall()
    d: dict[str, int] = {}
    for r in rows:
        d[r.verification_status] = int(r.cnt)
    return {
        "total":      sum(d.values()),
        "verified":   d.get("VERIFIED",   0),
        "conflict":   d.get("CONFLICT",   0),
        "unverified": d.get("UNVERIFIED", 0),
        "stale":      d.get("STALE",      0),
    }


# ── Per-control risk score ────────────────────────────────────────────────

def compute_control_risk_score(control_id: str, org_id: str, db: Session) -> dict:
    cc = _claim_counts(control_id, org_id, db)
    mc = compute_method_coverage(control_id, org_id, db)

    weight_row = db.execute(
        text("SELECT points, title FROM controls WHERE id = :id"),
        {"id": control_id},
    ).fetchone()
    weight = int(weight_row.points) if weight_row else 1
    title = weight_row.title if weight_row else control_id

    # SSP status from latest ssp_section
    ssp_row = db.execute(text("""
        SELECT implementation_status FROM ssp_sections
        WHERE org_id = :o AND control_id = :c
        ORDER BY version DESC LIMIT 1
    """), {"o": org_id, "c": control_id}).fetchone()
    ssp_status = (ssp_row.implementation_status if ssp_row else "Not Assessed").strip()
    is_met = ssp_status.lower() in ("met", "fully implemented")

    risk = 0.0
    factors: list[str] = []

    if cc["conflict"] > 0:
        risk += cc["conflict"] * 10 * weight
        factors.append(f"{cc['conflict']} claim(s) contradicted by evidence")
    if is_met and cc["unverified"] > 0:
        risk += cc["unverified"] * 3 * weight
        factors.append(f"{cc['unverified']} unverified claim(s) on MET control")
    if cc["stale"] > 0:
        risk += cc["stale"] * 5 * weight
        factors.append(f"{cc['stale']} claim(s) supported by stale evidence")
    if is_met:
        missing = 3 - mc["method_count"]
        if missing > 0:
            risk += missing * 2 * weight
            missing_names = [
                m for m in ("EXAMINE", "INTERVIEW", "TEST")
                if not mc.get(m.lower(), False)
            ]
            factors.append(f"Missing {missing} method(s): {', '.join(missing_names)}")

    return {
        "control_id":      control_id,
        "control_title":   title,
        "control_weight":  weight,
        "ssp_status":      ssp_status,
        "claim_counts":    cc,
        "method_coverage": mc,
        "risk_score":      round(risk, 1),
        "risk_factors":    factors,
    }


# ── Top-conflict observation text helper ──────────────────────────────────

def _top_conflict_observation(control_id: str, org_id: str, db: Session) -> Optional[str]:
    row = db.execute(text("""
        SELECT o.observation_text
        FROM resolutions r
        JOIN claims c       ON c.id = r.claim_id
        JOIN observations o ON o.id = r.observation_id
        WHERE c.org_id = :o
          AND c.control_id = :c
          AND r.relationship = 'CONTRADICTS'
        ORDER BY r.confidence DESC
        LIMIT 1
    """), {"o": org_id, "c": control_id}).fetchone()
    return row.observation_text if row else None


# ── Likely failures ───────────────────────────────────────────────────────

def identify_likely_failures(org_id: str, db: Session, top_n: int = 10) -> list[dict]:
    controls = db.execute(text("""
        SELECT DISTINCT control_id FROM claims WHERE org_id = :o
    """), {"o": org_id}).fetchall()

    scored: list[dict] = []
    for r in controls:
        risk = compute_control_risk_score(r.control_id, org_id, db)
        if risk["risk_score"] > 0:
            risk["top_conflict_observation"] = _top_conflict_observation(r.control_id, org_id, db)
            scored.append(risk)

    scored.sort(key=lambda x: x["risk_score"], reverse=True)
    return scored[:top_n]


# ── LLM finding generation ───────────────────────────────────────────────

_FINDING_SYSTEM = (
    "You are a CMMC C3PAO assessor writing a finding for an assessment "
    "report. Write in measured, factual tone. Each finding should: "
    "state the objective, state the assertion, state the contradicting "
    "or missing evidence, and recommend specific remediation. "
    "Do not use first person. Maximum 4 sentences. Return plain text only."
)


def generate_assessor_finding(
    control_id: str, control_title: str, risk_data: dict, db: Session,
) -> str:
    """Single LLM call. Falls back to a template on any failure."""
    user_prompt = (
        f"Control: {control_id} — {control_title}\n"
        f"SSP Status: {risk_data.get('ssp_status', 'Unknown')}\n"
        f"Claims: {json.dumps(risk_data.get('claim_counts', {}))}\n"
        f"Method Coverage: {json.dumps(risk_data.get('method_coverage', {}))}\n"
        f"Risk Factors: {json.dumps(risk_data.get('risk_factors', []))}\n"
    )
    top_obs = risk_data.get("top_conflict_observation")
    if top_obs:
        user_prompt += f"Contradicting Observation: {top_obs[:500]}\n"

    try:
        from src.agents.llm_client import get_llm
        llm = get_llm()
        return llm.generate(
            system_prompt=_FINDING_SYSTEM,
            user_prompt=user_prompt,
            max_tokens=512,
            temperature=0.2,
        ).strip()
    except Exception:
        logger.exception("Finding generation failed for %s", control_id)
        factors = "; ".join(risk_data.get("risk_factors", ["no details"]))
        return (
            f"{control_id} ({control_title}): Assessment risk identified. "
            f"Issues: {factors}. "
            f"Recommendation: Address the identified gaps before the C3PAO assessment."
        )


# ── Truth-adjusted SPRS ──────────────────────────────────────────────────

def compute_truth_adjusted_sprs(org_id: str, db: Session) -> dict:
    """Call the existing SPRS engine and apply truth-model penalties."""
    from src.scoring.sprs import SPRSCalculator

    calc = SPRSCalculator(org_id)
    result = calc.calculate()

    actual_score = result.score
    penalty_total = 0
    penalized: list[dict] = []

    for ctrl in result.controls:
        is_met = ctrl.status_label.upper() in ("MET",)
        if not is_met:
            continue

        cc = _claim_counts(ctrl.control_id, org_id, db)
        w = ctrl.points

        if cc["conflict"] > 0:
            p = round(CONFLICT_PENALTY_MULTIPLIER * w)
            penalty_total += p
            penalized.append({
                "control_id": ctrl.control_id,
                "reason":     f"{cc['conflict']} conflicting claim(s)",
                "penalty":    p,
            })
        elif cc["stale"] > 0:
            p = round(STALE_PENALTY_MULTIPLIER * w)
            penalty_total += p
            penalized.append({
                "control_id": ctrl.control_id,
                "reason":     f"{cc['stale']} stale claim(s)",
                "penalty":    p,
            })

    adjusted = max(SPRS_FLOOR, actual_score - penalty_total)
    return {
        "sprs_actual":         actual_score,
        "sprs_truth_adjusted": adjusted,
        "sprs_delta":          actual_score - adjusted,
        "penalized_controls":  penalized,
        "floor":               SPRS_FLOOR,
    }


# ── Readiness percentage ─────────────────────────────────────────────────

def compute_readiness_pct(org_id: str, db: Session) -> dict:
    sprs = compute_truth_adjusted_sprs(org_id, db)

    res_summary_row = db.execute(text("""
        SELECT COUNT(*) FILTER (WHERE verification_status IN ('VERIFIED','CONFLICT'))
               AS covered,
               COUNT(*) AS total
        FROM claims WHERE org_id = :o
    """), {"o": org_id}).fetchone()
    coverage_pct = (
        (res_summary_row.covered / res_summary_row.total * 100)
        if res_summary_row and res_summary_row.total > 0 else 0.0
    )

    controls_with_claims = db.execute(text("""
        SELECT DISTINCT control_id FROM claims WHERE org_id = :o
    """), {"o": org_id}).fetchall()
    if controls_with_claims:
        mc_sum = 0.0
        for r in controls_with_claims:
            mc = compute_method_coverage(r.control_id, org_id, db)
            mc_sum += mc["coverage_pct"]
        avg_mc = mc_sum / len(controls_with_claims)
    else:
        avg_mc = 0.0

    stale_claims = db.execute(text("""
        SELECT COUNT(*) FROM claims
        WHERE org_id = :o AND verification_status = 'STALE'
    """), {"o": org_id}).scalar() or 0
    total_claims = db.execute(text(
        "SELECT COUNT(*) FROM claims WHERE org_id = :o"
    ), {"o": org_id}).scalar() or 0
    stale_pct = (stale_claims / total_claims) if total_claims > 0 else 0.0

    adj = max(0, sprs["sprs_truth_adjusted"])
    components = {
        "sprs_score_component":      round(adj / 110 * 100 * 0.40, 1),
        "coverage_component":        round(coverage_pct * 0.20, 1),
        "method_coverage_component": round(avg_mc * 0.25, 1),
        "freshness_component":       round((1 - stale_pct) * 100 * 0.15, 1),
    }
    total = min(100.0, max(0.0, round(sum(components.values()), 1)))
    return {
        "readiness_pct": total,
        "components":    components,
    }


# ── Full simulation ──────────────────────────────────────────────────────

def run_simulation(org_id: str, db: Session, user_id: Optional[str] = None) -> dict:
    safe_user = _safe_user_fk(db, user_id)
    now = datetime.now(timezone.utc)

    sprs = compute_truth_adjusted_sprs(org_id, db)
    failures = identify_likely_failures(org_id, db, top_n=10)

    for f in failures:
        f["finding"] = generate_assessor_finding(
            f["control_id"], f.get("control_title", ""), f, db,
        )

    # Org-wide claim counts
    status_rows = db.execute(text("""
        SELECT verification_status, COUNT(*) FROM claims
        WHERE org_id = :o GROUP BY verification_status
    """), {"o": org_id}).fetchall()
    by_status = {r[0]: int(r[1]) for r in status_rows}
    total_claims = sum(by_status.values())

    readiness = compute_readiness_pct(org_id, db)

    snapshot_id = _gen_id(f"assess:{org_id}:{now.isoformat()}")

    findings_for_json = [
        {k: v for k, v in f.items() if k != "method_coverage"}
        for f in failures
    ]

    db.execute(text("""
        INSERT INTO assessment_snapshots
            (id, org_id, created_at, created_by,
             readiness_pct, sprs_actual, sprs_truth_adjusted, sprs_delta,
             total_claims, verified_claims, conflict_claims,
             unverified_claims, stale_claims,
             controls_at_risk, method_coverage_pct,
             findings_json, details_json)
        VALUES
            (:id, :o, :now, :by,
             :readiness, :actual, :adjusted, :delta,
             :total, :verified, :conflict,
             :unverified, :stale,
             :at_risk, :mc_pct,
             CAST(:findings AS jsonb), CAST(:details AS jsonb))
    """), {
        "id":         snapshot_id,
        "o":          org_id,
        "now":        now,
        "by":         safe_user,
        "readiness":  readiness["readiness_pct"],
        "actual":     sprs["sprs_actual"],
        "adjusted":   sprs["sprs_truth_adjusted"],
        "delta":      sprs["sprs_delta"],
        "total":      total_claims,
        "verified":   by_status.get("VERIFIED",   0),
        "conflict":   by_status.get("CONFLICT",   0),
        "unverified": by_status.get("UNVERIFIED", 0),
        "stale":      by_status.get("STALE",      0),
        "at_risk":    len(failures),
        "mc_pct":     readiness["components"].get("method_coverage_component"),
        "findings":   json.dumps(findings_for_json),
        "details":    json.dumps({
            "sprs":          sprs,
            "readiness":     readiness,
            "claim_status":  by_status,
        }),
    })
    db.commit()

    _audit(
        db, actor=safe_user or "system", action="ASSESSMENT_SIMULATION_RUN",
        target_id=snapshot_id,
        details={
            "org_id":       org_id,
            "readiness_pct": readiness["readiness_pct"],
            "sprs_delta":   sprs["sprs_delta"],
            "at_risk":      len(failures),
        },
    )
    db.commit()

    return {
        "snapshot_id":          snapshot_id,
        "readiness_pct":        readiness["readiness_pct"],
        "readiness_components": readiness["components"],
        "sprs_actual":          sprs["sprs_actual"],
        "sprs_truth_adjusted":  sprs["sprs_truth_adjusted"],
        "sprs_delta":           sprs["sprs_delta"],
        "penalized_controls":   sprs["penalized_controls"],
        "total_claims":         total_claims,
        "verified_claims":      by_status.get("VERIFIED",   0),
        "conflict_claims":      by_status.get("CONFLICT",   0),
        "unverified_claims":    by_status.get("UNVERIFIED", 0),
        "stale_claims":         by_status.get("STALE",      0),
        "controls_at_risk":     len(failures),
        "likely_failures":      failures,
    }
