"""
src/api/intake_modules/module3_cm_ia.py

Module 3 — Configuration Management (CM) + Identification & Authentication (IA).
20 primary CONTROL_STATUS questions (CM=9, IA=11) plus a conditional
follow-up on IA.L2-3.5.3 (MFA scope).
"""
from src.api.intake_modules import ModuleDefinition, register_module
from src.api.intake_modules._shared import status_q, followup_q


M = 3
SECTION_CM = "Configuration Management"
SECTION_IA = "Identification & Authentication"


QUESTIONS = [
    # ── CM ───────────────────────────────────────────────────────────────
    status_q(M, "CM", "3.4.1", "CM.L2-3.4.1", "Baseline Configuration",
        SECTION_CM, 5,
        "Maintain baseline configs and inventories of hardware, software, and firmware. "
        "Apex uses Intune compliance policies as the Windows 11 baseline and Defender "
        "Vulnerability Management for asset + software inventory; Palo Alto config is "
        "tracked in Panorama-equivalent version control.",
        high_weight_flag=True,
    ),
    status_q(M, "CM", "3.4.2", "CM.L2-3.4.2", "Security Configuration Enforcement",
        SECTION_CM, 5,
        "Enforce security configuration settings on IT products. Intune Security Baselines "
        "(Windows 11 + Edge) are deployed via Entra ID device groups; CrowdStrike prevention "
        "policies enforce endpoint hardening; Palo Alto config templates prevent drift.",
        high_weight_flag=True,
    ),
    status_q(M, "CM", "3.4.3", "CM.L2-3.4.3", "System Change Management",
        SECTION_CM, 1,
        "Track, review, approve or disapprove, and log changes to systems. A ticket tool "
        "(e.g., Jira/ServiceNow) owns change records; IaC changes require Azure DevOps PR "
        "approval from a second engineer before merge.",
    ),
    status_q(M, "CM", "3.4.4", "CM.L2-3.4.4", "Security Impact Analysis",
        SECTION_CM, 1,
        "Analyze the security impact of changes before implementation. Change tickets have a "
        "mandatory security-impact field reviewed by the ISSO during the approval step.",
    ),
    status_q(M, "CM", "3.4.5", "CM.L2-3.4.5", "Access Restrictions for Change",
        SECTION_CM, 3,
        "Define who can perform changes on systems, physical or logical. Entra PIM gates "
        "privileged role activation; Azure DevOps branch protection restricts production "
        "merges to the platform team group.",
    ),
    status_q(M, "CM", "3.4.6", "CM.L2-3.4.6", "Least Functionality",
        SECTION_CM, 1,
        "Employ the principle of least functionality — only essential capabilities. Intune "
        "policies disable unused Windows features; Palo Alto App-ID rules only allow "
        "applications required for business.",
    ),
    status_q(M, "CM", "3.4.7", "CM.L2-3.4.7", "Nonessential Functionality",
        SECTION_CM, 1,
        "Restrict, disable, or prevent use of nonessential programs, ports, and services. "
        "AppLocker rules via Intune block known-bad categories; Palo Alto PAN-OS filters "
        "non-business applications by category.",
    ),
    status_q(M, "CM", "3.4.8", "CM.L2-3.4.8", "Application Execution Policy",
        SECTION_CM, 1,
        "Apply deny-by-exception (blacklist) or permit-by-exception (whitelist) for software. "
        "Intune ASR rules plus CrowdStrike custom IOA blocks enforce denylists; "
        "allowlist is maintained for critical servers.",
    ),
    status_q(M, "CM", "3.4.9", "CM.L2-3.4.9", "User-Installed Software",
        SECTION_CM, 1,
        "Control and monitor user-installed software. Intune Company Portal serves the "
        "approved-app catalog; AppLocker blocks installers outside %ProgramFiles%; "
        "CrowdStrike maintains an installed-application inventory per endpoint.",
    ),

    # ── IA ───────────────────────────────────────────────────────────────
    status_q(M, "IA", "3.5.1", "IA.L2-3.5.1", "Identification",
        SECTION_IA, 5,
        "Identify users, processes acting on behalf of users, and devices. Entra ID is the "
        "identity plane with unique UPNs; Intune enrollment gives every managed device a "
        "unique Entra identity.",
        high_weight_flag=True,
    ),
    status_q(M, "IA", "3.5.2", "IA.L2-3.5.2", "Authentication",
        SECTION_IA, 5,
        "Authenticate users, processes, and devices as a prerequisite to access. Entra ID "
        "with password hash sync + Authenticator app (TOTP + push), certificate-based auth "
        "for Intune-joined devices.",
        high_weight_flag=True,
    ),
    status_q(M, "IA", "3.5.3", "IA.L2-3.5.3", "Multifactor Authentication",
        SECTION_IA, 3,
        "MFA for local and network access to privileged accounts, and for network access to "
        "non-privileged accounts. Apex uses Entra Conditional Access requiring MFA for all "
        "cloud apps; Palo Alto GlobalProtect uses SAML to Entra so VPN inherits MFA.",
    ),
    status_q(M, "IA", "3.5.4", "IA.L2-3.5.4", "Replay-Resistant Authentication",
        SECTION_IA, 1,
        "Replay-resistant authentication for network access to privileged and non-privileged "
        "accounts. Entra ID uses time-bound TOTP / push + Kerberos-with-AES where AD is in "
        "play; NTLMv1 is disabled.",
    ),
    status_q(M, "IA", "3.5.5", "IA.L2-3.5.5", "Identifier Reuse",
        SECTION_IA, 1,
        "Prevent reuse of identifiers for a defined period. Entra ID UPNs are HR-driven and "
        "retired accounts are soft-deleted; reassignment requires an ISSO override.",
    ),
    status_q(M, "IA", "3.5.6", "IA.L2-3.5.6", "Identifier Management",
        SECTION_IA, 1,
        "Disable identifiers after a defined period of inactivity. Entra ID lifecycle "
        "workflow disables accounts after 90 days inactive; documented offboarding playbook "
        "disables on Day 0 of separation.",
    ),
    status_q(M, "IA", "3.5.7", "IA.L2-3.5.7", "Password Complexity",
        SECTION_IA, 1,
        "Enforce a minimum password complexity and change of characters when new passwords "
        "are created. Entra password protection + MS banned-password list; Entra ID "
        "Protection flags risky sign-ins and forces reset.",
    ),
    status_q(M, "IA", "3.5.8", "IA.L2-3.5.8", "Password Reuse",
        SECTION_IA, 1,
        "Prohibit password reuse for a defined number of generations. On-prem AD "
        "(if present) enforces 24 generations; Entra steers users toward passwordless "
        "(FIDO2) so reuse is mostly eliminated.",
    ),
    status_q(M, "IA", "3.5.9", "IA.L2-3.5.9", "Temporary Passwords",
        SECTION_IA, 1,
        "Allow temporary passwords for system logons that must be changed immediately to a "
        "permanent password. Entra SSPR workflow forces password change on first use; "
        "temp access passes expire within 1 hour.",
    ),
    status_q(M, "IA", "3.5.10", "IA.L2-3.5.10", "Cryptographic Password Storage",
        SECTION_IA, 1,
        "Store and transmit only cryptographically-protected passwords. Entra ID stores "
        "hashed/salted credentials; TLS 1.2+ for all M365 endpoints; application secrets "
        "live in Azure Key Vault, never in code.",
    ),
    status_q(M, "IA", "3.5.11", "IA.L2-3.5.11", "Obscure Feedback",
        SECTION_IA, 1,
        "Obscure feedback of authentication information. Windows Hello / Entra login prompts "
        "mask password entry by default; no custom auth UI is used.",
    ),

    # ── IA.L2-3.5.3 follow-up (MFA scope) ────────────────────────────────
    followup_q(
        module_num=M,
        family_abbrev="IA",
        nist_id="3.5.3",
        suffix="mfa_scope",
        text="Where is MFA enforced in your environment?",
        options=[
            "All users and access methods",
            "Remote access and privileged accounts only",
            "Remote access only",
            "Not implemented",
        ],
        help_text=(
            "MFA scope affects SPRS scoring: full enforcement = MET (0 deduction), "
            "remote+privileged only = partial (-3), none = NOT MET (-5)."
        ),
        control_id="IA.L2-3.5.3",
        weight=5,
    ),
]


# All control IDs except the MFA-scope follow-up (which already covers 3.5.3)
_CONTROL_IDS = []
_seen = set()
for q in QUESTIONS:
    if q.control_id and q.control_id not in _seen:
        _seen.add(q.control_id)
        _CONTROL_IDS.append(q.control_id)


register_module(ModuleDefinition(
    number=M,
    name="Configuration Management + Identification & Authentication",
    description="CM and IA control families — hardening baselines, change control, identity and MFA.",
    families=["CM", "IA"],
    control_ids=_CONTROL_IDS,
    doc_templates=["cm_plan"],
    estimated_minutes=20,
    questions=QUESTIONS,
))
