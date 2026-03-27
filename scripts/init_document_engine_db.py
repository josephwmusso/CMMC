"""
scripts/init_document_engine_db.py
Database migration: document generation engine tables.
"""

import sys
import os
import hashlib
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.db.session import get_session


MIGRATION_SQL = """
-- Document templates: blueprints for each document type
CREATE TABLE IF NOT EXISTS document_templates (
    id                  VARCHAR(30) PRIMARY KEY,
    doc_type            VARCHAR(50) NOT NULL UNIQUE,
    title               VARCHAR(200) NOT NULL,
    description         TEXT,
    sections            JSON NOT NULL,
    control_ids         JSON NOT NULL DEFAULT '[]',
    generation_rules    JSON NOT NULL DEFAULT '{}',
    conditional_on      VARCHAR(100),
    conditional_values  JSON DEFAULT '[]',
    min_modules_required JSON DEFAULT '[]',
    estimated_pages     INTEGER,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- Generated documents: instances created from templates for a specific org
CREATE TABLE IF NOT EXISTS generated_documents (
    id                  VARCHAR(30) PRIMARY KEY,
    org_id              VARCHAR(30) NOT NULL REFERENCES organizations(id),
    template_id         VARCHAR(30) NOT NULL REFERENCES document_templates(id),
    doc_type            VARCHAR(50) NOT NULL,
    title               VARCHAR(200) NOT NULL,
    version             INTEGER NOT NULL DEFAULT 1,
    status              VARCHAR(20) NOT NULL DEFAULT 'draft',
    sections_data       JSON NOT NULL DEFAULT '[]',
    file_path           VARCHAR(500),
    word_count          INTEGER,
    generated_by        VARCHAR(50) DEFAULT 'document_engine',
    evidence_artifact_id VARCHAR(30),
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(org_id, doc_type, version)
);

CREATE INDEX IF NOT EXISTS idx_generated_documents_org
    ON generated_documents(org_id);
CREATE INDEX IF NOT EXISTS idx_generated_documents_type
    ON generated_documents(org_id, doc_type);
"""


# =============================================================================
# Seed the 8 document templates
# =============================================================================

DOCUMENT_TEMPLATES = [
    {
        "doc_type": "integrated_security_policy",
        "title": "Information Security Policy & Procedures Manual",
        "description": "Consolidated policy document covering all 14 NIST 800-171 control families. NIST SP 800-171A lists family-specific policies as Examine objects across nearly every family.",
        "sections": [
            {"id": "governance", "title": "Governance", "type": "mixed", "subsections": [
                {"id": "policy_statement", "title": "Policy Statement", "type": "boilerplate"},
                {"id": "scope", "title": "Scope and Applicability", "type": "variable", "intake_fields": ["m0_company_name", "m0_cui_types", "m0_dfars_clause"]},
                {"id": "roles", "title": "Roles and Responsibilities", "type": "variable", "intake_fields": ["m0_employee_count", "m0_company_name"]},
                {"id": "enforcement", "title": "Enforcement and Exceptions", "type": "boilerplate"},
                {"id": "review_cycle", "title": "Document Review Cycle", "type": "boilerplate"},
            ]},
            {"id": "access_control", "title": "Access Control (AC)", "type": "ai_narrative", "family": "AC",
             "control_ids": ["AC.L2-3.1.1","AC.L2-3.1.2","AC.L2-3.1.3","AC.L2-3.1.4","AC.L2-3.1.5","AC.L2-3.1.6","AC.L2-3.1.7","AC.L2-3.1.8","AC.L2-3.1.9","AC.L2-3.1.10","AC.L2-3.1.11","AC.L2-3.1.12","AC.L2-3.1.13","AC.L2-3.1.14","AC.L2-3.1.15","AC.L2-3.1.16","AC.L2-3.1.17","AC.L2-3.1.18","AC.L2-3.1.19","AC.L2-3.1.20","AC.L2-3.1.21","AC.L2-3.1.22"],
             "intake_fields": ["m0_identity_provider", "m0_remote_workers", "m0_wireless"]},
            {"id": "awareness_training", "title": "Awareness and Training (AT) + Personnel Security (PS)", "type": "ai_narrative", "family": "AT+PS",
             "control_ids": ["AT.L2-3.2.1","AT.L2-3.2.2","AT.L2-3.2.3","PS.L2-3.9.1","PS.L2-3.9.2"],
             "intake_fields": []},
            {"id": "audit_accountability", "title": "Audit and Accountability (AU)", "type": "ai_narrative", "family": "AU",
             "control_ids": ["AU.L2-3.3.1","AU.L2-3.3.2","AU.L2-3.3.3","AU.L2-3.3.4","AU.L2-3.3.5","AU.L2-3.3.6","AU.L2-3.3.7","AU.L2-3.3.8","AU.L2-3.3.9"],
             "intake_fields": ["m0_siem"]},
            {"id": "config_management", "title": "Configuration Management (CM)", "type": "ai_narrative", "family": "CM",
             "control_ids": ["CM.L2-3.4.1","CM.L2-3.4.2","CM.L2-3.4.3","CM.L2-3.4.4","CM.L2-3.4.5","CM.L2-3.4.6","CM.L2-3.4.7","CM.L2-3.4.8","CM.L2-3.4.9"],
             "intake_fields": ["m0_edr", "m0_firewall"]},
            {"id": "identification_auth", "title": "Identification and Authentication (IA)", "type": "ai_narrative", "family": "IA",
             "control_ids": ["IA.L2-3.5.1","IA.L2-3.5.2","IA.L2-3.5.3","IA.L2-3.5.4","IA.L2-3.5.5","IA.L2-3.5.6","IA.L2-3.5.7","IA.L2-3.5.8","IA.L2-3.5.9","IA.L2-3.5.10","IA.L2-3.5.11"],
             "intake_fields": ["m0_identity_provider"]},
            {"id": "incident_response", "title": "Incident Response (IR)", "type": "ai_narrative", "family": "IR",
             "control_ids": ["IR.L2-3.6.1","IR.L2-3.6.2","IR.L2-3.6.3"],
             "intake_fields": []},
            {"id": "maintenance", "title": "Maintenance (MA)", "type": "ai_narrative", "family": "MA",
             "control_ids": ["MA.L2-3.7.1","MA.L2-3.7.2","MA.L2-3.7.3","MA.L2-3.7.4","MA.L2-3.7.5","MA.L2-3.7.6"],
             "intake_fields": []},
            {"id": "media_protection", "title": "Media Protection (MP)", "type": "ai_narrative", "family": "MP",
             "control_ids": ["MP.L2-3.8.1","MP.L2-3.8.2","MP.L2-3.8.3","MP.L2-3.8.4","MP.L2-3.8.5","MP.L2-3.8.6","MP.L2-3.8.7","MP.L2-3.8.8","MP.L2-3.8.9"],
             "intake_fields": []},
            {"id": "physical_protection", "title": "Physical Protection (PE)", "type": "ai_narrative", "family": "PE",
             "control_ids": ["PE.L2-3.10.1","PE.L2-3.10.2","PE.L2-3.10.3","PE.L2-3.10.4","PE.L2-3.10.5","PE.L2-3.10.6"],
             "intake_fields": []},
            {"id": "risk_assessment", "title": "Risk Assessment (RA)", "type": "ai_narrative", "family": "RA",
             "control_ids": ["RA.L2-3.11.1","RA.L2-3.11.2","RA.L2-3.11.3"],
             "intake_fields": []},
            {"id": "security_assessment", "title": "Security Assessment (CA)", "type": "ai_narrative", "family": "CA",
             "control_ids": ["CA.L2-3.12.1","CA.L2-3.12.2","CA.L2-3.12.3","CA.L2-3.12.4"],
             "intake_fields": []},
            {"id": "system_comms", "title": "System and Communications Protection (SC)", "type": "ai_narrative", "family": "SC",
             "control_ids": ["SC.L2-3.13.1","SC.L2-3.13.2","SC.L2-3.13.3","SC.L2-3.13.4","SC.L2-3.13.5","SC.L2-3.13.6","SC.L2-3.13.7","SC.L2-3.13.8","SC.L2-3.13.9","SC.L2-3.13.10","SC.L2-3.13.11","SC.L2-3.13.12","SC.L2-3.13.13","SC.L2-3.13.14","SC.L2-3.13.15","SC.L2-3.13.16"],
             "intake_fields": ["m0_firewall", "m0_email_platform"]},
            {"id": "system_integrity", "title": "System and Information Integrity (SI)", "type": "ai_narrative", "family": "SI",
             "control_ids": ["SI.L2-3.14.1","SI.L2-3.14.2","SI.L2-3.14.3","SI.L2-3.14.4","SI.L2-3.14.5","SI.L2-3.14.6","SI.L2-3.14.7"],
             "intake_fields": ["m0_edr", "m0_siem"]},
        ],
        "control_ids": [],
        "conditional_on": None,
        "min_modules_required": [0],
        "estimated_pages": 25,
    },
    {
        "doc_type": "incident_response_plan",
        "title": "Incident Response Plan (CUI Environment)",
        "description": "Standalone IR plan. NIST SP 800-171A explicitly lists incident response plan as an Examine object for IR controls.",
        "sections": [
            {"id": "purpose", "title": "Purpose and Scope", "type": "variable", "intake_fields": ["m0_company_name", "m0_cui_types"]},
            {"id": "incident_types", "title": "Incident Types and Classifications", "type": "boilerplate"},
            {"id": "roles_contacts", "title": "Roles and Contact Matrix", "type": "variable", "intake_fields": ["m0_company_name", "m0_employee_count"]},
            {"id": "detection_reporting", "title": "Detection and Reporting", "type": "ai_narrative", "intake_fields": ["m0_siem", "m0_edr"]},
            {"id": "triage", "title": "Triage and Classification", "type": "boilerplate"},
            {"id": "containment", "title": "Containment, Eradication, and Recovery", "type": "ai_narrative", "intake_fields": ["m0_edr", "m0_firewall"]},
            {"id": "evidence_preservation", "title": "Evidence Preservation and Logging", "type": "ai_narrative", "intake_fields": ["m0_siem"]},
            {"id": "external_reporting", "title": "External Reporting Obligations (DFARS 7012)", "type": "boilerplate"},
            {"id": "exercises", "title": "Exercises and Testing Plan", "type": "boilerplate"},
            {"id": "training_ir", "title": "IR Training Requirements", "type": "boilerplate"},
            {"id": "recordkeeping", "title": "Recordkeeping and Retention", "type": "boilerplate"},
        ],
        "control_ids": ["IR.L2-3.6.1", "IR.L2-3.6.2", "IR.L2-3.6.3"],
        "conditional_on": None,
        "min_modules_required": [0],
        "estimated_pages": 10,
    },
    {
        "doc_type": "config_management_plan",
        "title": "Configuration Management Plan",
        "description": "Baselines, inventory, change control. NIST SP 800-171A explicitly lists CM plan, baseline configuration, and system inventory as Examine objects.",
        "sections": [
            {"id": "purpose", "title": "Purpose and Scope", "type": "variable", "intake_fields": ["m0_company_name"]},
            {"id": "roles_cm", "title": "CM Roles and Responsibilities", "type": "variable", "intake_fields": ["m0_company_name", "m0_employee_count"]},
            {"id": "baseline", "title": "Baseline Configuration Standard", "type": "ai_narrative", "intake_fields": ["m0_edr", "m0_firewall", "m0_identity_provider"]},
            {"id": "inventory", "title": "System Inventory Management", "type": "ai_narrative", "intake_fields": ["m0_email_platform", "m0_edr", "m0_firewall", "m0_siem"]},
            {"id": "change_control", "title": "Change Control Process", "type": "ai_narrative", "intake_fields": []},
            {"id": "least_functionality", "title": "Least Functionality and Secure Configuration", "type": "ai_narrative", "intake_fields": ["m0_edr", "m0_firewall"]},
            {"id": "config_auditing", "title": "Configuration Auditing", "type": "boilerplate"},
            {"id": "records", "title": "Evidence and Records Retained", "type": "boilerplate"},
        ],
        "control_ids": ["CM.L2-3.4.1","CM.L2-3.4.2","CM.L2-3.4.3","CM.L2-3.4.4","CM.L2-3.4.5","CM.L2-3.4.6","CM.L2-3.4.7","CM.L2-3.4.8","CM.L2-3.4.9"],
        "conditional_on": None,
        "min_modules_required": [0],
        "estimated_pages": 8,
    },
    {
        "doc_type": "risk_assessment_report",
        "title": "Risk Assessment Report and Vulnerability Management Procedure",
        "description": "Risk methodology, findings, vuln mgmt. NIST SP 800-171A lists risk assessment and vulnerability scanning results as Examine objects. RA.L2-3.11.2 is a 5-point control.",
        "sections": [
            {"id": "methodology", "title": "Risk Assessment Methodology", "type": "boilerplate"},
            {"id": "scope_ra", "title": "Assessment Scope", "type": "variable", "intake_fields": ["m0_company_name", "m0_cui_types"]},
            {"id": "risk_register", "title": "Risk Register", "type": "ai_narrative", "intake_fields": ["m0_email_platform", "m0_identity_provider", "m0_edr", "m0_firewall"]},
            {"id": "vuln_mgmt", "title": "Vulnerability Management Procedure", "type": "ai_narrative", "intake_fields": ["m0_edr"]},
            {"id": "patch_sla", "title": "Patch Management SLAs", "type": "boilerplate"},
            {"id": "scan_summary", "title": "Most Recent Scan Summary", "type": "variable", "intake_fields": []},
        ],
        "control_ids": ["RA.L2-3.11.1","RA.L2-3.11.2","RA.L2-3.11.3"],
        "conditional_on": None,
        "min_modules_required": [0],
        "estimated_pages": 8,
    },
    {
        "doc_type": "training_program",
        "title": "Security Awareness and Training Program",
        "description": "Training roles, curriculum, records. NIST SP 800-171A expects training policy, curriculum, materials, and records as Examine objects.",
        "sections": [
            {"id": "purpose_training", "title": "Purpose and Scope", "type": "variable", "intake_fields": ["m0_company_name"]},
            {"id": "training_roles", "title": "Training Roles and Audiences", "type": "variable", "intake_fields": ["m0_employee_count"]},
            {"id": "awareness", "title": "Annual Security Awareness Training", "type": "ai_narrative", "intake_fields": []},
            {"id": "role_based", "title": "Role-Based Training", "type": "ai_narrative", "intake_fields": []},
            {"id": "insider_threat", "title": "Insider Threat Awareness", "type": "boilerplate"},
            {"id": "records_training", "title": "Recordkeeping and Tracking", "type": "ai_narrative", "intake_fields": []},
        ],
        "control_ids": ["AT.L2-3.2.1","AT.L2-3.2.2","AT.L2-3.2.3"],
        "conditional_on": None,
        "min_modules_required": [0],
        "estimated_pages": 6,
    },
    {
        "doc_type": "scope_package",
        "title": "CMMC Level 2 Assessment Scope Package",
        "description": "Asset inventory, network diagram placeholder, CUI flow, ESP list. DoD CIO Level 2 Scoping Guide requires asset categorization and network diagram.",
        "sections": [
            {"id": "purpose_scope", "title": "Purpose and Assessment Boundary", "type": "variable", "intake_fields": ["m0_company_name", "m0_dfars_clause"]},
            {"id": "asset_categories", "title": "Asset Categorization Overview", "type": "boilerplate"},
            {"id": "asset_inventory", "title": "Asset Inventory", "type": "ai_narrative", "intake_fields": ["m0_email_platform", "m0_identity_provider", "m0_edr", "m0_firewall", "m0_siem", "m0_employee_count", "m0_locations"]},
            {"id": "network_diagram", "title": "Network Diagram", "type": "variable", "intake_fields": ["m0_firewall"]},
            {"id": "cui_flow", "title": "CUI Flow Narrative", "type": "ai_narrative", "intake_fields": ["m0_cui_types", "m0_cui_flow", "m0_email_platform"]},
            {"id": "esp_list", "title": "External Service Providers", "type": "ai_narrative", "intake_fields": ["m0_email_platform", "m0_identity_provider"]},
        ],
        "control_ids": ["CM.L2-3.4.1","CA.L2-3.12.4"],
        "conditional_on": None,
        "min_modules_required": [0],
        "estimated_pages": 8,
    },
    {
        "doc_type": "shared_responsibility_matrix",
        "title": "Customer Responsibility Matrix (Cloud Service Providers)",
        "description": "CRM/SRM for M365 GCC High or other CSPs. Generated only when ESPs/cloud services are in scope.",
        "sections": [
            {"id": "purpose_crm", "title": "Purpose", "type": "variable", "intake_fields": ["m0_company_name", "m0_email_platform"]},
            {"id": "csp_overview", "title": "Cloud Service Provider Overview", "type": "ai_narrative", "intake_fields": ["m0_email_platform", "m0_identity_provider"]},
            {"id": "responsibility_matrix", "title": "Control Responsibility Matrix", "type": "ai_narrative", "intake_fields": ["m0_email_platform"]},
            {"id": "inherited_controls", "title": "Inherited Controls Summary", "type": "ai_narrative", "intake_fields": ["m0_email_platform"]},
            {"id": "customer_controls", "title": "Customer-Implemented Controls", "type": "ai_narrative", "intake_fields": ["m0_identity_provider", "m0_edr", "m0_firewall"]},
        ],
        "control_ids": [],
        "conditional_on": "m0_email_platform",
        "conditional_values": ["Microsoft 365 GCC High", "Microsoft 365 GCC"],
        "min_modules_required": [0],
        "estimated_pages": 5,
    },
]


def run_migration():
    print("Running document engine DB migration...")

    with get_session() as session:
        statements = [s.strip() for s in MIGRATION_SQL.split(";") if s.strip()]
        for stmt in statements:
            try:
                session.execute(text(stmt))
            except Exception as e:
                if "already exists" in str(e).lower():
                    continue
                print(f"  Warning: {e}")
        session.commit()

    # Verify tables
    with get_session() as session:
        for table in ["document_templates", "generated_documents"]:
            result = session.execute(
                text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = :t"),
                {"t": table}
            ).scalar()
            print(f"  [{'OK' if result else 'MISSING'}] {table}")

    # Seed templates
    print("\nSeeding document templates...")
    with get_session() as session:
        for tmpl in DOCUMENT_TEMPLATES:
            tmpl_id = hashlib.sha256(f"template:{tmpl['doc_type']}".encode()).hexdigest()[:20]

            # Collect all control_ids from sections if not set at top level
            all_control_ids = list(tmpl.get("control_ids", []))
            for sec in tmpl.get("sections", []):
                all_control_ids.extend(sec.get("control_ids", []))
            all_control_ids = sorted(set(all_control_ids))

            try:
                session.execute(text("""
                    INSERT INTO document_templates
                        (id, doc_type, title, description, sections, control_ids,
                         generation_rules, conditional_on, conditional_values,
                         min_modules_required, estimated_pages)
                    VALUES
                        (:id, :doc_type, :title, :desc, CAST(:sections AS json),
                         CAST(:control_ids AS json), CAST(:gen_rules AS json),
                         :conditional_on, CAST(:conditional_values AS json),
                         CAST(:min_modules AS json), :pages)
                    ON CONFLICT (doc_type) DO UPDATE SET
                        title = :title,
                        description = :desc,
                        sections = CAST(:sections AS json),
                        control_ids = CAST(:control_ids AS json),
                        conditional_on = :conditional_on,
                        conditional_values = CAST(:conditional_values AS json),
                        min_modules_required = CAST(:min_modules AS json),
                        estimated_pages = :pages
                """), {
                    "id": tmpl_id,
                    "doc_type": tmpl["doc_type"],
                    "title": tmpl["title"],
                    "desc": tmpl.get("description", ""),
                    "sections": json.dumps(tmpl["sections"]),
                    "control_ids": json.dumps(all_control_ids),
                    "gen_rules": json.dumps(tmpl.get("generation_rules", {})),
                    "conditional_on": tmpl.get("conditional_on"),
                    "conditional_values": json.dumps(tmpl.get("conditional_values", [])),
                    "min_modules": json.dumps(tmpl.get("min_modules_required", [])),
                    "pages": tmpl.get("estimated_pages"),
                })
                print(f"  [OK] {tmpl['doc_type']} ({tmpl['title'][:50]}...)")
            except Exception as e:
                print(f"  [ERR] {tmpl['doc_type']}: {e}")

        session.commit()

    # Verify count
    with get_session() as session:
        count = session.execute(text("SELECT COUNT(*) FROM document_templates")).scalar()
        print(f"\n{count} templates registered.")


if __name__ == "__main__":
    run_migration()
