"""
src/truth/claim_extractor.py

Decompose an SSP narrative into atomic, verifiable claims using the
same LLM client that powers SSP generation (ComplianceLLM / Claude
Sonnet in dev, vLLM in prod).

Each claim is one checkable fact an assessor could verify: a policy
reference, a system config, or a recurring operational activity. Claims
are persisted to the ``claims`` table and linked to the SSP section
they came from. Re-extraction is idempotent — prior claims for the
same (org_id, ssp_section_id) are wiped before new rows are inserted.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.agents.llm_client import get_llm

logger = logging.getLogger(__name__)


_VALID_TYPES = {"POLICY", "TECHNICAL", "OPERATIONAL"}
_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def _gen_id(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()[:20]


def _audit(db: Session, *, actor: str, action: str, target_id: str, details: dict) -> None:
    try:
        from src.evidence.state_machine import create_audit_entry
        create_audit_entry(
            db=db,
            actor=actor,
            actor_type="user",
            action=action,
            target_type="ssp_section",
            target_id=target_id,
            details=details,
        )
    except Exception:
        logger.exception("audit entry %s failed", action)


def _safe_user_fk(db: Session, user_id: Optional[str]) -> Optional[str]:
    if not user_id:
        return None
    row = db.execute(text("SELECT 1 FROM users WHERE id = :id"), {"id": user_id}).fetchone()
    return user_id if row else None


# ── LLM prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are a CMMC compliance analyst extracting verifiable claims from "
    "System Security Plan narratives. Return ONLY a JSON array — no "
    "preamble, no markdown fences, no trailing commentary."
)


def _build_user_prompt(control_id: str, control_title: str, narrative: str) -> str:
    return f"""For the given SSP section, identify every atomic, verifiable factual claim.

Rules:
1. Each claim must be a single verifiable fact, not a compound statement.
2. Skip generic boilerplate (e.g. "The organization values security").
3. Classify each claim:
   - POLICY      = documented governance (policies, procedures, standards, roles)
   - TECHNICAL   = system / tool configuration (MFA, encryption, firewall rules, software versions)
   - OPERATIONAL = recurring human process (reviews, training, audits, incident response activities)
4. source_sentence MUST be a VERBATIM substring taken directly from the narrative — do not paraphrase.
5. confidence: 1.0 = clearly verifiable specific claim; 0.5 = somewhat verifiable; <0.3 = likely boilerplate.
6. suggested_evidence is a short list of evidence artifact types that would verify this claim.

CONTROL: {control_id} — {control_title}

NARRATIVE:
\"\"\"
{narrative}
\"\"\"

Respond with ONLY a JSON array:
[
  {{
    "claim_text": "<atomic verifiable claim>",
    "claim_type": "POLICY|TECHNICAL|OPERATIONAL",
    "source_sentence": "<verbatim substring from narrative>",
    "confidence": 0.0-1.0,
    "suggested_evidence": ["<type 1>", "<type 2>"]
  }}
]"""


def _strip_fences(raw: str) -> str:
    return _JSON_FENCE_RE.sub("", raw.strip()).strip()


def _parse_llm_json_array(raw: str) -> list[dict]:
    cleaned = _strip_fences(raw)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        # Last-ditch: snip the outermost [...] and retry.
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end > start:
            try:
                parsed = json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                logger.warning("Claim extraction JSON parse failed. Raw: %s", raw[:500])
                return []
        else:
            logger.warning("Claim extraction JSON parse failed (no array). Raw: %s", raw[:500])
            return []
    if not isinstance(parsed, list):
        logger.warning("Claim extraction returned non-list: %r", type(parsed))
        return []
    return [c for c in parsed if isinstance(c, dict)]


# ── Span locator ──────────────────────────────────────────────────────────

def _locate_span(narrative: str, source: Optional[str]) -> tuple[Optional[int], Optional[int]]:
    """Return (start, end) character offsets of ``source`` within
    ``narrative``. Exact substring match first; falls back to a
    sentence-level fuzzy match (best SequenceMatcher ratio ≥ 0.6)."""
    if not narrative or not source:
        return (None, None)

    src = source.strip()
    if not src:
        return (None, None)

    idx = narrative.find(src)
    if idx != -1:
        return (idx, idx + len(src))

    # Fuzzy fallback — split narrative into rough sentences, pick best match.
    sentences: list[tuple[int, int, str]] = []
    cursor = 0
    for chunk in re.split(r"(?<=[.!?])\s+", narrative):
        if not chunk:
            cursor += len(chunk)
            continue
        start = narrative.find(chunk, cursor)
        if start == -1:
            start = cursor
        end = start + len(chunk)
        sentences.append((start, end, chunk))
        cursor = end

    best: Optional[tuple[float, int, int]] = None
    src_l = src.lower()
    for start, end, sent in sentences:
        ratio = SequenceMatcher(None, sent.lower(), src_l).ratio()
        if ratio >= 0.6 and (best is None or ratio > best[0]):
            best = (ratio, start, end)

    if best is None:
        return (None, None)
    return (best[1], best[2])


# ── Evidence ref mapping ──────────────────────────────────────────────────

def _load_evidence_ids_for_control(db: Session, org_id: str, control_id: str) -> list[str]:
    """All evidence_artifacts linked to this control via evidence_control_map
    for the org. Used as the pool of concrete IDs we can attach to claims."""
    rows = db.execute(text("""
        SELECT DISTINCT ea.id
        FROM evidence_artifacts ea
        JOIN evidence_control_map ecm ON ecm.evidence_id = ea.id
        WHERE ea.org_id = :org_id AND ecm.control_id = :cid
    """), {"org_id": org_id, "cid": control_id}).fetchall()
    return [r[0] for r in rows]


# ── Main extractor ────────────────────────────────────────────────────────

def extract_claims_from_section(
    narrative: str,
    control_id: str,
    control_title: str,
    org_id: str,
    ssp_section_id: str,
    db: Session,
    user_id: str,
) -> list[dict]:
    """Extract + persist claims for a single SSP section.

    Idempotent: wipes existing claims for (org_id, ssp_section_id) before
    inserting. LLM/parse failures return an empty list — never raise.
    """
    narrative = (narrative or "").strip()
    if not narrative:
        return []

    safe_user_id = _safe_user_fk(db, user_id)
    evidence_pool = _load_evidence_ids_for_control(db, org_id, control_id)

    # ── LLM call ─────────────────────────────────────────────────────────
    llm = get_llm()
    try:
        raw = llm.generate(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=_build_user_prompt(control_id, control_title, narrative),
            max_tokens=2048,
            temperature=0.1,
        )
    except Exception:
        logger.exception("LLM call failed for claim extraction on %s", control_id)
        return []

    parsed = _parse_llm_json_array(raw)
    if not parsed:
        logger.info("No claims parsed for %s (section %s)", control_id, ssp_section_id)
        return []

    extraction_model = getattr(llm, "model", None) or "unknown"
    now = datetime.now(timezone.utc)

    # ── Wipe old claims for this section (idempotent re-extract) ─────────
    db.execute(text("""
        DELETE FROM claims
        WHERE org_id = :org_id AND ssp_section_id = :sid
    """), {"org_id": org_id, "sid": ssp_section_id})

    inserted: list[dict] = []
    for raw_claim in parsed:
        claim_text = (raw_claim.get("claim_text") or "").strip()
        if not claim_text:
            continue

        claim_type = (raw_claim.get("claim_type") or "TECHNICAL").strip().upper()
        if claim_type not in _VALID_TYPES:
            claim_type = "TECHNICAL"

        source_sentence = (raw_claim.get("source_sentence") or "").strip() or None
        span_start, span_end = _locate_span(narrative, source_sentence)

        try:
            confidence = float(raw_claim.get("confidence"))
        except (TypeError, ValueError):
            confidence = None

        # Best-effort evidence mapping: attach every evidence artifact
        # already linked to this control — the UI filters further.
        evidence_refs = list(evidence_pool) if evidence_pool else None

        claim_id = _gen_id(
            f"claim:{org_id}:{control_id}:{hashlib.sha256(claim_text.encode()).hexdigest()}"
        )

        db.execute(text("""
            INSERT INTO claims
                (id, org_id, control_id, ssp_section_id, claim_text, claim_type,
                 verification_status, source_sentence, source_span_start, source_span_end,
                 confidence, evidence_refs, extracted_at, extraction_model)
            VALUES
                (:id, :org_id, :cid, :sid, :text, :ctype,
                 'UNVERIFIED', :src, :start, :end,
                 :conf, :refs, :now, :model)
            ON CONFLICT (id) DO UPDATE SET
                claim_text        = EXCLUDED.claim_text,
                claim_type        = EXCLUDED.claim_type,
                source_sentence   = EXCLUDED.source_sentence,
                source_span_start = EXCLUDED.source_span_start,
                source_span_end   = EXCLUDED.source_span_end,
                confidence        = EXCLUDED.confidence,
                evidence_refs     = EXCLUDED.evidence_refs,
                extracted_at      = EXCLUDED.extracted_at,
                extraction_model  = EXCLUDED.extraction_model
        """), {
            "id":     claim_id,
            "org_id": org_id,
            "cid":    control_id,
            "sid":    ssp_section_id,
            "text":   claim_text,
            "ctype":  claim_type,
            "src":    source_sentence,
            "start":  span_start,
            "end":    span_end,
            "conf":   confidence,
            "refs":   evidence_refs,
            "now":    now,
            "model":  extraction_model,
        })

        inserted.append({
            "id":                  claim_id,
            "org_id":              org_id,
            "control_id":          control_id,
            "ssp_section_id":      ssp_section_id,
            "claim_text":          claim_text,
            "claim_type":          claim_type,
            "verification_status": "UNVERIFIED",
            "source_sentence":     source_sentence,
            "source_span_start":   span_start,
            "source_span_end":     span_end,
            "confidence":          confidence,
            "evidence_refs":       evidence_refs or [],
            "suggested_evidence":  raw_claim.get("suggested_evidence") or [],
            "extracted_at":        now.isoformat(),
            "extraction_model":    extraction_model,
        })

    db.commit()

    _audit(
        db,
        actor=safe_user_id or "system",
        action="CLAIMS_EXTRACTED",
        target_id=ssp_section_id,
        details={
            "org_id":        org_id,
            "control_id":    control_id,
            "claim_count":   len(inserted),
            "by_type":       _count_by(inserted, "claim_type"),
            "model":         extraction_model,
        },
    )
    db.commit()

    return inserted


def _count_by(claims: list[dict], key: str) -> dict:
    out: dict[str, int] = {}
    for c in claims:
        v = c.get(key)
        if v:
            out[v] = out.get(v, 0) + 1
    return out


def extract_claims_for_org(
    org_id: str,
    db: Session,
    user_id: str,
    control_ids: Optional[list[str]] = None,
) -> dict:
    """Extract claims across every latest-version SSP section for the org.

    When ``control_ids`` is provided, scoped to those control IDs.
    Never crashes on a single-section failure — logs, accumulates into
    ``errors``, and moves on.
    """
    params: dict[str, Any] = {"org_id": org_id}
    scope_sql = ""
    if control_ids:
        scope_sql = "AND ss.control_id = ANY(:cids)"
        params["cids"] = control_ids

    sections = db.execute(text(f"""
        SELECT DISTINCT ON (ss.control_id)
               ss.id, ss.control_id, ss.narrative,
               COALESCE(c.title, ss.control_id) AS control_title
        FROM ssp_sections ss
        LEFT JOIN controls c ON c.id = ss.control_id
        WHERE ss.org_id = :org_id
          AND ss.narrative IS NOT NULL
          AND ss.narrative <> ''
          {scope_sql}
        ORDER BY ss.control_id, ss.version DESC
    """), params).fetchall()

    total_sections = 0
    total_claims = 0
    by_type: dict[str, int] = {}
    errors: list[dict] = []

    for row in sections:
        total_sections += 1
        try:
            claims = extract_claims_from_section(
                narrative=row.narrative,
                control_id=row.control_id,
                control_title=row.control_title,
                org_id=org_id,
                ssp_section_id=row.id,
                db=db,
                user_id=user_id,
            )
            total_claims += len(claims)
            for c in claims:
                ct = c.get("claim_type") or "TECHNICAL"
                by_type[ct] = by_type.get(ct, 0) + 1
        except Exception as exc:
            logger.exception("extract_claims_for_org: section %s failed", row.id)
            errors.append({"section_id": row.id, "control_id": row.control_id, "error": str(exc)[:200]})

    return {
        "total_sections_processed": total_sections,
        "total_claims_extracted":   total_claims,
        "by_type":                  by_type,
        "by_status":                {"UNVERIFIED": total_claims},
        "errors":                   errors,
    }
