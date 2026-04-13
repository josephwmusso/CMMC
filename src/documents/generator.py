"""
src/documents/generator.py
Document generation pipeline.

Usage:
    from src.documents.generator import DocumentGenerator
    gen = DocumentGenerator()
    result = gen.generate_document("incident_response_plan")
    # result = {"doc_id": "...", "title": "...", "sections": [...], "word_count": N}
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text

from src.agents.llm_client import get_llm
from src.agents.ssp_prompts_v2 import DEMO_ORG_PROFILE, format_org_context
from src.db.session import get_session

ORG_ID = "9de53b587b23450b87af"


# =============================================================================
# Boilerplate content for common sections
# =============================================================================

BOILERPLATE = {
    "policy_statement": (
        "{company_name} is committed to protecting Controlled Unclassified Information (CUI) "
        "in accordance with NIST SP 800-171 Rev 2, DFARS 252.204-7012, and the Cybersecurity "
        "Maturity Model Certification (CMMC) Level 2 requirements. This policy establishes the "
        "security controls, procedures, and responsibilities necessary to safeguard CUI throughout "
        "its lifecycle within {company_name}'s information systems and operating environment."
    ),
    "enforcement": (
        "Violations of this policy may result in disciplinary action up to and including termination "
        "of employment or contract. All personnel are required to report suspected violations to the "
        "Information System Security Officer (ISSO) or management. Exceptions to this policy must be "
        "documented, risk-assessed, approved by the System Owner, and reviewed annually."
    ),
    "review_cycle": (
        "This document is reviewed and updated at least annually, or whenever significant changes occur "
        "to the information system, operating environment, or regulatory requirements. The document owner "
        "is responsible for initiating the review cycle and obtaining re-approval."
    ),
    "incident_types": (
        "This plan addresses the following incident categories:\n\n"
        "- Unauthorized access to CUI or CUI-scoped systems\n"
        "- Malware or ransomware infection on endpoints or servers within the CUI enclave\n"
        "- Data exfiltration or suspected data loss involving CUI\n"
        "- Insider threat indicators (unauthorized data transfers, policy violations)\n"
        "- Denial of service affecting CUI system availability\n"
        "- Physical security breach affecting areas where CUI is processed or stored\n"
        "- Supply chain compromise affecting CUI-scoped software or services\n"
        "- Loss or theft of devices containing CUI"
    ),
    "triage": (
        "Upon detection, the incident handler performs initial triage:\n\n"
        "Severity 1 (Critical): Active data exfiltration, ransomware execution, or confirmed CUI compromise. "
        "Response within 1 hour. Escalate to ISSO and System Owner immediately.\n\n"
        "Severity 2 (High): Suspected unauthorized access, malware detection on CUI systems, or failed "
        "containment of a lower-severity incident. Response within 4 hours.\n\n"
        "Severity 3 (Medium): Policy violations, suspicious activity without confirmed compromise, or "
        "vulnerability exploitation attempts. Response within 24 hours.\n\n"
        "Severity 4 (Low): Informational alerts, failed login attempts below threshold, or minor policy "
        "deviations. Response within 72 hours."
    ),
    "external_reporting": (
        "Per DFARS 252.204-7012, {company_name} must report cyber incidents that affect covered defense "
        "information to the DoD within 72 hours of discovery via https://dibnet.dod.mil. The report must "
        "include the information required by the clause. {company_name} will preserve and protect images "
        "of affected systems and relevant monitoring data for at least 90 days following the report.\n\n"
        "The ISSO is responsible for determining reportability and coordinating the submission."
    ),
    "exercises": (
        "{company_name} conducts incident response exercises at least annually:\n\n"
        "- Tabletop exercise: Annual, scenario-based discussion exercise involving key IR personnel. "
        "Scenarios rotate through the incident types listed in this plan.\n"
        "- After-action report: Documented within 14 days of each exercise, identifying lessons learned "
        "and improvements to be incorporated into this plan.\n"
        "- Plan update: This IR plan is updated based on exercise findings and any actual incidents."
    ),
    "training_ir": (
        "All personnel with incident response roles receive IR-specific training within 30 days of "
        "assignment and annually thereafter. Training covers this plan, reporting procedures, evidence "
        "preservation requirements, and their specific role responsibilities."
    ),
    "recordkeeping": (
        "All incident records, exercise reports, after-action reports, and IR plan versions are retained "
        "for a minimum of six years in accordance with CMMC evidence retention requirements. Records are "
        "stored in the compliance platform with SHA-256 integrity hashing."
    ),
    "asset_categories": (
        "Assets within the CMMC Assessment Scope are categorized per the DoD CIO Level 2 Scoping Guide "
        "into five categories:\n\n"
        "1. CUI Assets: Systems that process, store, or transmit CUI\n"
        "2. Security Protection Assets: Systems that provide security functions for CUI assets "
        "(firewalls, SIEM, EDR, identity providers)\n"
        "3. Contractor Risk Managed Assets (CRMAs): Assets that can but do not process CUI, where the "
        "contractor determines risk is acceptable\n"
        "4. Specialized Assets: IoT devices, OT systems, test equipment, or government-provided equipment\n"
        "5. Out-of-Scope Assets: Systems completely isolated from CUI processing"
    ),
    "risk_methodology": (
        "Risk is assessed using a likelihood x impact matrix:\n\n"
        "Likelihood: 1 (Rare) / 2 (Unlikely) / 3 (Possible) / 4 (Likely) / 5 (Almost Certain)\n"
        "Impact: 1 (Negligible) / 2 (Minor) / 3 (Moderate) / 4 (Major) / 5 (Severe)\n\n"
        "Risk Score = Likelihood x Impact. Scores 1-6: Low (accept). 7-14: Medium (mitigate within "
        "90 days). 15-25: High/Critical (mitigate within 30 days or escalate).\n\n"
        "Risk acceptance requires documented approval by the System Owner."
    ),
    "patch_sla": (
        "Patch management follows severity-based SLAs:\n\n"
        "- Critical (CVSS 9.0+): Apply within 14 days of release\n"
        "- High (CVSS 7.0-8.9): Apply within 30 days\n"
        "- Medium (CVSS 4.0-6.9): Apply within 60 days\n"
        "- Low (CVSS < 4.0): Apply within 90 days or next maintenance window\n\n"
        "Exceptions require documented risk acceptance and inclusion in the risk register."
    ),
    "config_auditing": (
        "Configuration compliance is audited at least quarterly using automated scanning tools. "
        "Results are compared against the baseline configuration standard. Deviations are documented, "
        "risk-assessed, and either remediated or added to the risk register with documented acceptance.\n\n"
        "Audit results are retained as evidence artifacts in the compliance platform."
    ),
    "records": (
        "Configuration management records — including baselines, change requests, approvals, "
        "implementation records, and audit results — are retained for a minimum of six years in "
        "accordance with CMMC evidence retention requirements."
    ),
    "insider_threat": (
        "All personnel receive insider threat awareness training as part of the annual security "
        "awareness program. Training covers: recognizing indicators of insider threat behavior, "
        "reporting channels and procedures, handling of sensitive information, and consequences "
        "of policy violations. Refresher training is provided when threat indicators are elevated."
    ),
}


# =============================================================================
# LLM prompts for narrative sections
# =============================================================================

DOC_SECTION_SYSTEM_PROMPT = """You are a CMMC compliance documentation expert writing sections of
compliance documents for defense contractors. Write professional, assessor-grade content that:

1. References the organization's ACTUAL tools and systems by name (from the org context provided)
2. Is specific enough that a C3PAO assessor would accept it as evidence
3. Uses clear, direct language — not vague or aspirational
4. Includes specific procedures, frequencies, and responsible roles where applicable
5. Does NOT fabricate any technical details not present in the provided context

Write in third person referring to the organization by name. Output ONLY the section content
as prose paragraphs. Do not include the section heading — that's added separately.
Do not include markdown formatting. Just clean prose."""

DOC_SECTION_USER_PROMPT = """Write the "{section_title}" section for {company_name}'s {document_title}.

ORGANIZATION CONTEXT:
{org_context}

INTAKE ANSWERS RELEVANT TO THIS SECTION:
{intake_context}

CONTROLS THIS SECTION ADDRESSES:
{controls_context}

SECTION PURPOSE:
This section should describe how {company_name} implements the requirements related to
{section_title}. Be specific about tools, configurations, procedures, and responsibilities.
Write 2-4 paragraphs of assessor-grade content."""


class DocumentGenerator:
    """Generates compliance documents from templates + intake answers + LLM."""

    def __init__(self, org_id: str = ORG_ID, org_profile: dict = None):
        self.org_id = org_id
        self.org_profile = org_profile or DEMO_ORG_PROFILE
        self.llm = get_llm()

    def get_template(self, doc_type: str) -> dict:
        """Load a document template from the database."""
        with get_session() as session:
            row = session.execute(text("""
                SELECT id, doc_type, title, description, sections, control_ids,
                       conditional_on, conditional_values, estimated_pages
                FROM document_templates WHERE doc_type = :dt
            """), {"dt": doc_type}).fetchone()

        if not row:
            raise ValueError(f"Template not found: {doc_type}")

        sections = row[4] if isinstance(row[4], list) else json.loads(row[4])

        return {
            "id": row[0],
            "doc_type": row[1],
            "title": row[2],
            "description": row[3],
            "sections": sections,
            "control_ids": row[5] if isinstance(row[5], list) else json.loads(row[5] or "[]"),
            "conditional_on": row[6],
            "conditional_values": row[7] if isinstance(row[7], list) else json.loads(row[7] or "[]"),
            "estimated_pages": row[8],
        }

    def get_intake_answers(self) -> dict:
        """Fetch all intake answers for this org, keyed by question_id."""
        with get_session() as session:
            rows = session.execute(text("""
                SELECT question_id, answer_value
                FROM intake_responses ir
                JOIN intake_sessions s ON s.id = ir.session_id
                WHERE s.org_id = :org_id
                ORDER BY ir.answered_at DESC
            """), {"org_id": self.org_id}).fetchall()

        answers = {}
        for row in rows:
            if row[0] not in answers:
                answers[row[0]] = row[1]
        return answers

    def get_company_profile(self) -> dict:
        """Fetch company profile for this org."""
        with get_session() as session:
            row = session.execute(text("""
                SELECT company_name, employee_count, primary_location,
                       identity_provider, email_platform, edr_product,
                       firewall_product, siem_product, cui_types, cui_flow
                FROM company_profiles WHERE org_id = :org_id
            """), {"org_id": self.org_id}).fetchone()

        if not row:
            return {}

        return {
            "company_name": row[0],
            "employee_count": row[1],
            "primary_location": row[2],
            "identity_provider": row[3],
            "email_platform": row[4],
            "edr_product": row[5],
            "firewall_product": row[6],
            "siem_product": row[7],
            "cui_types": row[8],
            "cui_flow": row[9],
        }

    def build_intake_context(self, intake_fields: list[str], answers: dict) -> str:
        """Build a text summary of relevant intake answers for a section."""
        lines = []
        for field_id in intake_fields:
            val = answers.get(field_id)
            if val:
                clean_id = field_id.replace("m0_", "").replace("_", " ").title()
                lines.append(f"- {clean_id}: {val}")
        return "\n".join(lines) if lines else "No specific intake answers for this section."

    def generate_section_content(
        self,
        section: dict,
        template: dict,
        answers: dict,
        company_name: str,
    ) -> str:
        """Generate content for a single section based on its type."""
        section_type = section.get("type", "boilerplate")
        section_id = section.get("id", "")
        section_title = section.get("title", "Untitled")

        # --- Boilerplate ---
        if section_type == "boilerplate":
            content = BOILERPLATE.get(section_id, "")
            return content.format(company_name=company_name) if content else f"[Content for {section_title} to be completed.]"

        # --- Variable (intake-populated) ---
        if section_type == "variable":
            intake_fields = section.get("intake_fields", [])
            parts = []
            for field_id in intake_fields:
                val = answers.get(field_id)
                if val:
                    clean_id = field_id.replace("m0_", "").replace("_", " ").title()
                    parts.append(f"{clean_id}: {val}")
            if parts:
                return f"The following information applies to {company_name}:\n\n" + "\n".join(f"- {p}" for p in parts)
            return f"[Information for {section_title} to be completed during intake.]"

        # --- AI Narrative ---
        if section_type in ("ai_narrative", "mixed"):
            intake_fields = section.get("intake_fields", [])
            intake_context = self.build_intake_context(intake_fields, answers)
            control_ids = section.get("control_ids", [])
            controls_text = ", ".join(control_ids) if control_ids else "General organizational policy"

            user_prompt = DOC_SECTION_USER_PROMPT.format(
                section_title=section_title,
                company_name=company_name,
                document_title=template["title"],
                org_context=format_org_context(self.org_profile),
                intake_context=intake_context,
                controls_context=controls_text,
            )

            try:
                content = self.llm.generate(
                    system_prompt=DOC_SECTION_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    max_tokens=2048,
                )
                return content.strip()
            except Exception as e:
                print(f"  LLM error for {section_title}: {e}")
                return f"[AI generation failed for {section_title}. Error: {e}]"

        return f"[Unknown section type: {section_type}]"

    def generate_document(self, doc_type: str) -> dict:
        """
        Generate a complete document.

        Returns dict with: doc_id, title, doc_type, sections (with content), word_count
        """
        template = self.get_template(doc_type)
        answers = self.get_intake_answers()
        profile = self.get_company_profile()
        company_name = profile.get("company_name") or self.org_profile.get("name", "Organization")

        # Merge profile answers into the answers dict for lookup
        profile_to_answer = {
            "m0_company_name": profile.get("company_name", ""),
            "m0_employee_count": str(profile.get("employee_count", "")),
            "m0_primary_location": profile.get("primary_location", ""),
            "m0_identity_provider": profile.get("identity_provider", ""),
            "m0_email_platform": profile.get("email_platform", ""),
            "m0_edr": profile.get("edr_product", ""),
            "m0_firewall": profile.get("firewall_product", ""),
            "m0_siem": profile.get("siem_product", ""),
            "m0_cui_types": str(profile.get("cui_types", "")),
            "m0_cui_flow": profile.get("cui_flow", ""),
        }
        for k, v in profile_to_answer.items():
            if v and k not in answers:
                answers[k] = v

        print(f"\nGenerating: {template['title']}")
        print(f"  Company: {company_name}")
        print(f"  Sections: {len(template['sections'])}")

        generated_sections = []
        total_words = 0

        for section in template["sections"]:
            section_title = section.get("title", "Untitled")
            print(f"  [{section.get('type', '?')}] {section_title}...", end=" ", flush=True)

            content = self.generate_section_content(section, template, answers, company_name)
            word_count = len(content.split())
            total_words += word_count

            generated_sections.append({
                "id": section["id"],
                "title": section_title,
                "type": section.get("type", "boilerplate"),
                "content": content,
                "word_count": word_count,
            })

            # Handle subsections
            for subsec in section.get("subsections", []):
                sub_content = self.generate_section_content(subsec, template, answers, company_name)
                sub_words = len(sub_content.split())
                total_words += sub_words
                generated_sections.append({
                    "id": subsec["id"],
                    "title": subsec.get("title", ""),
                    "type": subsec.get("type", "boilerplate"),
                    "content": sub_content,
                    "word_count": sub_words,
                    "parent_id": section["id"],
                })

            print(f"{word_count} words")

        # Persist to generated_documents
        now = datetime.now(timezone.utc)
        doc_id = hashlib.sha256(
            f"doc:{self.org_id}:{doc_type}:{now.isoformat()}".encode()
        ).hexdigest()[:20]

        with get_session() as session:
            # RETURNING id ensures we get the PERSISTED row's id, not the
            # freshly-computed one — when ON CONFLICT triggers, the DB keeps
            # the original id and we must honour it for downstream UPDATEs
            # (e.g. file_content blob write in document_routes.py).
            row = session.execute(text("""
                INSERT INTO generated_documents
                    (id, org_id, template_id, doc_type, title, version, status,
                     sections_data, word_count, generated_by, created_at, updated_at)
                VALUES
                    (:id, :org_id, :tmpl_id, :doc_type, :title, 1, 'draft',
                     CAST(:sections AS json), :words, 'document_engine',
                     :now, :now)
                ON CONFLICT (org_id, doc_type, version) DO UPDATE SET
                    sections_data = CAST(:sections AS json),
                    word_count = :words,
                    updated_at = :now
                RETURNING id
            """), {
                "id": doc_id,
                "org_id": self.org_id,
                "tmpl_id": template["id"],
                "doc_type": doc_type,
                "title": template["title"],
                "sections": json.dumps(generated_sections),
                "words": total_words,
                "now": now.isoformat(),
            }).fetchone()
            session.commit()
            if row:
                doc_id = row[0]

        print(f"\n  Total: {total_words} words, saved as {doc_id}")

        return {
            "doc_id": doc_id,
            "title": template["title"],
            "doc_type": doc_type,
            "sections": generated_sections,
            "word_count": total_words,
        }

    def create_evidence_artifact(self, doc_id: str, doc_type: str, title: str, file_path: str, control_ids: list[str]) -> str:
        """
        Create an evidence_artifacts entry for a generated document.
        Returns the evidence artifact ID.
        """
        now = datetime.now(timezone.utc)
        artifact_id = hashlib.sha256(f"evidence:{doc_id}".encode()).hexdigest()[:20]

        import os
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        with get_session() as session:
            session.execute(text("""
                INSERT INTO evidence_artifacts
                    (id, org_id, filename, file_path, evidence_type, source_system,
                     description, state, file_size_bytes, owner, created_at, updated_at)
                VALUES
                    (:id, :org_id, :filename, :file_path, 'Policy', 'document_engine',
                     :desc, 'DRAFT', :size, 'system', :now, :now)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": artifact_id,
                "org_id": self.org_id,
                "filename": os.path.basename(file_path),
                "file_path": file_path,
                "desc": f"AI-generated {title} — requires human review before publishing",
                "size": file_size,
                "now": now.isoformat(),
            })

            # Link to controls
            for cid in control_ids:
                link_id = hashlib.sha256(f"link:{artifact_id}:{cid}".encode()).hexdigest()[:20]
                session.execute(text("""
                    INSERT INTO evidence_control_map (id, evidence_id, control_id, mapped_by)
                    VALUES (:id, :eid, :cid, 'document_engine')
                    ON CONFLICT (id) DO NOTHING
                """), {"id": link_id, "eid": artifact_id, "cid": cid})

            # Update generated_documents with artifact link
            session.execute(text("""
                UPDATE generated_documents SET evidence_artifact_id = :aid WHERE id = :did
            """), {"aid": artifact_id, "did": doc_id})

            session.commit()

        return artifact_id
