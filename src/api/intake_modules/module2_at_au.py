"""
src/api/intake_modules/module2_at_au.py

Module 2 — Awareness & Training (AT) + Audit & Accountability (AU).
One CONTROL_STATUS question per control, 12 total (AT=3, AU=9).

Note: the caller spec listed only AT.L2-3.2.1 and AT.L2-3.2.2, but
data/nist/controls_full.py contains AT.L2-3.2.3 as well. Covered here
to keep the full 110-control set intact across modules 1-8.
"""
from src.api.intake_modules import ModuleDefinition, register_module
from src.api.intake_modules._shared import status_q


M = 2
SECTION_AT = "Awareness & Training"
SECTION_AU = "Audit & Accountability"


QUESTIONS = [
    # ── AT ───────────────────────────────────────────────────────────────
    status_q(M, "AT", "3.2.1", "AT.L2-3.2.1", "Role-Based Risk Awareness",
        SECTION_AT, 3,
        "Make users, admins, and managers aware of the security risks of their activities. "
        "For Apex Defense (45 employees on Entra ID + M365 GCC High), KnowBe4 delivers the "
        "new-hire security awareness course and annual refreshers; enrollment is driven by "
        "Entra ID group membership so onboarding auto-enrolls and offboarding auto-revokes.",
        high_weight_flag=False,
    ),
    status_q(M, "AT", "3.2.2", "AT.L2-3.2.2", "Role-Based Training",
        SECTION_AT, 3,
        "Role-specific training: admins get elevated-access training, developers get secure "
        "coding, executives get targeted phishing drills. KnowBe4 supports custom learning "
        "paths per role group in Entra ID; training completion is attested in the LMS and "
        "evidenced as a PDF certificate stored in the SharePoint compliance library.",
    ),
    status_q(M, "AT", "3.2.3", "AT.L2-3.2.3", "Insider Threat Awareness",
        SECTION_AT, 1,
        "Annual briefing on insider-threat indicators and the reporting channel. KnowBe4 has "
        "a dedicated insider-threat module; completion is tracked via Entra group membership "
        "and recorded in the HR system as an annual compliance item.",
    ),

    # ── AU ───────────────────────────────────────────────────────────────
    status_q(M, "AU", "3.3.1", "AU.L2-3.3.1", "System Auditing",
        SECTION_AU, 5,
        "Create, protect, and retain audit records covering logins, privilege changes, CUI "
        "access, and security-relevant events. For Apex: Microsoft Sentinel is the central "
        "SIEM, ingesting Entra ID sign-in logs, M365 Unified Audit Log, CrowdStrike Falcon "
        "event streams, and Palo Alto PA-450 syslog. 1-year hot retention plus 2-year cold.",
        high_weight_flag=True,
    ),
    status_q(M, "AU", "3.3.2", "AU.L2-3.3.2", "User Accountability",
        SECTION_AU, 3,
        "Every action must be traceable to a named individual — no shared accounts. Entra ID "
        "is the single source of truth: each employee has a unique UPN, each admin has a "
        "separate privileged account, and CrowdStrike Falcon per-device agents attribute "
        "endpoint actions to the signed-in user.",
    ),
    status_q(M, "AU", "3.3.3", "AU.L2-3.3.3", "Event Review",
        SECTION_AU, 1,
        "Review and update the list of audited events at defined intervals. Quarterly "
        "Sentinel analytic-rule review plus an annual refresh of the organization's list of "
        "auditable events documented in the SSP.",
    ),
    status_q(M, "AU", "3.3.4", "AU.L2-3.3.4", "Audit Failure Alerting",
        SECTION_AU, 1,
        "Alert immediately if audit logging fails. Sentinel data-connector health alerts fire "
        "when ingestion from Entra ID, M365, or CrowdStrike stops; CrowdStrike console "
        "surfaces agent check-in failures as Critical events routed to the on-call channel.",
    ),
    status_q(M, "AU", "3.3.5", "AU.L2-3.3.5", "Audit Correlation",
        SECTION_AU, 1,
        "Correlate audit records across system components to support investigation. Sentinel "
        "KQL joins firewall flows, Entra sign-ins, and CrowdStrike detections into a single "
        "timeline; workbooks present correlated views for common incident patterns.",
    ),
    status_q(M, "AU", "3.3.6", "AU.L2-3.3.6", "Reduction and Reporting",
        SECTION_AU, 1,
        "Provide audit record reduction and report generation. Sentinel workbooks + scheduled "
        "KQL reports satisfy this; CISO receives a weekly summary of auth anomalies and "
        "security events.",
    ),
    status_q(M, "AU", "3.3.7", "AU.L2-3.3.7", "Time Stamps",
        SECTION_AU, 1,
        "System clocks synced to an authoritative time source so audit timestamps are "
        "trustworthy. Domain-joined Windows endpoints sync via the Windows Time Service to "
        "an Entra-managed NTP hierarchy; Palo Alto PA-450 NTP points at time.nist.gov.",
    ),
    status_q(M, "AU", "3.3.8", "AU.L2-3.3.8", "Audit Record Protection",
        SECTION_AU, 1,
        "Protect audit information and tools from unauthorized access, modification, and "
        "deletion. Sentinel workspace uses Entra RBAC with PIM-gated Contributor role; "
        "retention policies are locked at the workspace level so entries are immutable.",
    ),
    status_q(M, "AU", "3.3.9", "AU.L2-3.3.9", "Audit Management",
        SECTION_AU, 1,
        "Limit audit-log management to a small set of privileged users. Entra PIM requires "
        "time-boxed activation + MFA for Sentinel management roles; Conditional Access "
        "restricts those activations to managed devices on the admin jump-box subnet.",
    ),
]


register_module(ModuleDefinition(
    number=M,
    name="Awareness & Training + Audit & Accountability",
    description="AT and AU control families — user awareness, role-based training, and the audit/logging program.",
    families=["AT", "AU"],
    control_ids=[q.control_id for q in QUESTIONS],
    doc_templates=["training_program"],
    estimated_minutes=15,
    questions=QUESTIONS,
))
