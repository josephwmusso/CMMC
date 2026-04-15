"""
src/api/intake_modules/module0_foundation.py

Module 0 — Foundation. Migrated verbatim from the hardcoded
MODULE_0_QUESTIONS list that used to live in src/api/intake_routes.py.
IDs, text, options, and branching behaviour are preserved exactly so
existing sessions keep working.
"""
from src.api.intake_modules import (
    IntakeQuestion,
    ModuleDefinition,
    QuestionTier,
    QuestionType,
    register_module,
)


SECTION_COMPANY = "Company Information"
SECTION_CUI = "Contract & CUI Scoping"
SECTION_ENV = "Environment Scoping"
SECTION_TECH = "Technology Stack"
SECTION_EXISTING = "Existing Compliance"


QUESTIONS = [
    # ── Company Information ──────────────────────────────────────────────
    IntakeQuestion(
        id="m0_company_name",
        text="What is your company's legal name?",
        question_type=QuestionType.TEXT,
        tier=QuestionTier.SCREENING,
        section=SECTION_COMPANY,
        required=True,
        help_text="The name as it appears on your government contracts.",
    ),
    IntakeQuestion(
        id="m0_cage_code",
        text="What is your CAGE code?",
        question_type=QuestionType.TEXT,
        tier=QuestionTier.SCREENING,
        section=SECTION_COMPANY,
        required=False,
        help_text="A 5-character identifier assigned by DLA. You can look it up at sam.gov.",
    ),
    IntakeQuestion(
        id="m0_employee_count",
        text="How many employees does your company have?",
        question_type=QuestionType.NUMBER,
        tier=QuestionTier.SCREENING,
        section=SECTION_COMPANY,
        required=True,
        help_text="Include full-time, part-time, and contractors who access your systems.",
    ),
    IntakeQuestion(
        id="m0_locations",
        text="How many physical locations does your company operate from?",
        question_type=QuestionType.NUMBER,
        tier=QuestionTier.SCREENING,
        section=SECTION_COMPANY,
        required=True,
        help_text="Include offices, labs, manufacturing facilities, and any location where CUI is handled.",
    ),
    IntakeQuestion(
        id="m0_primary_location",
        text="Where is your primary office located?",
        question_type=QuestionType.TEXT,
        tier=QuestionTier.SCREENING,
        section=SECTION_COMPANY,
        required=True,
        help_text="City and state (e.g., 'Columbia, MD').",
    ),

    # ── Contract & CUI Scoping ───────────────────────────────────────────
    IntakeQuestion(
        id="m0_dfars_clause",
        text="Do your contracts include the DFARS 252.204-7012 clause?",
        question_type=QuestionType.YES_NO_UNSURE,
        tier=QuestionTier.SCREENING,
        section=SECTION_CUI,
        required=True,
        help_text="This clause requires you to protect Controlled Unclassified Information (CUI). Check your contract or ask your contracting officer.",
        metadata={
            "branch": {
                "unsure": {"flag": "Verify DFARS clause with contracting officer before proceeding."},
            },
        },
    ),
    IntakeQuestion(
        id="m0_cui_types",
        text="What types of CUI does your company handle?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        tier=QuestionTier.SCREENING,
        section=SECTION_CUI,
        required=True,
        help_text="Select all that apply. CUI is sensitive government information that isn't classified.",
        options=[
            "Technical data (drawings, specs, test results)",
            "ITAR-controlled data",
            "Controlled Technical Information (CTI)",
            "Export-controlled data",
            "Source selection information",
            "Budget/financial data",
            "Personally identifiable information (PII)",
            "I'm not sure what types of CUI we handle",
        ],
    ),
    IntakeQuestion(
        id="m0_cui_flow",
        text="How does CUI typically enter and move through your organization?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        tier=QuestionTier.SCREENING,
        section=SECTION_CUI,
        required=True,
        help_text="This determines which systems are 'in scope' for CMMC.",
        options=[
            "We receive CUI only via email",
            "CUI is stored on shared network drives",
            "CUI lives in our ERP or database system",
            "CUI is in cloud storage (SharePoint, OneDrive, etc.)",
            "CUI is on individual laptops/desktops",
            "CUI is in a specialized application",
        ],
    ),

    # ── Environment Scoping ──────────────────────────────────────────────
    IntakeQuestion(
        id="m0_remote_workers",
        text="Do any of your employees work remotely or access company systems from outside the office?",
        question_type=QuestionType.YES_NO_UNSURE,
        tier=QuestionTier.SCREENING,
        section=SECTION_ENV,
        required=True,
        help_text="This includes VPN connections, remote desktop, or accessing cloud apps from home.",
        control_ids=["AC.L2-3.1.12", "AC.L2-3.1.14", "AC.L2-3.1.15"],
        control_id="AC.L2-3.1.12",
        metadata={
            "branch": {
                "no": {"skip": ["AC.L2-3.1.12", "AC.L2-3.1.14", "AC.L2-3.1.15"]},
            },
        },
    ),
    IntakeQuestion(
        id="m0_wireless",
        text="Does your office have a wireless (Wi-Fi) network?",
        question_type=QuestionType.YES_NO_UNSURE,
        tier=QuestionTier.SCREENING,
        section=SECTION_ENV,
        required=True,
        help_text="Include guest networks and any wireless access points in your facility.",
        control_ids=["AC.L2-3.1.16", "AC.L2-3.1.17"],
        control_id="AC.L2-3.1.16",
        metadata={
            "branch": {
                "no": {"skip": ["AC.L2-3.1.16", "AC.L2-3.1.17"]},
            },
        },
    ),

    # ── Technology Stack ─────────────────────────────────────────────────
    IntakeQuestion(
        id="m0_email_platform",
        text="What email system does your company use?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        tier=QuestionTier.SCREENING,
        section=SECTION_TECH,
        required=True,
        help_text="This is one of the most important questions for CMMC scoping.",
        options=[
            "Microsoft 365 GCC High",
            "Microsoft 365 GCC",
            "Microsoft 365 (commercial/business)",
            "Google Workspace",
            "On-premises Exchange",
            "Other email provider",
            "I'm not sure",
        ],
        control_ids=["SC.L2-3.13.1", "SC.L2-3.13.8", "SC.L2-3.13.11"],
        control_id="SC.L2-3.13.1",
        metadata={
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
        },
    ),
    IntakeQuestion(
        id="m0_identity_provider",
        text="How do your employees log into their computers and applications?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        tier=QuestionTier.SCREENING,
        section=SECTION_TECH,
        required=True,
        help_text="This is your identity/access management system.",
        options=[
            "Microsoft Entra ID (Azure AD) with MFA",
            "Microsoft Entra ID (Azure AD) without MFA",
            "On-premises Active Directory with MFA",
            "On-premises Active Directory without MFA",
            "Okta",
            "Google Identity",
            "No centralized login system",
            "I'm not sure",
        ],
        allows_free_text=True,
        free_text_prompt="Describe your identity and access management setup (e.g., providers, MFA method, federation)",
        control_ids=["AC.L2-3.1.1", "AC.L2-3.1.2", "IA.L2-3.5.1", "IA.L2-3.5.2", "IA.L2-3.5.3"],
        control_id="AC.L2-3.1.1",
        metadata={
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
        },
    ),
    IntakeQuestion(
        id="m0_edr",
        text="What endpoint protection (antivirus/EDR) do you use on your computers?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        tier=QuestionTier.SCREENING,
        section=SECTION_TECH,
        required=True,
        help_text="EDR = Endpoint Detection and Response. This is your anti-malware solution.",
        options=[
            "CrowdStrike Falcon",
            "Microsoft Defender for Endpoint",
            "SentinelOne",
            "Carbon Black",
            "Symantec/Broadcom",
            "Traditional antivirus only (e.g., Norton, McAfee)",
            "None / I'm not sure",
        ],
        allows_free_text=True,
        free_text_prompt="Describe your endpoint detection and response tools",
        control_ids=["SI.L2-3.14.1", "SI.L2-3.14.2", "SI.L2-3.14.4", "SI.L2-3.14.5"],
        control_id="SI.L2-3.14.1",
        metadata={
            "branch": {
                "None / I'm not sure": {
                    "flag": "critical",
                    "message": "Endpoint protection is required for CMMC Level 2. This is a critical gap.",
                },
            },
        },
    ),
    IntakeQuestion(
        id="m0_firewall",
        text="What firewall protects your network?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        tier=QuestionTier.SCREENING,
        section=SECTION_TECH,
        required=True,
        help_text="This is the device at the edge of your network that controls traffic.",
        options=[
            "Palo Alto Networks",
            "Fortinet FortiGate",
            "Cisco (ASA, Firepower, Meraki)",
            "SonicWall",
            "pfSense / OPNsense",
            "ISP-provided router only",
            "I'm not sure",
        ],
        allows_free_text=True,
        free_text_prompt="Describe your network firewall and perimeter security setup",
        control_ids=["SC.L2-3.13.1", "SC.L2-3.13.5", "SC.L2-3.13.6"],
        control_id="SC.L2-3.13.1",
        metadata={
            "branch": {
                "ISP-provided router only": {
                    "flag": "high",
                    "message": "An ISP router alone is unlikely to meet CMMC boundary protection requirements. A commercial firewall is strongly recommended.",
                },
            },
        },
    ),
    IntakeQuestion(
        id="m0_siem",
        text="Do you have a system that collects and monitors security logs?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        tier=QuestionTier.SCREENING,
        section=SECTION_TECH,
        required=True,
        help_text="This is called a SIEM (Security Information and Event Management). It's where your audit logs go.",
        options=[
            "Microsoft Sentinel",
            "Splunk",
            "Elastic SIEM",
            "Arctic Wolf / Blumira / other managed",
            "We collect logs but don't have a SIEM",
            "No log collection",
            "I'm not sure",
        ],
        allows_free_text=True,
        free_text_prompt="Describe your security monitoring and log management setup",
        control_ids=["AU.L2-3.3.1", "AU.L2-3.3.2", "AU.L2-3.3.5", "SI.L2-3.14.6", "SI.L2-3.14.7"],
        control_id="AU.L2-3.3.1",
    ),
    IntakeQuestion(
        id="m0_training_tool",
        text="What security awareness training platform does your organization use?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        tier=QuestionTier.SCREENING,
        section=SECTION_TECH,
        required=True,
        help_text=(
            "Security awareness training is required under AT.L2-3.2.1 / 3.2.2. "
            "This platform delivers new-hire and annual refreshers plus phishing drills."
        ),
        options=[
            "KnowBe4",
            "Proofpoint Security Awareness",
            "Cofense PhishMe",
            "SANS Security Awareness",
            "Infosec IQ",
            "Ninjio",
            "Microsoft Security Awareness (built-in)",
            "Other",
            "None",
        ],
        allows_free_text=True,
        free_text_prompt="Describe your security awareness training program and tools",
        control_ids=["AT.L2-3.2.1", "AT.L2-3.2.2", "AT.L2-3.2.3"],
        control_id="AT.L2-3.2.1",
    ),

    # ── Existing Compliance ──────────────────────────────────────────────
    IntakeQuestion(
        id="m0_existing_docs",
        text="Which of these documents does your company already have?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        tier=QuestionTier.SCREENING,
        section=SECTION_EXISTING,
        required=True,
        help_text="Select any that exist, even if they're outdated. We can work with what you have.",
        options=[
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
        metadata={
            "branch": {
                "None of these": {
                    "flag": "info",
                    "message": "No problem - the platform will help you create all required documentation.",
                },
            },
        },
    ),
]


register_module(ModuleDefinition(
    number=0,
    name="Foundation",
    description="Organization scope, CUI boundary, tool stack, and provider dependencies",
    families=[],
    control_ids=[],
    doc_templates=["scope_package"],
    estimated_minutes=15,
    questions=QUESTIONS,
))
