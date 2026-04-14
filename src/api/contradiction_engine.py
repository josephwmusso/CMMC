"""
src/api/contradiction_engine.py

Phase 2.9A — cross-module consistency checks.

Each rule takes (answers, ctx, evidence_summary) and returns a list of
ContradictionFinding objects. Rules gracefully return [] when the
answers they need are not yet populated — that's the normal case for
partially-completed intakes and must NOT produce a spurious finding.

Persistence:
  run_and_sync(db, org_id, session_id) runs every rule, then upserts the
  findings into intake_contradictions using (org_id, rule_id) as the
  uniqueness key. OPEN rows whose rule stopped firing flip to RESOLVED.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Iterable, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


# ============================================================================
# Finding + helpers
# ============================================================================

@dataclass
class ContradictionFinding:
    rule_id: str
    family: str
    severity: str                   # CRITICAL / HIGH / MEDIUM / LOW
    description: str
    source_question_id: str
    source_answer: Optional[str] = None
    conflicting_question_id: Optional[str] = None
    conflicting_answer: Optional[str] = None
    affected_control_ids: list[str] = field(default_factory=list)


NEGATIVE_STATUSES = {"not implemented", "planned"}


def _status_is_negative(answer: Optional[str]) -> bool:
    if not answer:
        return False
    return answer.strip().lower() in NEGATIVE_STATUSES


def _first_present(answers: dict, *qids: str) -> Optional[tuple[str, str]]:
    """Return (qid, value) for the first question that has a non-empty answer."""
    for qid in qids:
        v = answers.get(qid)
        if v is not None and str(v).strip() != "":
            return qid, v
    return None


# ============================================================================
# Data loaders
# ============================================================================

def _load_answers(db: Session, org_id: str) -> dict[str, str]:
    """All intake answers for the org, keyed by question_id. Most recent wins."""
    rows = db.execute(text("""
        SELECT ir.question_id, ir.answer_value
        FROM intake_responses ir
        JOIN intake_sessions  s ON s.id = ir.session_id
        WHERE s.org_id = :oid
        ORDER BY ir.answered_at DESC
    """), {"oid": org_id}).fetchall()
    out: dict[str, str] = {}
    for qid, val in rows:
        if qid not in out:
            out[qid] = val
    return out


def _load_evidence_summary(db: Session, org_id: str) -> dict[str, dict]:
    """{control_id: {count: int, has_published: bool}} for the org.

    Used by rules that check "claims X but no evidence maps to X".
    """
    rows = db.execute(text("""
        SELECT ecm.control_id,
               COUNT(*) AS n,
               SUM(CASE WHEN ea.state = 'PUBLISHED' THEN 1 ELSE 0 END) AS n_pub
        FROM evidence_artifacts ea
        JOIN evidence_control_map ecm ON ecm.evidence_id = ea.id
        WHERE ea.org_id = :oid
        GROUP BY ecm.control_id
    """), {"oid": org_id}).fetchall()
    return {
        row[0]: {"count": int(row[1] or 0), "has_published": int(row[2] or 0) > 0}
        for row in rows
    }


def _latest_session_id(db: Session, org_id: str) -> Optional[str]:
    row = db.execute(text("""
        SELECT id FROM intake_sessions
        WHERE org_id = :oid
        ORDER BY started_at DESC
        LIMIT 1
    """), {"oid": org_id}).fetchone()
    return row[0] if row else None


# ============================================================================
# 14 rules — one per family
# ============================================================================

# --- AC (Access Control) ----------------------------------------------------
def rule_ac_01(answers: dict, ctx: dict, evidence: dict) -> list[ContradictionFinding]:
    """Claims RBAC (Module 1 AC answers positive) but has no identity provider."""
    idp = answers.get("m0_identity_provider") or ""
    if not idp:
        return []
    is_no_idp = idp.startswith("No centralized") or idp.lower().startswith("i'm not sure")
    # Proxy for "claims RBAC": any Module 1 AC status marked Fully/Partially implemented
    # OR m0_identity_provider is present (a non-empty IdP claim is itself an RBAC claim).
    if is_no_idp:
        return [ContradictionFinding(
            rule_id="CONTRADICTION_AC_01",
            family="AC",
            severity="CRITICAL",
            description=(
                "Organization records no centralized identity provider, but CMMC "
                "AC.L2-3.1.1 / 3.1.2 require authorized user enforcement. "
                "Without an identity provider, RBAC cannot be enforced."
            ),
            source_question_id="m0_identity_provider",
            source_answer=idp,
            affected_control_ids=["AC.L2-3.1.1", "AC.L2-3.1.2"],
        )]
    return []


# --- AT (Awareness & Training) ----------------------------------------------
def rule_at_01(answers: dict, ctx: dict, evidence: dict) -> list[ContradictionFinding]:
    tool = answers.get("m0_training_tool") or ""
    if not tool or tool.lower() in ("none", ""):
        return []
    status_321 = answers.get("m2_at_3.2.1_status")
    status_322 = answers.get("m2_at_3.2.2_status")
    if status_321 is None and status_322 is None:
        return []  # Module 2 AT not answered yet
    bad = [s for s in (status_321, status_322) if _status_is_negative(s)]
    if not bad:
        return []
    return [ContradictionFinding(
        rule_id="CONTRADICTION_AT_01",
        family="AT",
        severity="HIGH",
        description=(
            f"Organization reports using the training platform '{tool}' yet "
            "Module 2 AT answers indicate training controls are not implemented "
            "or only planned. Either the platform isn't being used as claimed, "
            "or the AT control status needs updating."
        ),
        source_question_id="m0_training_tool",
        source_answer=tool,
        conflicting_question_id="m2_at_3.2.1_status",
        conflicting_answer=status_321 or status_322,
        affected_control_ids=["AT.L2-3.2.1", "AT.L2-3.2.2"],
    )]


# --- AU (Audit & Accountability) -------------------------------------------
def rule_au_01(answers: dict, ctx: dict, evidence: dict) -> list[ContradictionFinding]:
    siem = answers.get("m0_siem") or ""
    if not siem or siem.lower().startswith(("no log", "i'm not sure")):
        return []
    status_331 = answers.get("m2_au_3.3.1_status")
    status_332 = answers.get("m2_au_3.3.2_status")
    if status_331 is None and status_332 is None:
        return []
    bad = [s for s in (status_331, status_332) if _status_is_negative(s)]
    if not bad:
        return []
    return [ContradictionFinding(
        rule_id="CONTRADICTION_AU_01",
        family="AU",
        severity="HIGH",
        description=(
            f"SIEM '{siem}' is in use, but Module 2 AU answers indicate audit "
            "log review and/or retention are not implemented. A SIEM without "
            "review procedures is not CMMC AU.L2-3.3.1/3.3.2 compliant."
        ),
        source_question_id="m0_siem",
        source_answer=siem,
        conflicting_question_id="m2_au_3.3.1_status",
        conflicting_answer=status_331 or status_332,
        affected_control_ids=["AU.L2-3.3.1", "AU.L2-3.3.2"],
    )]


# --- CM (Configuration Management) -----------------------------------------
def rule_cm_01(answers: dict, ctx: dict, evidence: dict) -> list[ContradictionFinding]:
    status_341 = answers.get("m3_cm_3.4.1_status")
    status_342 = answers.get("m3_cm_3.4.2_status")
    if status_341 is None and status_342 is None:
        return []
    claims_baseline = any(
        s and s.strip().lower() in ("fully implemented", "partially implemented")
        for s in (status_341, status_342)
    )
    if not claims_baseline:
        return []
    ev_341 = evidence.get("CM.L2-3.4.1") or {}
    ev_342 = evidence.get("CM.L2-3.4.2") or {}
    has_any = (ev_341.get("count", 0) + ev_342.get("count", 0)) > 0
    if has_any:
        return []
    return [ContradictionFinding(
        rule_id="CONTRADICTION_CM_01",
        family="CM",
        severity="HIGH",
        description=(
            "Intake claims configuration baselines are implemented, but no "
            "evidence artifacts are mapped to CM.L2-3.4.1 or CM.L2-3.4.2. "
            "Upload baseline documentation or scan results to substantiate "
            "the claim."
        ),
        source_question_id="m3_cm_3.4.1_status",
        source_answer=status_341,
        affected_control_ids=["CM.L2-3.4.1", "CM.L2-3.4.2"],
    )]


# --- IA (Identification & Authentication) ----------------------------------
def rule_ia_01(answers: dict, ctx: dict, evidence: dict) -> list[ContradictionFinding]:
    """Claims MFA everywhere via onboarding, but Module 3 IA shows partial MFA."""
    idp = answers.get("m0_identity_provider") or ""
    mfa_scope = answers.get("m3_ia_3.5.3_mfa_scope")
    if not idp or mfa_scope is None:
        return []
    claims_full_mfa = "with MFA" in idp
    weak = mfa_scope in (
        "Remote access and privileged accounts only",
        "Remote access only",
        "Not implemented",
    )
    if not (claims_full_mfa and weak):
        return []
    return [ContradictionFinding(
        rule_id="CONTRADICTION_IA_01",
        family="IA",
        severity="CRITICAL",
        description=(
            "Onboarding claims MFA is enabled on the identity provider, but "
            "Module 3 IA.L2-3.5.3 scope answer indicates MFA is only partially "
            "deployed. Under CMMC, MFA for privileged + network-access is "
            "required and the gap affects SPRS scoring."
        ),
        source_question_id="m0_identity_provider",
        source_answer=idp,
        conflicting_question_id="m3_ia_3.5.3_mfa_scope",
        conflicting_answer=mfa_scope,
        affected_control_ids=["IA.L2-3.5.3"],
    )]


# --- IR (Incident Response) -------------------------------------------------
def rule_ir_01(answers: dict, ctx: dict, evidence: dict) -> list[ContradictionFinding]:
    status_361 = answers.get("m4_ir_3.6.1_status")
    status_362 = answers.get("m4_ir_3.6.2_status")
    status_363 = answers.get("m4_ir_3.6.3_status")
    if status_361 is None and status_362 is None:
        return []
    negative = [s for s in (status_361, status_362, status_363) if _status_is_negative(s)]
    if not negative:
        return []
    # Only fire when 3.6.1 (plan) or 3.6.2 (reporting) are negative — 3.6.3 alone is weaker.
    if not (_status_is_negative(status_361) or _status_is_negative(status_362)):
        return []
    return [ContradictionFinding(
        rule_id="CONTRADICTION_IR_01",
        family="IR",
        severity="HIGH",
        description=(
            "Module 4 reports no incident response plan or no reporting process. "
            "CMMC IR.L2-3.6.1/3.6.2 require an operational IR capability; a "
            "DFARS-covered contractor must report cyber incidents within 72h."
        ),
        source_question_id="m4_ir_3.6.1_status",
        source_answer=status_361,
        conflicting_question_id="m4_ir_3.6.2_status",
        conflicting_answer=status_362,
        affected_control_ids=["IR.L2-3.6.1", "IR.L2-3.6.2"],
    )]


# --- MA (Maintenance) -------------------------------------------------------
def rule_ma_01(answers: dict, ctx: dict, evidence: dict) -> list[ContradictionFinding]:
    status_371 = answers.get("m4_ma_3.7.1_status")
    status_375 = answers.get("m4_ma_3.7.5_status")
    if status_371 is None and status_375 is None:
        return []
    if not (_status_is_negative(status_371) or _status_is_negative(status_375)):
        return []
    return [ContradictionFinding(
        rule_id="CONTRADICTION_MA_01",
        family="MA",
        severity="MEDIUM",
        description=(
            "Maintenance controls (logging or remote-maintenance MFA) are "
            "marked not implemented / planned. MA.L2-3.7.1 requires performed "
            "maintenance; MA.L2-3.7.5 requires MFA on nonlocal maintenance."
        ),
        source_question_id="m4_ma_3.7.1_status",
        source_answer=status_371,
        conflicting_question_id="m4_ma_3.7.5_status",
        conflicting_answer=status_375,
        affected_control_ids=["MA.L2-3.7.1", "MA.L2-3.7.5"],
    )]


# --- MP (Media Protection) --------------------------------------------------
def rule_mp_01(answers: dict, ctx: dict, evidence: dict) -> list[ContradictionFinding]:
    status_381 = answers.get("m5_mp_3.8.1_status")
    status_383 = answers.get("m5_mp_3.8.3_status")
    if status_381 is None and status_383 is None:
        return []
    if not _status_is_negative(status_383):
        return []
    return [ContradictionFinding(
        rule_id="CONTRADICTION_MP_01",
        family="MP",
        severity="MEDIUM",
        description=(
            "Media sanitization (MP.L2-3.8.3) is marked not implemented / "
            "planned, yet media protection (MP.L2-3.8.1) may be claimed. "
            "Sanitization is required before disposal or reuse."
        ),
        source_question_id="m5_mp_3.8.3_status",
        source_answer=status_383,
        conflicting_question_id="m5_mp_3.8.1_status",
        conflicting_answer=status_381,
        affected_control_ids=["MP.L2-3.8.1", "MP.L2-3.8.3"],
    )]


# --- PE (Physical Protection) -----------------------------------------------
def rule_pe_01(answers: dict, ctx: dict, evidence: dict) -> list[ContradictionFinding]:
    status_3101 = answers.get("m5_pe_3.10.1_status")
    status_3103 = answers.get("m5_pe_3.10.3_status")
    if status_3101 is None and status_3103 is None:
        return []
    if not _status_is_negative(status_3103):
        return []
    return [ContradictionFinding(
        rule_id="CONTRADICTION_PE_01",
        family="PE",
        severity="MEDIUM",
        description=(
            "Physical access is claimed (PE.L2-3.10.1) but visitor escort / "
            "visitor logging (PE.L2-3.10.3) is marked not implemented / "
            "planned. Both are required for assessor-grade physical control."
        ),
        source_question_id="m5_pe_3.10.3_status",
        source_answer=status_3103,
        conflicting_question_id="m5_pe_3.10.1_status",
        conflicting_answer=status_3101,
        affected_control_ids=["PE.L2-3.10.1", "PE.L2-3.10.3"],
    )]


# --- PS (Personnel Security) ------------------------------------------------
def rule_ps_01(answers: dict, ctx: dict, evidence: dict) -> list[ContradictionFinding]:
    status_391 = answers.get("m5_ps_3.9.1_status")
    status_392 = answers.get("m5_ps_3.9.2_status")
    if status_391 is None and status_392 is None:
        return []
    if not _status_is_negative(status_392):
        return []
    return [ContradictionFinding(
        rule_id="CONTRADICTION_PS_01",
        family="PS",
        severity="HIGH",
        description=(
            "Personnel screening may be performed but termination / role-change "
            "handling (PS.L2-3.9.2) is not implemented. CUI access must be "
            "revoked as part of separation or transfer."
        ),
        source_question_id="m5_ps_3.9.2_status",
        source_answer=status_392,
        conflicting_question_id="m5_ps_3.9.1_status",
        conflicting_answer=status_391,
        affected_control_ids=["PS.L2-3.9.1", "PS.L2-3.9.2"],
    )]


# --- RA (Risk Assessment) ---------------------------------------------------
def rule_ra_01(answers: dict, ctx: dict, evidence: dict) -> list[ContradictionFinding]:
    status_3111 = answers.get("m6_ra_3.11.1_status")
    status_3112 = answers.get("m6_ra_3.11.2_status")
    if status_3111 is None and status_3112 is None:
        return []
    if not (_status_is_negative(status_3111) or _status_is_negative(status_3112)):
        return []
    return [ContradictionFinding(
        rule_id="CONTRADICTION_RA_01",
        family="RA",
        severity="HIGH",
        description=(
            "Risk assessment process (RA.L2-3.11.1) or vulnerability scanning "
            "(RA.L2-3.11.2) is not implemented / planned. An ongoing risk "
            "program is required for CMMC Level 2."
        ),
        source_question_id="m6_ra_3.11.1_status",
        source_answer=status_3111,
        conflicting_question_id="m6_ra_3.11.2_status",
        conflicting_answer=status_3112,
        affected_control_ids=["RA.L2-3.11.1", "RA.L2-3.11.2"],
    )]


# --- CA (Security Assessment) ----------------------------------------------
def rule_ca_01(answers: dict, ctx: dict, evidence: dict) -> list[ContradictionFinding]:
    status_3121 = answers.get("m6_ca_3.12.1_status")
    status_3122 = answers.get("m6_ca_3.12.2_status")
    status_3124 = answers.get("m6_ca_3.12.4_status")  # SSP — NOT POA&M-eligible
    if status_3121 is None and status_3122 is None and status_3124 is None:
        return []
    ssp_missing = _status_is_negative(status_3124)
    negative_core = _status_is_negative(status_3121) or _status_is_negative(status_3122)
    if not (ssp_missing or negative_core):
        return []
    severity = "CRITICAL" if ssp_missing else "HIGH"
    description = (
        "System Security Plan (CA.L2-3.12.4) is not in place. CA.L2-3.12.4 "
        "CANNOT be placed on a POA&M — an SSP must exist at assessment time."
        if ssp_missing else
        "Security assessment (CA.L2-3.12.1) or POA&M process (CA.L2-3.12.2) "
        "is not implemented / planned. Both are required and POA&M must track "
        "every open gap."
    )
    source_qid = "m6_ca_3.12.4_status" if ssp_missing else "m6_ca_3.12.1_status"
    source_ans = status_3124 if ssp_missing else status_3121
    return [ContradictionFinding(
        rule_id="CONTRADICTION_CA_01",
        family="CA",
        severity=severity,
        description=description,
        source_question_id=source_qid,
        source_answer=source_ans,
        conflicting_question_id=("m6_ca_3.12.2_status" if not ssp_missing else None),
        conflicting_answer=(status_3122 if not ssp_missing else None),
        affected_control_ids=(
            ["CA.L2-3.12.4"] if ssp_missing
            else ["CA.L2-3.12.1", "CA.L2-3.12.2"]
        ),
    )]


# --- SC (System & Communications) ------------------------------------------
def rule_sc_01(answers: dict, ctx: dict, evidence: dict) -> list[ContradictionFinding]:
    status_3131 = answers.get("m7_sc_3.13.1_status")
    status_3138 = answers.get("m7_sc_3.13.8_status")
    status_31311 = answers.get("m7_sc_3.13.11_status")
    fips_scope = answers.get("m7_sc_3.13.11_fips_scope")
    if all(v is None for v in (status_3131, status_3138, status_31311, fips_scope)):
        return []
    negative = (
        _status_is_negative(status_3131)
        or _status_is_negative(status_3138)
        or _status_is_negative(status_31311)
        or fips_scope in ("No encryption", "Partial encryption coverage")
    )
    if not negative:
        return []
    return [ContradictionFinding(
        rule_id="CONTRADICTION_SC_01",
        family="SC",
        severity="CRITICAL",
        description=(
            "Boundary protection, transmission encryption, or FIPS-validated "
            "cryptography for CUI (SC.L2-3.13.1 / 3.13.8 / 3.13.11) is not "
            "implemented. FIPS 140-2/3 encryption is mandatory for CUI at "
            "rest and in transit."
        ),
        source_question_id="m7_sc_3.13.11_status",
        source_answer=status_31311,
        conflicting_question_id="m7_sc_3.13.11_fips_scope",
        conflicting_answer=fips_scope,
        affected_control_ids=["SC.L2-3.13.1", "SC.L2-3.13.8", "SC.L2-3.13.11"],
    )]


# --- SI (System & Information Integrity) -----------------------------------
def rule_si_01(answers: dict, ctx: dict, evidence: dict) -> list[ContradictionFinding]:
    edr = answers.get("m0_edr") or ""
    if not edr or edr.lower().startswith(("none", "i'm not sure")):
        return []
    status_3141 = answers.get("m8_si_3.14.1_status")
    status_3142 = answers.get("m8_si_3.14.2_status")
    status_3146 = answers.get("m8_si_3.14.6_status")
    if all(v is None for v in (status_3141, status_3142, status_3146)):
        return []
    if not (
        _status_is_negative(status_3142)
        or _status_is_negative(status_3146)
    ):
        return []
    return [ContradictionFinding(
        rule_id="CONTRADICTION_SI_01",
        family="SI",
        severity="HIGH",
        description=(
            f"Endpoint protection '{edr}' is reported, but Module 8 SI answers "
            "indicate malicious-code protection or continuous system monitoring "
            "are not implemented. SI.L2-3.14.2/3.14.6 require active deployment."
        ),
        source_question_id="m0_edr",
        source_answer=edr,
        conflicting_question_id="m8_si_3.14.2_status",
        conflicting_answer=status_3142,
        affected_control_ids=["SI.L2-3.14.1", "SI.L2-3.14.2", "SI.L2-3.14.6"],
    )]


# Registry of all rules — iterated by run_all_rules / run_family_rules.
RULES: list[tuple[str, Callable]] = [
    ("AC", rule_ac_01),
    ("AT", rule_at_01),
    ("AU", rule_au_01),
    ("CM", rule_cm_01),
    ("IA", rule_ia_01),
    ("IR", rule_ir_01),
    ("MA", rule_ma_01),
    ("MP", rule_mp_01),
    ("PE", rule_pe_01),
    ("PS", rule_ps_01),
    ("RA", rule_ra_01),
    ("CA", rule_ca_01),
    ("SC", rule_sc_01),
    ("SI", rule_si_01),
]


# ============================================================================
# Runner
# ============================================================================

def run_all_rules(
    db: Session, org_id: str, families: Optional[Iterable[str]] = None,
) -> list[ContradictionFinding]:
    """Evaluate rules for the given families (default: all) and return findings."""
    answers = _load_answers(db, org_id)
    # ctx is reserved for future rules; pass an empty dict for now.
    ctx: dict = {}
    evidence = _load_evidence_summary(db, org_id)
    family_filter = {f.upper() for f in families} if families else None
    findings: list[ContradictionFinding] = []
    for fam, fn in RULES:
        if family_filter and fam not in family_filter:
            continue
        try:
            findings.extend(fn(answers, ctx, evidence))
        except Exception as exc:  # a broken rule must not abort the scan
            import logging
            logging.getLogger(__name__).exception(
                "Contradiction rule %s.%s crashed: %s", fam, fn.__name__, exc,
            )
    return findings


def sync_findings(
    db: Session,
    org_id: str,
    findings: list[ContradictionFinding],
    *,
    families: Optional[Iterable[str]] = None,
    session_id: Optional[str] = None,
) -> dict[str, int]:
    """Upsert findings into intake_contradictions.

    families: if set, only sync within those families (rules-run scope).
              Rules not in this scope are left alone; OPEN rows in scope
              that didn't fire this run flip to RESOLVED.
    Returns {detected, resolved, total_open}.
    """
    now = datetime.now(timezone.utc).isoformat()
    fired_rule_ids = {f.rule_id for f in findings}

    # Active OPEN rows for this org — filtered by family if scoped.
    existing_query = (
        "SELECT rule_id, family FROM intake_contradictions "
        "WHERE org_id = :oid AND status = 'OPEN'"
    )
    existing_rows = db.execute(text(existing_query), {"oid": org_id}).fetchall()

    family_filter = {f.upper() for f in families} if families else None

    detected = 0
    for f in findings:
        if family_filter and f.family not in family_filter:
            continue
        # Upsert by (org_id, rule_id) unique key.
        row_id = hashlib.sha256(f"{org_id}:{f.rule_id}".encode()).hexdigest()[:20]
        db.execute(text("""
            INSERT INTO intake_contradictions
                (id, org_id, session_id, rule_id, family, severity, status,
                 description, source_question_id, source_answer,
                 conflicting_question_id, conflicting_answer,
                 affected_control_ids, detected_at, updated_at)
            VALUES
                (:id, :oid, :sid, :rule_id, :family, :sev, 'OPEN',
                 :desc, :sqid, :sans, :cqid, :cans,
                 CAST(:ctrls AS json), :now, :now)
            ON CONFLICT (org_id, rule_id) DO UPDATE SET
                session_id              = :sid,
                family                  = :family,
                severity                = :sev,
                status                  = CASE
                    WHEN intake_contradictions.status IN ('DISMISSED', 'OVERRIDDEN')
                        THEN intake_contradictions.status
                    ELSE 'OPEN'
                END,
                description             = :desc,
                source_question_id      = :sqid,
                source_answer           = :sans,
                conflicting_question_id = :cqid,
                conflicting_answer      = :cans,
                affected_control_ids    = CAST(:ctrls AS json),
                updated_at              = :now,
                resolved_at             = NULL,
                resolved_by             = NULL
        """), {
            "id": row_id,
            "oid": org_id,
            "sid": session_id,
            "rule_id": f.rule_id,
            "family": f.family,
            "sev": f.severity,
            "desc": f.description,
            "sqid": f.source_question_id,
            "sans": f.source_answer,
            "cqid": f.conflicting_question_id,
            "cans": f.conflicting_answer,
            "ctrls": json.dumps(f.affected_control_ids),
            "now": now,
        })
        detected += 1

    # Auto-resolve OPEN rows in scope that no longer fire.
    resolved = 0
    for rule_id, fam in existing_rows:
        if family_filter and fam not in family_filter:
            continue
        if rule_id in fired_rule_ids:
            continue
        r = db.execute(text("""
            UPDATE intake_contradictions
            SET status = 'RESOLVED', resolved_at = :now, updated_at = :now
            WHERE org_id = :oid AND rule_id = :rid AND status = 'OPEN'
        """), {"oid": org_id, "rid": rule_id, "now": now})
        resolved += r.rowcount or 0

    total_open = db.execute(text("""
        SELECT COUNT(*) FROM intake_contradictions
        WHERE org_id = :oid AND status = 'OPEN'
    """), {"oid": org_id}).scalar() or 0

    return {"detected": detected, "resolved": resolved, "total_open": int(total_open)}


def run_and_sync(
    db: Session,
    org_id: str,
    *,
    families: Optional[Iterable[str]] = None,
    session_id: Optional[str] = None,
) -> dict[str, int]:
    """Convenience: run rules → sync → return the counters."""
    findings = run_all_rules(db, org_id, families=families)
    if session_id is None:
        session_id = _latest_session_id(db, org_id)
    return sync_findings(db, org_id, findings, families=families, session_id=session_id)


# Map of module_id → family list — used by intake_routes for the post-save
# lightweight scan. Module 0 alone doesn't run any rules directly.
MODULE_TO_FAMILIES: dict[int, list[str]] = {
    0: [],
    1: ["AC"],
    2: ["AT", "AU"],
    3: ["CM", "IA"],
    4: ["IR", "MA"],
    5: ["MP", "PE", "PS"],
    6: ["RA", "CA"],
    7: ["SC"],
    8: ["SI"],
}
