"""
src/truth/resolver.py

Resolution engine (Phase 4.3). For each control, pair every claim
against every observation that references that control and ask the LLM
whether the observation SUPPORTS, CONTRADICTS, or is UNRELATED to the
claim. Roll up per-claim verdicts into ``claims.verification_status``
using the priority:  CONFLICT > VERIFIED > UNVERIFIED.

LLM calls go through the same ``get_llm()`` client that powers claim
extraction.  JSON parsing failures degrade to ``UNRELATED`` rather than
aborting the resolve pass.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.agents.llm_client import get_llm

logger = logging.getLogger(__name__)


_VALID_RELATIONSHIPS = {"SUPPORTS", "CONTRADICTS", "UNRELATED"}
_MATCH_CONFIDENCE    = 0.6    # threshold above which SUPPORTS/CONTRADICTS counts

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def _gen_id(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()[:20]


def _audit(db: Session, *, actor: str, action: str, target_id: str, details: dict) -> None:
    try:
        from src.evidence.state_machine import create_audit_entry
        create_audit_entry(
            db=db, actor=actor, actor_type="user", action=action,
            target_type="control", target_id=target_id, details=details,
        )
    except Exception:
        logger.exception("audit %s failed", action)


def _safe_user_fk(db: Session, user_id: Optional[str]) -> Optional[str]:
    if not user_id:
        return None
    row = db.execute(text("SELECT 1 FROM users WHERE id = :id"), {"id": user_id}).fetchone()
    return user_id if row else None


# ── LLM prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are a CMMC compliance assessor evaluating whether evidence "
    "observations support, contradict, or are unrelated to SSP claims. "
    "Return ONLY a JSON object — no markdown, no preamble."
)


def _build_user_prompt(
    control_id: str,
    claim_text: str, claim_type: str,
    observation_text: str, observation_type: str,
) -> str:
    return f"""Given:
- Control: {control_id}
- SSP Claim ({claim_type}): "{claim_text}"
- Evidence Observation ({observation_type}): "{observation_text}"

Determine the relationship:
- SUPPORTS: The observation provides evidence that the claim is true or partially true.
- CONTRADICTS: The observation provides evidence that the claim is false or misleading.
- UNRELATED: The observation has no bearing on this specific claim.

Respond with ONLY a JSON object:
{{"relationship": "SUPPORTS|CONTRADICTS|UNRELATED", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""


def _strip_fences(raw: str) -> str:
    return _JSON_FENCE_RE.sub("", raw.strip()).strip()


def _parse_verdict(raw: str) -> dict:
    """Best-effort JSON parse. Never raises — returns UNRELATED on failure."""
    cleaned = _strip_fences(raw)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end > start:
            try:
                parsed = json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                return {"relationship": "UNRELATED", "confidence": 0.0,
                        "reasoning": "LLM parse failure"}
        else:
            return {"relationship": "UNRELATED", "confidence": 0.0,
                    "reasoning": "LLM parse failure"}

    if not isinstance(parsed, dict):
        return {"relationship": "UNRELATED", "confidence": 0.0,
                "reasoning": "LLM returned non-object"}

    rel = str(parsed.get("relationship") or "").strip().upper()
    if rel not in _VALID_RELATIONSHIPS:
        rel = "UNRELATED"
    try:
        conf = float(parsed.get("confidence"))
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf))
    reasoning = str(parsed.get("reasoning") or "").strip()[:1000]
    return {"relationship": rel, "confidence": conf, "reasoning": reasoning}


# ── Pair-level resolve ────────────────────────────────────────────────────

def resolve_claim_observation_pair(
    claim_text: str,
    claim_type: str,
    observation_text: str,
    observation_type: str,
    control_id: str,
    _llm: Any = None,
) -> dict:
    """Ask the LLM for one verdict. ``_llm`` is an escape hatch so the
    caller can reuse a single client across many pairs (cheap keep-alive).
    """
    llm = _llm or get_llm()
    try:
        raw = llm.generate(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=_build_user_prompt(
                control_id=control_id,
                claim_text=claim_text, claim_type=claim_type,
                observation_text=observation_text, observation_type=observation_type,
            ),
            max_tokens=512,
            temperature=0.1,
        )
    except Exception:
        logger.exception("LLM call failed for resolution on %s", control_id)
        return {"relationship": "UNRELATED", "confidence": 0.0,
                "reasoning": "LLM call failed"}
    return _parse_verdict(raw)


# ── Claim status roll-up ──────────────────────────────────────────────────

def _rollup_status(resolutions: list[dict]) -> str:
    """Priority: CONFLICT > VERIFIED > UNVERIFIED.
    Only verdicts with confidence >= _MATCH_CONFIDENCE count."""
    has_conflict = any(
        r["relationship"] == "CONTRADICTS" and r["confidence"] >= _MATCH_CONFIDENCE
        for r in resolutions
    )
    if has_conflict:
        return "CONFLICT"
    has_support = any(
        r["relationship"] == "SUPPORTS" and r["confidence"] >= _MATCH_CONFIDENCE
        for r in resolutions
    )
    if has_support:
        return "VERIFIED"
    return "UNVERIFIED"


# ── Control-level resolve ─────────────────────────────────────────────────

def resolve_control(
    control_id: str,
    org_id: str,
    db: Session,
    user_id: str,
) -> dict:
    """Resolve every (claim, observation) pair for one control.

    Deletes existing resolutions for the control's claims before
    inserting, so a rerun reflects current claims/observations.
    """
    claims = db.execute(text("""
        SELECT id, claim_text, claim_type, verification_status
        FROM claims
        WHERE org_id = :o AND control_id = :c
    """), {"o": org_id, "c": control_id}).fetchall()

    observations = db.execute(text("""
        SELECT id, observation_text, observation_type
        FROM observations
        WHERE org_id = :o AND :c = ANY(control_ids)
    """), {"o": org_id, "c": control_id}).fetchall()

    if not claims:
        return {
            "control_id": control_id, "pairs_evaluated": 0,
            "claims_resolved": 0, "verified": 0, "conflict": 0, "unverified": 0,
        }

    # Wipe existing resolutions for these claims — idempotent rebuild.
    claim_ids = [c.id for c in claims]
    db.execute(text("""
        DELETE FROM resolutions
        WHERE org_id = :o AND claim_id = ANY(:ids)
    """), {"o": org_id, "ids": claim_ids})

    safe_user_id = _safe_user_fk(db, user_id)
    now = datetime.now(timezone.utc)

    pairs_evaluated = 0
    verdict_counts = {"SUPPORTS": 0, "CONTRADICTS": 0, "UNRELATED": 0}
    status_counts  = {"VERIFIED": 0, "CONFLICT": 0, "UNVERIFIED": 0}

    # If there are no observations, every claim falls through to UNVERIFIED.
    if not observations:
        for cl in claims:
            db.execute(text("""
                UPDATE claims
                SET verification_status = 'UNVERIFIED',
                    verified_at         = NULL,
                    verified_by         = NULL
                WHERE id = :id AND org_id = :o
            """), {"id": cl.id, "o": org_id})
            status_counts["UNVERIFIED"] += 1
        db.commit()
        _audit(
            db, actor=safe_user_id or "system", action="CLAIMS_RESOLVED",
            target_id=control_id,
            details={"org_id": org_id, "pairs_evaluated": 0, **status_counts},
        )
        db.commit()
        return {
            "control_id": control_id, "pairs_evaluated": 0,
            "claims_resolved": len(claims),
            "verified":   status_counts["VERIFIED"],
            "conflict":   status_counts["CONFLICT"],
            "unverified": status_counts["UNVERIFIED"],
        }

    llm = get_llm()
    model = getattr(llm, "model", None) or "unknown"

    for cl in claims:
        per_claim_verdicts: list[dict] = []
        for ob in observations:
            verdict = resolve_claim_observation_pair(
                claim_text=cl.claim_text,
                claim_type=cl.claim_type,
                observation_text=ob.observation_text,
                observation_type=ob.observation_type,
                control_id=control_id,
                _llm=llm,
            )
            pairs_evaluated += 1
            verdict_counts[verdict["relationship"]] = verdict_counts.get(verdict["relationship"], 0) + 1
            per_claim_verdicts.append(verdict)

            res_id = _gen_id(f"res:{cl.id}:{ob.id}")
            db.execute(text("""
                INSERT INTO resolutions
                    (id, org_id, claim_id, observation_id,
                     relationship, confidence, reasoning,
                     resolved_at, resolved_by, model_used)
                VALUES
                    (:id, :o, :cid, :oid,
                     :rel, :conf, :reason,
                     :now, :by, :model)
                ON CONFLICT (claim_id, observation_id) DO UPDATE SET
                    relationship = EXCLUDED.relationship,
                    confidence   = EXCLUDED.confidence,
                    reasoning    = EXCLUDED.reasoning,
                    resolved_at  = EXCLUDED.resolved_at,
                    resolved_by  = EXCLUDED.resolved_by,
                    model_used   = EXCLUDED.model_used
            """), {
                "id":     res_id,
                "o":      org_id,
                "cid":    cl.id,
                "oid":    ob.id,
                "rel":    verdict["relationship"],
                "conf":   verdict["confidence"],
                "reason": verdict["reasoning"],
                "now":    now,
                "by":     safe_user_id,
                "model":  model,
            })

        new_status = _rollup_status(per_claim_verdicts)
        status_counts[new_status] += 1

        if new_status == "UNVERIFIED":
            db.execute(text("""
                UPDATE claims
                SET verification_status = 'UNVERIFIED',
                    verified_at         = NULL,
                    verified_by         = NULL
                WHERE id = :id AND org_id = :o
            """), {"id": cl.id, "o": org_id})
        else:
            db.execute(text("""
                UPDATE claims
                SET verification_status = :status,
                    verified_at         = :now,
                    verified_by         = :by
                WHERE id = :id AND org_id = :o
            """), {
                "id": cl.id, "o": org_id,
                "status": new_status, "now": now, "by": safe_user_id,
            })

    db.commit()

    _audit(
        db, actor=safe_user_id or "system", action="CLAIMS_RESOLVED",
        target_id=control_id,
        details={
            "org_id":          org_id,
            "pairs_evaluated": pairs_evaluated,
            "by_relationship": verdict_counts,
            "by_status":       status_counts,
            "model":           model,
        },
    )
    db.commit()

    return {
        "control_id":      control_id,
        "pairs_evaluated": pairs_evaluated,
        "claims_resolved": len(claims),
        "verified":        status_counts["VERIFIED"],
        "conflict":        status_counts["CONFLICT"],
        "unverified":      status_counts["UNVERIFIED"],
        "by_relationship": verdict_counts,
    }


# ── Org-level resolve ─────────────────────────────────────────────────────

def resolve_all(
    org_id: str,
    db: Session,
    user_id: str,
    control_ids: Optional[list[str]] = None,
) -> dict:
    """Resolve every control that has at least one claim.

    When ``control_ids`` is given, scopes to just those. Per-control
    failures are logged to ``errors`` and do not abort the run.
    """
    if control_ids:
        params = {"o": org_id, "cids": list(control_ids)}
        rows = db.execute(text("""
            SELECT DISTINCT control_id
            FROM claims
            WHERE org_id = :o AND control_id = ANY(:cids)
            ORDER BY control_id
        """), params).fetchall()
    else:
        rows = db.execute(text("""
            SELECT DISTINCT control_id
            FROM claims
            WHERE org_id = :o
            ORDER BY control_id
        """), {"o": org_id}).fetchall()

    controls = [r[0] for r in rows]
    total_pairs = 0
    by_status   = {"VERIFIED": 0, "CONFLICT": 0, "UNVERIFIED": 0}
    errors:    list[dict] = []

    for cid in controls:
        try:
            summary = resolve_control(cid, org_id, db, user_id)
            total_pairs += summary.get("pairs_evaluated", 0)
            by_status["VERIFIED"]   += summary.get("verified",   0)
            by_status["CONFLICT"]   += summary.get("conflict",   0)
            by_status["UNVERIFIED"] += summary.get("unverified", 0)
        except Exception as exc:
            logger.exception("resolve_all: control %s failed", cid)
            errors.append({"control_id": cid, "error": str(exc)[:200]})

    return {
        "controls_processed": len(controls),
        "pairs_evaluated":    total_pairs,
        "by_status":          by_status,
        "errors":             errors,
    }


# ── Truth-model summary ───────────────────────────────────────────────────

def get_resolution_summary(org_id: str, db: Session) -> dict:
    """Dashboard rollup. Uses claims.verification_status (authoritative)
    and observation / resolution row counts for context."""
    status_rows = db.execute(text("""
        SELECT verification_status, COUNT(*) FROM claims
        WHERE org_id = :o GROUP BY verification_status
    """), {"o": org_id}).fetchall()
    status_counts = {r[0]: int(r[1]) for r in status_rows}
    total_claims = sum(status_counts.values())

    total_obs = db.execute(
        text("SELECT COUNT(*) FROM observations WHERE org_id = :o"),
        {"o": org_id},
    ).scalar() or 0
    total_res = db.execute(
        text("SELECT COUNT(*) FROM resolutions WHERE org_id = :o"),
        {"o": org_id},
    ).scalar() or 0

    verified   = status_counts.get("VERIFIED",   0)
    conflict   = status_counts.get("CONFLICT",   0)
    unverified = status_counts.get("UNVERIFIED", 0)
    stale      = status_counts.get("STALE",      0)

    coverage_pct = (
        (verified + conflict) / total_claims * 100.0
        if total_claims > 0 else 0.0
    )

    family_rows = db.execute(text("""
        SELECT SPLIT_PART(control_id, '.', 1) AS family,
               verification_status,
               COUNT(*) AS cnt
        FROM claims
        WHERE org_id = :o
        GROUP BY family, verification_status
    """), {"o": org_id}).fetchall()
    by_family: dict[str, dict[str, int]] = {}
    for fam, status, cnt in family_rows:
        bucket = by_family.setdefault(fam, {"verified": 0, "conflict": 0, "unverified": 0, "stale": 0})
        bucket[str(status).lower()] = int(cnt)

    return {
        "total_claims":       total_claims,
        "verified":           verified,
        "conflict":           conflict,
        "unverified":         unverified,
        "stale":              stale,
        "total_observations": int(total_obs),
        "total_resolutions":  int(total_res),
        "coverage_pct":       round(coverage_pct, 1),
        "by_family":          by_family,
    }
