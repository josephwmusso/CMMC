"""
src/api/intake_routes.py
FastAPI routes for the guided intake questionnaire.

Question banks live in src.api.intake_modules (one file per module). This
router just wires the registry to HTTP endpoints.

Endpoints:
  POST   /api/intake/sessions                       — Start a new intake session
  GET    /api/intake/sessions/{id}                  — Get session status + progress
  GET    /api/intake/sessions/{id}/module/{n}       — Get questions for module N (+ saved answers)
  GET    /api/intake/sessions/{id}/progress         — Per-module progress stats
  POST   /api/intake/sessions/{id}/responses        — Save one or more answers
  POST   /api/intake/company-profile                — Save Module 0 structured profile
  GET    /api/intake/company-profile/{org_id}       — Get saved company profile
  GET    /api/intake/modules                        — List all registered modules (summary)
  GET    /api/intake/modules/{n}                    — Full module definition + questions
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import bindparam, text

from src.api.auth import get_current_user, is_superadmin
from src.db.session import get_session
from src.api.intake_modules import (
    find_question,
    get_all_modules,
    get_module,
    get_module_count,
)
from src.documents.intake_context import get_template_readiness
from src.documents.generator import DOC_TYPE_TO_FRIENDLY

router = APIRouter(prefix="/api/intake", tags=["intake"])


# =============================================================================
# Request / Response models
# =============================================================================

class StartSessionRequest(BaseModel):
    # Client may not override org — authoritative source is the JWT.
    # Field is kept for backward compat but ignored in the handler unless
    # the caller is SUPERADMIN.
    org_id: Optional[str] = None


class AnswerRequest(BaseModel):
    question_id: str
    module_id: int
    control_ids: list[str] = []
    answer_type: str = "yes_no_unsure"
    answer_value: str
    answer_details: Optional[dict] = None


class BatchAnswerRequest(BaseModel):
    answers: list[AnswerRequest]


class CompanyProfileRequest(BaseModel):
    # org_id is filled from the JWT in the handler; retained as an optional
    # field so SUPERADMIN can explicitly target a different org.
    org_id: Optional[str] = None
    company_name: str
    cage_code: Optional[str] = None
    duns_number: Optional[str] = None
    employee_count: Optional[int] = None
    facility_count: Optional[int] = 1
    primary_location: Optional[str] = None
    cui_types: list[str] = []
    cui_flow: Optional[str] = None
    has_remote_workers: bool = False
    has_wireless: bool = False
    identity_provider: Optional[str] = None
    email_platform: Optional[str] = None
    email_tier: Optional[str] = None
    edr_product: Optional[str] = None
    firewall_product: Optional[str] = None
    siem_product: Optional[str] = None
    backup_solution: Optional[str] = None
    existing_ssp: bool = False
    existing_poam: bool = False
    prior_assessment: bool = False
    dfars_7012_clause: bool = False


# =============================================================================
# Helpers
# =============================================================================

_QID_PREFIX_RE = re.compile(r"^m(\d+)_")


def _resolve_org(req_org_id: Optional[str], caller: dict) -> str:
    """Decide which org an intake write targets.

    - Regular users: always their JWT org, request body override is ignored.
    - SUPERADMIN: may override via request body to support admin tooling.
    """
    if req_org_id and is_superadmin(caller):
        return req_org_id
    return caller["org_id"]


def _session_belongs_to(db, session_id: str, caller: dict) -> bool:
    """True iff the session exists AND belongs to caller's org
    (or caller is SUPERADMIN)."""
    row = db.execute(
        text("SELECT org_id FROM intake_sessions WHERE id = :sid"),
        {"sid": session_id},
    ).fetchone()
    if not row:
        return False
    return is_superadmin(caller) or row[0] == caller["org_id"]


def _lookup_tier(question_id: str) -> str:
    """Resolve a question_id to its tier via the module registry.

    Parse the module number from the id prefix ("m0_*", "m1_*", ...),
    look up the module, then find the question. Returns the tier value
    upper-cased to match the DB column's default ('SCREENING').
    Falls back to 'SCREENING' when prefix parsing, module lookup, or
    question lookup fails — safer than leaving the column NULL.
    """
    match = _QID_PREFIX_RE.match(question_id or "")
    if not match:
        return "SCREENING"
    try:
        module_num = int(match.group(1))
    except ValueError:
        return "SCREENING"
    mod = get_module(module_num)
    if mod is None:
        return "SCREENING"
    for q in mod.questions:
        if q.id == question_id:
            return (q.tier or "screening").upper()
    return "SCREENING"


# =============================================================================
# Routes — sessions
# =============================================================================

@router.post("/sessions")
async def start_session(
    req: StartSessionRequest,
    current_user: dict = Depends(get_current_user),
):
    """Start a new intake session. Always scoped to the caller's JWT org
    (SUPERADMIN may override via request body)."""
    org_id = _resolve_org(req.org_id, current_user)
    now = datetime.now(timezone.utc)
    session_id = hashlib.sha256(
        f"{org_id}:{now.isoformat()}".encode()
    ).hexdigest()[:20]

    with get_session() as db:
        db.execute(text("""
            INSERT INTO intake_sessions (id, org_id, started_at, updated_at, current_module, status)
            VALUES (:id, :org_id, :now, :now, 0, 'in_progress')
            ON CONFLICT (id) DO NOTHING
        """), {"id": session_id, "org_id": org_id, "now": now.isoformat()})
        db.commit()

    return {"session_id": session_id, "org_id": org_id, "current_module": 0}


@router.get("/sessions/{session_id}")
async def get_session_status(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get session progress. 404 if session is not in caller's org."""
    with get_session() as db:
        if not _session_belongs_to(db, session_id, current_user):
            raise HTTPException(404, "Session not found")
        row = db.execute(text("""
            SELECT id, org_id, current_module, status, modules_completed,
                   total_questions, answered_questions, gap_count, estimated_sprs,
                   started_at, updated_at
            FROM intake_sessions WHERE id = :id
        """), {"id": session_id}).fetchone()

    if not row:
        raise HTTPException(404, "Session not found")

    return {
        "session_id": row[0],
        "org_id": row[1],
        "current_module": row[2],
        "status": row[3],
        "modules_completed": row[4],
        "progress": {
            "total_questions": row[5],
            "answered_questions": row[6],
            "gap_count": row[7],
            "estimated_sprs": row[8],
        },
        "started_at": row[9],
        "updated_at": row[10],
    }


@router.get("/sessions/{session_id}/progress")
async def get_session_progress(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Per-module progress + doc readiness + outdated-doc detection.

    Readiness is org-scoped (not session-scoped): templates apply to the
    whole organization, and the frontend mainly cares whether doc
    generation will produce fresh output. "outdated" means a doc exists
    but its updated_at predates the most recent intake response for the
    org — i.e. regenerating now would yield different content.
    """
    modules_stats = []
    overall_total = 0
    overall_answered = 0

    with get_session() as db:
        # Resolve the session's org so we can attach org-scoped readiness.
        session_row = db.execute(
            text("SELECT org_id FROM intake_sessions WHERE id = :sid"),
            {"sid": session_id},
        ).fetchone()
        if not session_row:
            raise HTTPException(404, "Session not found")
        if session_row[0] != current_user["org_id"] and not is_superadmin(current_user):
            raise HTTPException(404, "Session not found")
        org_id = session_row[0]

        for mod in get_all_modules():
            q_ids = [q.id for q in mod.questions]
            total = len(q_ids)
            if total == 0:
                answered = 0
            else:
                stmt = text("""
                    SELECT COUNT(DISTINCT question_id)
                    FROM intake_responses
                    WHERE session_id = :sid AND question_id IN :qids
                """).bindparams(bindparam("qids", expanding=True))
                answered = db.execute(stmt, {"sid": session_id, "qids": q_ids}).scalar() or 0

            overall_total += total
            overall_answered += answered
            pct = round(100.0 * answered / total, 1) if total else 0.0
            if answered == 0:
                status_val = "empty"
            elif answered >= total:
                status_val = "complete"
            else:
                status_val = "in_progress"

            modules_stats.append({
                "module_number": mod.number,
                "name": mod.name,
                "total_questions": total,
                "answered": answered,
                "completion_pct": pct,
                "status": status_val,
                "doc_templates": list(mod.doc_templates),
            })

        overall_pct = round(100.0 * overall_answered / overall_total, 1) if overall_total else 0.0

        # Doc readiness — only if we could resolve an org.
        doc_readiness: dict = {}
        docs_ready_count = 0
        docs_total = 0

        if org_id:
            readiness_payload = get_template_readiness(org_id, db)
            readiness = readiness_payload.get("templates", {})
            docs_total = len(readiness)

            # Latest answered_at across all sessions for this org.
            max_resp_row = db.execute(text("""
                SELECT MAX(ir.answered_at)
                FROM intake_responses ir
                JOIN intake_sessions  s ON s.id = ir.session_id
                WHERE s.org_id = :org_id
            """), {"org_id": org_id}).fetchone()
            max_response_at = max_resp_row[0] if max_resp_row else None

            # Latest updated_at per doc_type for this org.
            doc_rows = db.execute(text("""
                SELECT doc_type, MAX(updated_at)
                FROM generated_documents
                WHERE org_id = :org_id
                GROUP BY doc_type
            """), {"org_id": org_id}).fetchall()
            last_gen_by_doc_type = {row[0]: row[1] for row in doc_rows}

            # Bridge friendly keys (intake_context) ↔ DB doc_types (generator).
            friendly_to_doc_type = {v: k for k, v in DOC_TYPE_TO_FRIENDLY.items()}

            for friendly, info in readiness.items():
                doc_type = friendly_to_doc_type.get(friendly)
                last_dt = last_gen_by_doc_type.get(doc_type) if doc_type else None
                last_generated = last_dt.isoformat() if last_dt else None
                outdated = bool(last_dt and max_response_at and max_response_at > last_dt)
                doc_readiness[friendly] = {
                    **info,
                    "outdated":       outdated,
                    "last_generated": last_generated,
                }
                if info.get("ready"):
                    docs_ready_count += 1

    return {
        "session_id": session_id,
        "modules": modules_stats,
        "overall": {
            "total_questions": overall_total,
            "answered": overall_answered,
            "completion_pct": overall_pct,
        },
        "doc_readiness":    doc_readiness,
        "docs_ready_count": docs_ready_count,
        "docs_total":       docs_total,
    }


@router.get("/sessions/{session_id}/module/{module_number}")
async def get_module_questions(
    session_id: str,
    module_number: int,
    current_user: dict = Depends(get_current_user),
):
    """Get questions for a module, each annotated with the session's saved answer."""
    with get_session() as _db_check:
        if not _session_belongs_to(_db_check, session_id, current_user):
            raise HTTPException(404, "Session not found")
    mod = get_module(module_number)
    if mod is None:
        return {
            "module_number": module_number,
            "name": f"Module {module_number}",
            "status": "not_available",
            "message": "This module is not yet implemented.",
            "questions": [],
        }

    q_ids = [q.id for q in mod.questions]
    existing: dict = {}
    if q_ids:
        stmt = text("""
            SELECT question_id, answer_value, answer_details
            FROM intake_responses
            WHERE session_id = :sid AND question_id IN :qids
        """).bindparams(bindparam("qids", expanding=True))
        with get_session() as db:
            rows = db.execute(stmt, {"sid": session_id, "qids": q_ids}).fetchall()
            for r in rows:
                existing[r[0]] = {"answer_value": r[1], "answer_details": r[2]}

    questions = []
    for q in mod.questions:
        d = q.to_dict()
        if q.id in existing:
            d["current_value"] = existing[q.id]["answer_value"]
            d["current_details"] = existing[q.id]["answer_details"]
        else:
            d["current_value"] = None
            d["current_details"] = None
        questions.append(d)

    payload = mod.to_full()
    payload["questions"] = questions
    payload["answered_count"] = len(existing)
    payload["module_id"] = mod.number  # legacy alias for frontend callers
    return payload


# =============================================================================
# Routes — responses
# =============================================================================

@router.post("/sessions/{session_id}/responses")
async def save_responses(
    session_id: str,
    req: BatchAnswerRequest,
    current_user: dict = Depends(get_current_user),
):
    """Save one or more questionnaire answers."""
    now = datetime.now(timezone.utc)
    saved = 0
    flags = []

    with get_session() as db:
        session_row = db.execute(text(
            "SELECT org_id FROM intake_sessions WHERE id = :id"
        ), {"id": session_id}).fetchone()
        if not session_row:
            raise HTTPException(404, "Session not found")
        if session_row[0] != current_user["org_id"] and not is_superadmin(current_user):
            raise HTTPException(404, "Session not found")

        org_id = session_row[0]

        for answer in req.answers:
            answer_id = hashlib.sha256(
                f"{session_id}:{answer.question_id}".encode()
            ).hexdigest()[:20]

            creates_gap = False
            gap_severity = None
            q_obj = find_question(answer.question_id)
            question_def = q_obj.to_dict() if q_obj else None

            # Module 0 style: branch -> flag/message
            # Module 1 style: branching -> alert (string message)
            branching = None
            if question_def:
                branching = question_def.get("branch") or question_def.get("branching")
            if branching:
                branch = branching.get(answer.answer_value, {}) or {}
                if branch.get("flag") in ("critical", "high"):
                    creates_gap = True
                    gap_severity = branch["flag"].upper()
                    flags.append({
                        "question_id": answer.question_id,
                        "severity": branch["flag"],
                        "message": branch.get("message", ""),
                    })
                elif branch.get("alert"):
                    creates_gap = True
                    gap_severity = "CRITICAL"
                    flags.append({
                        "question_id": answer.question_id,
                        "severity": "critical",
                        "message": branch["alert"],
                    })

            # Module 1 style: option-level gap + severity
            if question_def and not creates_gap:
                for opt in question_def.get("options") or []:
                    if isinstance(opt, dict) and opt.get("value") == answer.answer_value:
                        if opt.get("gap") and opt.get("severity"):
                            creates_gap = True
                            gap_severity = opt["severity"].upper()
                            flags.append({
                                "question_id": answer.question_id,
                                "severity": opt["severity"].lower(),
                                "message": f"Gap identified: {opt.get('label', answer.answer_value)} ({opt['severity']})",
                            })
                        break

            question_tier = _lookup_tier(answer.question_id)

            db.execute(text("""
                INSERT INTO intake_responses
                    (id, session_id, org_id, module_id, question_id, control_ids,
                     answer_type, answer_value, answer_details,
                     creates_gap, gap_severity, question_tier, answered_at)
                VALUES
                    (:id, :sid, :org_id, :mid, :qid, CAST(:cids AS json),
                     :atype, :aval, CAST(:adetails AS json),
                     :gap, :gsev, :tier, :now)
                ON CONFLICT (session_id, question_id) DO UPDATE SET
                    answer_value = :aval,
                    answer_details = CAST(:adetails AS json),
                    creates_gap = :gap,
                    gap_severity = :gsev,
                    question_tier = :tier,
                    answered_at = :now
            """), {
                "id": answer_id,
                "sid": session_id,
                "org_id": org_id,
                "mid": answer.module_id,
                "qid": answer.question_id,
                "cids": json.dumps(answer.control_ids),
                "atype": answer.answer_type,
                "aval": answer.answer_value,
                "adetails": json.dumps(answer.answer_details) if answer.answer_details else "{}",
                "gap": creates_gap,
                "gsev": gap_severity,
                "tier": question_tier,
                "now": now.isoformat(),
            })
            saved += 1

        counts = db.execute(text("""
            SELECT
                COUNT(*),
                SUM(CASE WHEN creates_gap THEN 1 ELSE 0 END)
            FROM intake_responses WHERE session_id = :sid
        """), {"sid": session_id}).fetchone()

        db.execute(text("""
            UPDATE intake_sessions SET
                answered_questions = :answered,
                gap_count = :gaps,
                updated_at = :now
            WHERE id = :sid
        """), {
            "answered": counts[0],
            "gaps": counts[1] or 0,
            "now": now.isoformat(),
            "sid": session_id,
        })

        db.commit()

    return {
        "saved": saved,
        "flags": flags,
        "progress": {
            "answered": counts[0],
            "gaps": counts[1] or 0,
        },
    }


# =============================================================================
# Routes — company profile
# =============================================================================

@router.post("/company-profile")
async def save_company_profile(
    req: CompanyProfileRequest,
    current_user: dict = Depends(get_current_user),
):
    """Save or update the company profile (Module 0 structured output).

    org_id is resolved from the caller's JWT; SUPERADMIN may target another
    org by including ``org_id`` in the request body.
    """
    org_id = _resolve_org(req.org_id, current_user)
    now = datetime.now(timezone.utc)
    profile_id = hashlib.sha256(
        f"profile:{org_id}".encode()
    ).hexdigest()[:20]

    with get_session() as db:
        db.execute(text("""
            INSERT INTO company_profiles
                (id, org_id, company_name, cage_code, duns_number,
                 employee_count, facility_count, primary_location,
                 cui_types, cui_flow, has_remote_workers, has_wireless,
                 identity_provider, email_platform, email_tier,
                 edr_product, firewall_product, siem_product, backup_solution,
                 existing_ssp, existing_poam, prior_assessment, dfars_7012_clause,
                 created_at, updated_at)
            VALUES
                (:id, :org_id, :name, :cage, :duns,
                 :emp, :fac, :loc,
                 CAST(:cui_types AS json), :cui_flow, :remote, :wireless,
                 :idp, :email, :email_tier,
                 :edr, :fw, :siem, :backup,
                 :ssp, :poam, :prior, :dfars,
                 :now, :now)
            ON CONFLICT (org_id) DO UPDATE SET
                company_name = :name, cage_code = :cage, employee_count = :emp,
                facility_count = :fac, primary_location = :loc,
                cui_types = CAST(:cui_types AS json), cui_flow = :cui_flow,
                has_remote_workers = :remote, has_wireless = :wireless,
                identity_provider = :idp, email_platform = :email, email_tier = :email_tier,
                edr_product = :edr, firewall_product = :fw, siem_product = :siem,
                backup_solution = :backup,
                existing_ssp = :ssp, existing_poam = :poam,
                prior_assessment = :prior, dfars_7012_clause = :dfars,
                updated_at = :now
        """), {
            "id": profile_id, "org_id": org_id,
            "name": req.company_name, "cage": req.cage_code, "duns": req.duns_number,
            "emp": req.employee_count, "fac": req.facility_count, "loc": req.primary_location,
            "cui_types": json.dumps(req.cui_types), "cui_flow": req.cui_flow,
            "remote": req.has_remote_workers, "wireless": req.has_wireless,
            "idp": req.identity_provider, "email": req.email_platform,
            "email_tier": req.email_tier,
            "edr": req.edr_product, "fw": req.firewall_product,
            "siem": req.siem_product, "backup": req.backup_solution,
            "ssp": req.existing_ssp, "poam": req.existing_poam,
            "prior": req.prior_assessment, "dfars": req.dfars_7012_clause,
            "now": now.isoformat(),
        })
        db.commit()

    return {"profile_id": profile_id, "org_id": org_id, "status": "saved"}


@router.get("/company-profile/{org_id}")
async def get_company_profile(
    org_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get the saved company profile. Path org_id must match the caller's
    JWT org (or caller must be SUPERADMIN) — prevents scanning profiles."""
    if org_id != current_user["org_id"] and not is_superadmin(current_user):
        raise HTTPException(404, "Company profile not found")
    with get_session() as db:
        row = db.execute(text("""
            SELECT * FROM company_profiles WHERE org_id = :org_id
        """), {"org_id": org_id}).fetchone()

    if not row:
        raise HTTPException(404, "Company profile not found")

    columns = [
        "id", "org_id", "session_id",
        "company_name", "cage_code", "duns_number",
        "employee_count", "facility_count", "primary_location",
        "cui_types", "cui_flow", "has_remote_workers", "has_wireless",
        "identity_provider", "email_platform", "email_tier",
        "edr_product", "firewall_product", "siem_product", "backup_solution",
        "existing_ssp", "existing_poam", "prior_assessment", "dfars_7012_clause",
        "created_at", "updated_at",
    ]
    return dict(zip(columns, row))


# =============================================================================
# Routes — module registry
# =============================================================================

@router.get("/modules")
async def list_modules():
    """List all registered intake modules (summary only)."""
    mods = get_all_modules()
    return {
        "modules": [m.to_summary() for m in mods],
        "total_modules": get_module_count(),
    }


@router.get("/modules/{module_number}")
async def get_module_full(module_number: int):
    """Full module definition including every question."""
    mod = get_module(module_number)
    if mod is None:
        raise HTTPException(404, f"Module {module_number} not registered")
    return mod.to_full()
