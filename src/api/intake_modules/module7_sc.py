"""
src/api/intake_modules/module7_sc.py

Module 7 — System & Communications Protection (SC).
16 primary CONTROL_STATUS questions plus a conditional follow-up on
SC.L2-3.13.11 (FIPS-validated cryptography scope).
"""
from src.api.intake_modules import ModuleDefinition, register_module
from src.api.intake_modules._shared import status_q, followup_q


M = 7
SECTION_SC = "System & Communications Protection"


QUESTIONS = [
    status_q(M, "SC", "3.13.1", "SC.L2-3.13.1", "Boundary Protection",
        SECTION_SC, 5,
        "Monitor, control, and protect communications at external and key internal "
        "boundaries. A next-gen firewall enforces the external perimeter and "
        "inter-VLAN boundaries between the CUI, user, and DMZ zones; Sentinel ingests "
        "firewall logs for correlation.",
        high_weight_flag=True,
    ),
    status_q(M, "SC", "3.13.2", "SC.L2-3.13.2", "Security Engineering Principles",
        SECTION_SC, 3,
        "Employ architectural designs, software development techniques, and systems "
        "engineering principles that promote information security. Zero-trust reference "
        "architecture (Entra ID + Intune + Conditional Access) is the default; new systems "
        "require an ISSO-reviewed design.",
    ),
    status_q(M, "SC", "3.13.3", "SC.L2-3.13.3", "Separate User Functionality",
        SECTION_SC, 1,
        "Separate user functionality from system management functionality. Admins use "
        "dedicated privileged accounts (Entra PIM) and a jump-box VM for server "
        "administration — no admin tasks from the daily-driver laptop.",
    ),
    status_q(M, "SC", "3.13.4", "SC.L2-3.13.4", "Shared Resource Isolation",
        SECTION_SC, 1,
        "Prevent unauthorized and unintended information transfer via shared system "
        "resources. Intune clears storage on device reassignment; CUI-processing "
        "workstations live on a dedicated VLAN with firewall isolation.",
    ),
    status_q(M, "SC", "3.13.5", "SC.L2-3.13.5", "Public-Access Segregation",
        SECTION_SC, 1,
        "Implement subnetworks for publicly accessible system components that are "
        "physically or logically separated from internal networks. Palo Alto PA-450 DMZ "
        "zone hosts the public-facing services with no routes into the CUI network.",
    ),
    status_q(M, "SC", "3.13.6", "SC.L2-3.13.6", "Deny Traffic by Default",
        SECTION_SC, 1,
        "Deny network communications traffic by default and allow by exception. Palo Alto "
        "PA-450 zero-trust policy at perimeter and between zones uses explicit allow rules "
        "on top of a default-deny posture.",
    ),
    status_q(M, "SC", "3.13.7", "SC.L2-3.13.7", "Prevent Split Tunneling",
        SECTION_SC, 1,
        "Prevent remote devices from simultaneously establishing a non-remote connection "
        "and communicating via some other connection. GlobalProtect VPN is configured as "
        "always-on with split-tunneling disabled — all traffic is tunneled.",
    ),
    status_q(M, "SC", "3.13.8", "SC.L2-3.13.8", "Cryptographic Transmission Protection",
        SECTION_SC, 1,
        "Implement cryptographic mechanisms to prevent unauthorized disclosure of CUI "
        "during transmission unless otherwise protected by alternative physical safeguards. "
        "TLS 1.2+ for all M365 services (GCC High FIPS); FIPS-validated IPsec for VPN; SMB "
        "signing enforced on file shares.",
    ),
    status_q(M, "SC", "3.13.9", "SC.L2-3.13.9", "Terminate Network Connections",
        SECTION_SC, 1,
        "Terminate network connections associated with communication sessions at the end of "
        "the session or after a defined period of inactivity. Entra Conditional Access "
        "sign-in frequency policy; GlobalProtect VPN idle timeout 30 minutes.",
    ),
    status_q(M, "SC", "3.13.10", "SC.L2-3.13.10", "Cryptographic Key Management",
        SECTION_SC, 1,
        "Establish and manage cryptographic keys for cryptography employed in the system. "
        "Azure Key Vault (HSM-backed) holds application and Veeam encryption keys; "
        "BitLocker recovery keys are escrowed in Entra ID.",
    ),
    status_q(M, "SC", "3.13.11", "SC.L2-3.13.11", "CUI Encryption (FIPS)",
        SECTION_SC, 5,
        "Employ FIPS-validated cryptography when used to protect the confidentiality of "
        "CUI. BitLocker in FIPS mode on all laptops; Palo Alto PA-450 in FIPS-CC mode; "
        "M365 GCC High runs FIPS 140-2 cryptographic modules by default.",
        high_weight_flag=True,
    ),
    status_q(M, "SC", "3.13.12", "SC.L2-3.13.12", "Collaborative Computing",
        SECTION_SC, 1,
        "Prohibit remote activation of collaborative computing devices and provide "
        "indication of use to users. Intune baseline disables microphones and cameras at "
        "the OS level unless the user grants an explicit per-app permission.",
    ),
    status_q(M, "SC", "3.13.13", "SC.L2-3.13.13", "Mobile Code Control",
        SECTION_SC, 1,
        "Control and monitor the use of mobile code. Intune browser policies block "
        "unsigned ActiveX/Java; Microsoft Edge security mode is set to Strict; legacy "
        "browsers are not permitted on CUI endpoints.",
    ),
    status_q(M, "SC", "3.13.14", "SC.L2-3.13.14", "VoIP Control",
        SECTION_SC, 1,
        "Control and monitor the use of Voice over Internet Protocol (VoIP) technologies. "
        "Microsoft Teams carries all VoIP with Entra ID authentication and optional E2EE "
        "for sensitive calls; SIP to external numbers is blocked at the firewall.",
    ),
    status_q(M, "SC", "3.13.15", "SC.L2-3.13.15", "Communications Authenticity",
        SECTION_SC, 1,
        "Protect the authenticity of communications sessions. TLS certificates from "
        "trusted CAs with certificate pinning where supported; DKIM, DMARC, and SPF for "
        "email authenticity (M365 Exchange Online).",
    ),
    status_q(M, "SC", "3.13.16", "SC.L2-3.13.16", "Protect CUI at Rest",
        SECTION_SC, 1,
        "Protect the confidentiality of CUI at rest. BitLocker full-disk on laptops; "
        "M365 Purview DLP prevents CUI leakage; SharePoint is encrypted at rest in "
        "GCC High with FIPS-validated modules.",
    ),

    # ── SC.L2-3.13.11 follow-up (FIPS scope) ─────────────────────────────
    followup_q(
        module_num=M,
        family_abbrev="SC",
        nist_id="3.13.11",
        suffix="fips_scope",
        text="What encryption is used to protect CUI at rest and in transit?",
        options=[
            "FIPS 140-2/3 validated modules",
            "Standard encryption (not FIPS-validated)",
            "Partial encryption coverage",
            "No encryption",
        ],
        help_text=(
            "FIPS 140-2/3 validated encryption is required. Non-FIPS encryption results in "
            "partial scoring (-3). No encryption = -5."
        ),
        control_id="SC.L2-3.13.11",
        weight=5,
    ),
]


# Unique control IDs (the follow-up reuses 3.13.11)
_CONTROL_IDS = []
_seen = set()
for q in QUESTIONS:
    if q.control_id and q.control_id not in _seen:
        _seen.add(q.control_id)
        _CONTROL_IDS.append(q.control_id)


register_module(ModuleDefinition(
    number=M,
    name="System & Communications Protection",
    description="SC controls — boundary protection, segmentation, encryption, and session controls.",
    families=["SC"],
    control_ids=_CONTROL_IDS,
    doc_templates=["scope_package"],
    estimated_minutes=20,
    questions=QUESTIONS,
))
