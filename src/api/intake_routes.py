"""
src/api/intake_routes.py
FastAPI routes for the guided intake questionnaire.

Endpoints:
  POST   /api/intake/sessions              — Start a new intake session
  GET    /api/intake/sessions/{id}          — Get session status + progress
  GET    /api/intake/sessions/{id}/module/{n} — Get questions for module N
  POST   /api/intake/sessions/{id}/responses — Save answer(s)
  GET    /api/intake/sessions/{id}/summary  — Completion summary + gaps

  POST   /api/intake/company-profile       — Save Module 0 company profile
  GET    /api/intake/company-profile/{org_id} — Get saved company profile
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from src.db.session import get_session
from src.api.intake_module1 import MODULE_1_QUESTIONS, MODULE_1_SECTIONS

router = APIRouter(prefix="/api/intake", tags=["intake"])

# Unified question bank — all modules
ALL_QUESTIONS = []  # populated after MODULE_0_QUESTIONS is defined below

ORG_ID = "9de53b587b23450b87af"  # Dev org


# =============================================================================
# Request / Response models
# =============================================================================

class StartSessionRequest(BaseModel):
    org_id: str = ORG_ID


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
    org_id: str = ORG_ID
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
# Module 0 question bank (Company Profile & Scoping)
# =============================================================================

MODULE_0_QUESTIONS = [
    {
        "id": "m0_company_name",
        "text": "What is your company's legal name?",
        "help": "The name as it appears on your government contracts.",
        "answer_type": "text",
        "required": True,
        "section": "Company Information",
    },
    {
        "id": "m0_cage_code",
        "text": "What is your CAGE code?",
        "help": "A 5-character identifier assigned by DLA. You can look it up at sam.gov.",
        "answer_type": "text",
        "required": False,
        "section": "Company Information",
    },
    {
        "id": "m0_employee_count",
        "text": "How many employees does your company have?",
        "help": "Include full-time, part-time, and contractors who access your systems.",
        "answer_type": "number",
        "required": True,
        "section": "Company Information",
    },
    {
        "id": "m0_locations",
        "text": "How many physical locations does your company operate from?",
        "help": "Include offices, labs, manufacturing facilities, and any location where CUI is handled.",
        "answer_type": "number",
        "required": True,
        "section": "Company Information",
    },
    {
        "id": "m0_primary_location",
        "text": "Where is your primary office located?",
        "help": "City and state (e.g., 'Columbia, MD').",
        "answer_type": "text",
        "required": True,
        "section": "Company Information",
    },
    {
        "id": "m0_dfars_clause",
        "text": "Do your contracts include the DFARS 252.204-7012 clause?",
        "help": "This clause requires you to protect Controlled Unclassified Information (CUI). Check your contract or ask your contracting officer.",
        "answer_type": "yes_no_unsure",
        "required": True,
        "section": "Contract & CUI Scoping",
        "branch": {
            "unsure": {"flag": "Verify DFARS clause with contracting officer before proceeding."}
        },
    },
    {
        "id": "m0_cui_types",
        "text": "What types of CUI does your company handle?",
        "help": "Select all that apply. CUI is sensitive government information that isn't classified.",
        "answer_type": "multiple_choice",
        "options": [
            "Technical data (drawings, specs, test results)",
            "ITAR-controlled data",
            "Controlled Technical Information (CTI)",
            "Export-controlled data",
            "Source selection information",
            "Budget/financial data",
            "Personally identifiable information (PII)",
            "I'm not sure what types of CUI we handle",
        ],
        "required": True,
        "section": "Contract & CUI Scoping",
    },
    {
        "id": "m0_cui_flow",
        "text": "How does CUI typically enter and move through your organization?",
        "help": "This determines which systems are 'in scope' for CMMC.",
        "answer_type": "multiple_choice",
        "options": [
            "We receive CUI only via email",
            "CUI is stored on shared network drives",
            "CUI lives in our ERP or database system",
            "CUI is in cloud storage (SharePoint, OneDrive, etc.)",
            "CUI is on individual laptops/desktops",
            "CUI is in a specialized application",
        ],
        "required": True,
        "section": "Contract & CUI Scoping",
    },
    {
        "id": "m0_remote_workers",
        "text": "Do any of your employees work remotely or access company systems from outside the office?",
        "help": "This includes VPN connections, remote desktop, or accessing cloud apps from home.",
        "answer_type": "yes_no_unsure",
        "required": True,
        "section": "Environment Scoping",
        "branch": {
            "no": {"skip": ["AC.L2-3.1.12", "AC.L2-3.1.14", "AC.L2-3.1.15"]},
        },
        "control_ids": ["AC.L2-3.1.12", "AC.L2-3.1.14", "AC.L2-3.1.15"],
    },
    {
        "id": "m0_wireless",
        "text": "Does your office have a wireless (Wi-Fi) network?",
        "help": "Include guest networks and any wireless access points in your facility.",
        "answer_type": "yes_no_unsure",
        "required": True,
        "section": "Environment Scoping",
        "branch": {
            "no": {"skip": ["AC.L2-3.1.16", "AC.L2-3.1.17"]},
        },
        "control_ids": ["AC.L2-3.1.16", "AC.L2-3.1.17"],
    },
    {
        "id": "m0_email_platform",
        "text": "What email system does your company use?",
        "help": "This is one of the most important questions for CMMC scoping.",
        "answer_type": "multiple_choice",
        "options": [
            "Microsoft 365 GCC High",
            "Microsoft 365 GCC",
            "Microsoft 365 (commercial/business)",
            "Google Workspace",
            "On-premises Exchange",
            "Other email provider",
            "I'm not sure",
        ],
        "required": True,
        "section": "Technology Stack",
        "branch": {
            "Microsoft 365 (commercial/business)": {
                "flag": "critical",
                "message": "Your current Microsoft 365 plan does not meet DFARS 7012 requirements for handling CUI. You will need to migrate to GCC High or an equivalent FedRAMP Moderate-authorized service.",
            },
            "Google Workspace": {
                "flag": "critical",
                "message": "Standard Google Workspace is not FedRAMP Moderate authorized for CUI. You will need Google Workspace with Assured Controls or migrate to an authorized platform.",
            },
            "Microsoft 365 GCC High": {
                "generates": "shared_responsibility_matrix",
                "skip_controls": [],
            },
        },
        "control_ids": ["SC.L2-3.13.1", "SC.L2-3.13.8", "SC.L2-3.13.11"],
    },
    {
        "id": "m0_identity_provider",
        "text": "How do your employees log into their computers and applications?",
        "help": "This is your identity/access management system.",
        "answer_type": "multiple_choice",
        "options": [
            "Microsoft Entra ID (Azure AD) with MFA",
            "Microsoft Entra ID (Azure AD) without MFA",
            "On-premises Active Directory with MFA",
            "On-premises Active Directory without MFA",
            "Okta",
            "Google Identity",
            "No centralized login system",
            "I'm not sure",
        ],
        "required": True,
        "section": "Technology Stack",
        "branch": {
            "Microsoft Entra ID (Azure AD) without MFA": {
                "flag": "critical",
                "message": "Multi-factor authentication is required for CMMC Level 2. You must enable MFA before your assessment.",
            },
            "On-premises Active Directory without MFA": {
                "flag": "critical",
                "message": "Multi-factor authentication is required for CMMC Level 2.",
            },
            "No centralized login system": {
                "flag": "critical",
                "message": "CMMC requires centralized account management. You need an identity provider.",
            },
        },
        "control_ids": ["AC.L2-3.1.1", "AC.L2-3.1.2", "IA.L2-3.5.1", "IA.L2-3.5.2", "IA.L2-3.5.3"],
    },
    {
        "id": "m0_edr",
        "text": "What endpoint protection (antivirus/EDR) do you use on your computers?",
        "help": "EDR = Endpoint Detection and Response. This is your anti-malware solution.",
        "answer_type": "multiple_choice",
        "options": [
            "CrowdStrike Falcon",
            "Microsoft Defender for Endpoint",
            "SentinelOne",
            "Carbon Black",
            "Symantec/Broadcom",
            "Traditional antivirus only (e.g., Norton, McAfee)",
            "None / I'm not sure",
        ],
        "required": True,
        "section": "Technology Stack",
        "branch": {
            "None / I'm not sure": {
                "flag": "critical",
                "message": "Endpoint protection is required for CMMC Level 2. This is a critical gap.",
            },
        },
        "control_ids": ["SI.L2-3.14.1", "SI.L2-3.14.2", "SI.L2-3.14.4", "SI.L2-3.14.5"],
    },
    {
        "id": "m0_firewall",
        "text": "What firewall protects your network?",
        "help": "This is the device at the edge of your network that controls traffic.",
        "answer_type": "multiple_choice",
        "options": [
            "Palo Alto Networks",
            "Fortinet FortiGate",
            "Cisco (ASA, Firepower, Meraki)",
            "SonicWall",
            "pfSense / OPNsense",
            "ISP-provided router only",
            "I'm not sure",
        ],
        "required": True,
        "section": "Technology Stack",
        "branch": {
            "ISP-provided router only": {
                "flag": "high",
                "message": "An ISP router alone is unlikely to meet CMMC boundary protection requirements. A commercial firewall is strongly recommended.",
            },
        },
        "control_ids": ["SC.L2-3.13.1", "SC.L2-3.13.5", "SC.L2-3.13.6"],
    },
    {
        "id": "m0_siem",
        "text": "Do you have a system that collects and monitors security logs?",
        "help": "This is called a SIEM (Security Information and Event Management). It's where your audit logs go.",
        "answer_type": "multiple_choice",
        "options": [
            "Microsoft Sentinel",
            "Splunk",
            "Elastic SIEM",
            "Arctic Wolf / Blumira / other managed",
            "We collect logs but don't have a SIEM",
            "No log collection",
            "I'm not sure",
        ],
        "required": True,
        "section": "Technology Stack",
        "control_ids": ["AU.L2-3.3.1", "AU.L2-3.3.2", "AU.L2-3.3.5", "SI.L2-3.14.6", "SI.L2-3.14.7"],
    },
    {
        "id": "m0_existing_docs",
        "text": "Which of these documents does your company already have?",
        "help": "Select any that exist, even if they're outdated. We can work with what you have.",
        "answer_type": "multiple_choice",
        "options": [
            "System Security Plan (SSP)",
            "Plan of Action & Milestones (POA&M)",
            "Incident Response Plan",
            "Access Control Policy",
            "Security Awareness Training Program",
            "Configuration Management Plan",
            "Risk Assessment Report",
            "Network Diagram",
            "None of these",
        ],
        "required": True,
        "section": "Existing Compliance",
        "branch": {
            "None of these": {
                "flag": "info",
                "message": "No problem - the platform will help you create all required documentation.",
            },
        },
    },
]

# Build unified question bank
ALL_QUESTIONS.extend(MODULE_0_QUESTIONS)
ALL_QUESTIONS.extend(MODULE_1_QUESTIONS)

MODULE_METADATA = {
    0: {
        "title": "Company Profile & Scoping",
        "description": (
            "Let's start with the basics about your company, your contracts, "
            "and the technology you use. This information drives the entire "
            "assessment - getting it right saves hours later."
        ),
        "estimated_time": "10-15 minutes",
    },
    1: {
        "title": "Access Control (AC)",
        "description": (
            "This module covers all 22 Access Control requirements from NIST 800-171. "
            "Your answers determine how well your organization controls who can access "
            "CUI systems and what they can do once connected."
        ),
        "estimated_time": "15-20 minutes",
    },
}


# =============================================================================
# Routes
# =============================================================================

@router.post("/sessions")
async def start_session(req: StartSessionRequest):
    """Start a new intake session for an organization."""
    now = datetime.now(timezone.utc)
    session_id = hashlib.sha256(
        f"{req.org_id}:{now.isoformat()}".encode()
    ).hexdigest()[:20]

    with get_session() as db:
        db.execute(text("""
            INSERT INTO intake_sessions (id, org_id, started_at, updated_at, current_module, status)
            VALUES (:id, :org_id, :now, :now, 0, 'in_progress')
            ON CONFLICT (id) DO NOTHING
        """), {"id": session_id, "org_id": req.org_id, "now": now.isoformat()})
        db.commit()

    return {"session_id": session_id, "org_id": req.org_id, "current_module": 0}


@router.get("/sessions/{session_id}")
async def get_session_status(session_id: str):
    """Get session progress."""
    with get_session() as db:
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


@router.get("/sessions/{session_id}/module/{module_id}")
async def get_module_questions(session_id: str, module_id: int):
    """Get questions for a specific module, with existing answers filled in."""
    if module_id not in MODULE_METADATA:
        return {
            "module_id": module_id,
            "title": f"Module {module_id}",
            "status": "not_available",
            "message": "This module is not yet implemented.",
            "questions": [],
        }

    meta = MODULE_METADATA[module_id]
    module_questions = [q for q in ALL_QUESTIONS if q.get("module", 0) == module_id]

    # Get existing answers for this module
    with get_session() as db:
        rows = db.execute(text("""
            SELECT question_id, answer_value, answer_details
            FROM intake_responses
            WHERE session_id = :sid AND module_id = :mid
        """), {"sid": session_id, "mid": module_id}).fetchall()

    existing = {}
    for row in rows:
        existing[row[0]] = {
            "answer_value": row[1],
            "answer_details": row[2],
        }

    # Merge questions with existing answers
    questions = []
    for q in module_questions:
        q_copy = dict(q)
        if q["id"] in existing:
            q_copy["current_answer"] = existing[q["id"]]
        questions.append(q_copy)

    return {
        "module_id": module_id,
        "title": meta["title"],
        "description": meta["description"],
        "estimated_time": meta["estimated_time"],
        "question_count": len(module_questions),
        "answered_count": len(existing),
        "questions": questions,
    }


@router.post("/sessions/{session_id}/responses")
async def save_responses(session_id: str, req: BatchAnswerRequest):
    """Save one or more questionnaire answers."""
    now = datetime.now(timezone.utc)
    saved = 0
    flags = []

    with get_session() as db:
        # Verify session exists
        session_row = db.execute(text(
            "SELECT org_id FROM intake_sessions WHERE id = :id"
        ), {"id": session_id}).fetchone()
        if not session_row:
            raise HTTPException(404, "Session not found")

        org_id = session_row[0]

        for answer in req.answers:
            answer_id = hashlib.sha256(
                f"{session_id}:{answer.question_id}".encode()
            ).hexdigest()[:20]

            # Check for branching flags and option-level gaps
            creates_gap = False
            gap_severity = None
            question_def = next(
                (q for q in ALL_QUESTIONS if q["id"] == answer.question_id),
                None
            )

            # Module 0 style: branch -> flag/message
            branching = question_def.get("branch") or question_def.get("branching") if question_def else None
            if branching:
                branch = branching.get(answer.answer_value, {})
                if branch.get("flag") in ("critical", "high"):
                    creates_gap = True
                    gap_severity = branch["flag"].upper()
                    flags.append({
                        "question_id": answer.question_id,
                        "severity": branch["flag"],
                        "message": branch.get("message", ""),
                    })
                # Module 1 style: branching -> alert (string message)
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
                for opt in question_def.get("options", []):
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

            db.execute(text("""
                INSERT INTO intake_responses
                    (id, session_id, org_id, module_id, question_id, control_ids,
                     answer_type, answer_value, answer_details,
                     creates_gap, gap_severity, answered_at)
                VALUES
                    (:id, :sid, :org_id, :mid, :qid, CAST(:cids AS json),
                     :atype, :aval, CAST(:adetails AS json),
                     :gap, :gsev, :now)
                ON CONFLICT (session_id, question_id) DO UPDATE SET
                    answer_value = :aval,
                    answer_details = CAST(:adetails AS json),
                    creates_gap = :gap,
                    gap_severity = :gsev,
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
                "now": now.isoformat(),
            })
            saved += 1

        # Update session progress
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


@router.post("/company-profile")
async def save_company_profile(req: CompanyProfileRequest):
    """Save or update the company profile (Module 0 structured output)."""
    now = datetime.now(timezone.utc)
    profile_id = hashlib.sha256(
        f"profile:{req.org_id}".encode()
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
            "id": profile_id, "org_id": req.org_id,
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

    return {"profile_id": profile_id, "org_id": req.org_id, "status": "saved"}


@router.get("/company-profile/{org_id}")
async def get_company_profile(org_id: str):
    """Get the saved company profile."""
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
