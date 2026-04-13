"""
src/api/intake_modules/module8_si.py

Module 8 — System & Information Integrity (SI).
7 CONTROL_STATUS questions.

Weight note: the caller spec said 3.14.1, 3.14.2, and 3.14.3 are all
5-point controls, but data/nist/controls_full.py shows only 3.14.1 as
5-pt (3.14.2 and 3.14.3 are 3-pt). Following the data (source of truth)
and only flagging 3.14.1 as high-weight.
"""
from src.api.intake_modules import ModuleDefinition, register_module
from src.api.intake_modules._shared import status_q


M = 8
SECTION_SI = "System & Information Integrity"


QUESTIONS = [
    status_q(M, "SI", "3.14.1", "SI.L2-3.14.1", "Flaw Remediation",
        SECTION_SI, 5,
        "Identify, report, and correct information and system flaws in a timely manner. "
        "Defender Vulnerability Management surfaces CVEs; Intune Update Rings drive "
        "patching with critical ≤7 days, high ≤30 days; Sentinel tracks open-patch KPIs.",
        high_weight_flag=True,
    ),
    status_q(M, "SI", "3.14.2", "SI.L2-3.14.2", "Malicious Code Protection",
        SECTION_SI, 3,
        "Provide protection from malicious code at designated locations within the system. "
        "CrowdStrike Falcon on all endpoints and servers; Microsoft Defender for Endpoint "
        "supplements on M365; Palo Alto PA-450 threat prevention module at the perimeter.",
    ),
    status_q(M, "SI", "3.14.3", "SI.L2-3.14.3", "Security Alerts and Advisories",
        SECTION_SI, 3,
        "Monitor system security alerts and advisories and take action in response. "
        "Subscribed to CISA Known Exploited Vulnerabilities and the MS Security Update "
        "Guide; alerts route to a dedicated Teams channel and the ISSO runs a weekly "
        "triage review.",
    ),
    status_q(M, "SI", "3.14.4", "SI.L2-3.14.4", "Update Malicious Code Protection",
        SECTION_SI, 1,
        "Update malicious code protection mechanisms when new releases are available. "
        "CrowdStrike auto-updates sensor version and signatures; Defender for Endpoint "
        "auto-updates via Intune; no manual touch required.",
    ),
    status_q(M, "SI", "3.14.5", "SI.L2-3.14.5", "Perform Malicious Code Scans",
        SECTION_SI, 1,
        "Perform periodic scans of the system and real-time scans of files from external "
        "sources. CrowdStrike enables continuous prevention plus a scheduled monthly full "
        "scan; Defender real-time on-access scanning covers downloaded files.",
    ),
    status_q(M, "SI", "3.14.6", "SI.L2-3.14.6", "Monitor System Security",
        SECTION_SI, 1,
        "Monitor the system to detect attacks and indicators of potential attacks. Sentinel "
        "analytic rules cover user-behavior anomalies, impossible travel, and suspicious "
        "sign-ins; CrowdStrike OverWatch MDR provides 24/7 managed detection.",
    ),
    status_q(M, "SI", "3.14.7", "SI.L2-3.14.7", "Identify Unauthorized Use",
        SECTION_SI, 1,
        "Identify unauthorized use of the system. Sentinel rules flag anomalous access "
        "patterns and off-hours activity; M365 Purview DLP alerts on CUI exfiltration "
        "attempts via email or cloud storage.",
    ),
]


register_module(ModuleDefinition(
    number=M,
    name="System & Information Integrity",
    description="SI controls — flaw remediation, malicious-code protection, alerts, and continuous monitoring.",
    families=["SI"],
    control_ids=[q.control_id for q in QUESTIONS],
    doc_templates=["policy_manual"],
    estimated_minutes=10,
    questions=QUESTIONS,
))
