"""
src/api/intake_modules/module6_ra_ca.py

Module 6 — Risk Assessment (RA) + Security Assessment (CA).
7 CONTROL_STATUS questions (RA=3, CA=4).

Note: CA.L2-3.12.4 (System Security Plan) is POA&M-ineligible per the
DoD Assessment Methodology and must be MET at assessment time.
"""
from src.api.intake_modules import ModuleDefinition, register_module
from src.api.intake_modules._shared import status_q


M = 6
SECTION_RA = "Risk Assessment"
SECTION_CA = "Security Assessment"


QUESTIONS = [
    # ── RA ───────────────────────────────────────────────────────────────
    status_q(M, "RA", "3.11.1", "RA.L2-3.11.1", "Risk Assessments",
        SECTION_RA, 3,
        "Periodically assess risk to operations, assets, and individuals from CUI processing "
        "systems. Organizations should perform an annual formal risk assessment; vulnerability "
        "Management and Sentinel risk scoring feed findings into the RA report.",
    ),
    status_q(M, "RA", "3.11.2", "RA.L2-3.11.2", "Vulnerability Scan",
        SECTION_RA, 1,
        "Scan for vulnerabilities in systems and applications periodically and when new "
        "vulnerabilities are identified. Defender Vulnerability Management runs continuous "
        "internal scans; external authenticated scans via Tenable or Qualys monthly.",
    ),
    status_q(M, "RA", "3.11.3", "RA.L2-3.11.3", "Vulnerability Remediation",
        SECTION_RA, 1,
        "Remediate vulnerabilities in accordance with risk assessments. Patch SLA — "
        "critical ≤7 days, high ≤30 days, medium ≤90 — tracked in the ticket system; "
        "Intune deployment rings enforce rollout; exception process requires ISSO approval.",
    ),

    # ── CA ───────────────────────────────────────────────────────────────
    status_q(M, "CA", "3.12.1", "CA.L2-3.12.1", "Security Control Assessment",
        SECTION_CA, 3,
        "Periodically assess the security controls in the system to determine effectiveness. "
        "Annual internal review maps evidence to each control; Intranest generates the "
        "compliance binder aligned to the SSP, and the ISSO signs off on control status.",
    ),
    status_q(M, "CA", "3.12.2", "CA.L2-3.12.2", "Plan of Action & Milestones",
        SECTION_CA, 1,
        "Develop and implement plans of action designed to correct deficiencies and reduce "
        "or eliminate vulnerabilities. Intranest auto-generates POA&M items from gap "
        "findings; the ISSO owns closure and a quarterly review cadence updates milestones.",
    ),
    status_q(M, "CA", "3.12.3", "CA.L2-3.12.3", "Security Control Monitoring",
        SECTION_CA, 1,
        "Monitor security controls on an ongoing basis to ensure continued effectiveness. "
        "Sentinel control-effectiveness dashboards and a monthly ops review convert live "
        "telemetry into a continuous monitoring report for the ISSO and leadership.",
    ),
    status_q(M, "CA", "3.12.4", "CA.L2-3.12.4", "System Security Plan",
        SECTION_CA, 3,
        "\u26a0\ufe0f CA.L2-3.12.4 CANNOT be placed on a Plan of Action & Milestones "
        "(POA&M). You must have a current SSP at the time of assessment. Intranest "
        "generates your SSP automatically.\n\n"
        "Develop, document, and periodically update the SSP describing system boundaries, "
        "environments of operation, implemented security requirements, and relationships to "
        "other systems. Intranest produces this document from your intake answers and "
        "regenerates it after each annual review or significant change.",
    ),
]


register_module(ModuleDefinition(
    number=M,
    name="Risk & Security Assessment",
    description="RA and CA control families — risk assessment, vulnerability management, POA&M, and the SSP.",
    families=["RA", "CA"],
    control_ids=[q.control_id for q in QUESTIONS],
    doc_templates=["risk_assessment"],
    estimated_minutes=10,
    questions=QUESTIONS,
))
