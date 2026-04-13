"""
src/api/intake_modules/module1_ac.py

Module 1 — Access Control (AC). 28 questions across 5 sections covering
22 NIST 800-171 AC controls (3.1.1 through 3.1.22). Migrated verbatim
from src/api/intake_module1.py. IDs, text, options, branching and
control_id linkage are preserved exactly.
"""
from src.api.intake_modules import (
    IntakeQuestion,
    ModuleDefinition,
    QuestionTier,
    QuestionType,
    register_module,
)


SECTION_ACCT = "account_management"
SECTION_LOGIN = "login_session"
SECTION_REMOTE = "remote_access"
SECTION_WIRELESS = "wireless_mobile"
SECTION_EXT = "external_cui_flow"


def _q(
    qid: str,
    section: str,
    control_ids: list,
    text: str,
    answer_type: str,
    options: list,
    help_text: str,
    branching: dict = None,
) -> IntakeQuestion:
    """Compact constructor for the Module 1 questions — they all share the
    same shape so this keeps the listing readable."""
    return IntakeQuestion(
        id=qid,
        text=text,
        question_type=answer_type,
        tier=QuestionTier.CONTROL_STATUS,
        section=section,
        required=True,
        help_text=help_text,
        options=options,
        control_ids=list(control_ids),
        control_id=control_ids[0] if control_ids else None,
        metadata={"branching": branching} if branching else {},
    )


QUESTIONS = [
    # ── SECTION 1: account_management (3.1.1, 3.1.2, 3.1.4–3.1.7) ────────
    _q(
        "m1_q01", SECTION_ACCT, ["AC.L2-3.1.1"],
        "How are user accounts created and approved for systems that store or process CUI?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "formal_process", "label": "Formal request and approval process (e.g., ticketing system, manager sign-off)", "gap": False},
            {"value": "manager_email", "label": "Manager sends email or verbal request to IT", "gap": False},
            {"value": "it_creates_as_needed", "label": "IT creates accounts as needed without formal approval", "gap": True, "severity": "HIGH"},
            {"value": "self_service", "label": "Users can self-register or create their own accounts", "gap": True, "severity": "CRITICAL"},
        ],
        "NIST 800-171 requires that only authorized users, processes, and devices have access to CUI systems. Assessors will look for documented account provisioning procedures and approval records.",
        branching={"self_service": {"alert": "Self-service account creation on CUI systems violates AC.L2-3.1.1. All accounts must be authorized."}},
    ),
    _q(
        "m1_q02", SECTION_ACCT, ["AC.L2-3.1.1"],
        "How often are user accounts reviewed to verify they are still needed?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "quarterly", "label": "Quarterly or more frequently", "gap": False},
            {"value": "semiannual", "label": "Every 6 months", "gap": False},
            {"value": "annual", "label": "Annually", "gap": False},
            {"value": "no_review", "label": "No regular account reviews", "gap": True, "severity": "HIGH"},
        ],
        "Regular access reviews ensure terminated or transferred employees no longer have access. Assessors expect documented evidence of periodic reviews with sign-off.",
    ),
    _q(
        "m1_q03", SECTION_ACCT, ["AC.L2-3.1.1", "AC.L2-3.1.2"],
        "What happens to a user's account when they leave the company or change roles?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "same_day_disable", "label": "Account disabled same day, access reviewed within 24 hours", "gap": False},
            {"value": "within_week", "label": "Account disabled within a few business days", "gap": False},
            {"value": "eventually", "label": "Account disabled eventually when someone remembers", "gap": True, "severity": "HIGH"},
            {"value": "no_process", "label": "No formal offboarding process exists", "gap": True, "severity": "CRITICAL"},
        ],
        "Timely account deprovisioning is one of the most commonly failed controls in CMMC assessments. Assessors will ask to see offboarding records for recent departures.",
        branching={"no_process": {"alert": "Missing offboarding process means former employees may retain CUI access. Critical gap for 3.1.1 and 3.1.2."}},
    ),
    _q(
        "m1_q04", SECTION_ACCT, ["AC.L2-3.1.2"],
        "How do you control what each user can do on CUI systems (role-based access, permissions)?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "rbac_enforced", "label": "Role-based access control (RBAC) with defined roles and permissions", "gap": False},
            {"value": "ad_groups", "label": "Active Directory / Entra ID security groups control access to resources", "gap": False},
            {"value": "per_user_manual", "label": "Permissions set individually per user, managed manually", "gap": False},
            {"value": "everyone_admin", "label": "Most users have the same broad access or admin rights", "gap": True, "severity": "CRITICAL"},
        ],
        "Assessors verify that users can only perform transactions and functions they are specifically authorized for. RBAC through your identity provider is the cleanest evidence.",
        branching={"everyone_admin": {"alert": "Broad admin access violates least privilege (3.1.5) and function-based restrictions (3.1.2). Immediate remediation needed."}},
    ),
    _q(
        "m1_q05", SECTION_ACCT, ["AC.L2-3.1.4"],
        "Are duties separated so that no single person can perform all critical steps of a sensitive process (e.g., the person who approves access is different from the person who provisions it)?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "yes_documented", "label": "Yes, separation of duties is documented and enforced", "gap": False},
            {"value": "yes_informal", "label": "Yes, in practice different people handle different steps, but not formally documented", "gap": False},
            {"value": "partial", "label": "For some processes but not all", "gap": True, "severity": "MEDIUM"},
            {"value": "no_separation", "label": "No — one person can approve and execute sensitive actions", "gap": True, "severity": "MEDIUM"},
        ],
        "For a small company, perfect separation of duties is challenging. The key is documenting which duties are separated and where compensating controls (like audit logging) are used. This is a 1-point control.",
    ),
    _q(
        "m1_q06", SECTION_ACCT, ["AC.L2-3.1.5"],
        "How are privileged accounts (domain admin, root, system admin) managed?",
        QuestionType.MULTI_CHOICE,
        [
            {"value": "named_admins", "label": "Each admin has a named privileged account (not shared)", "gap": False},
            {"value": "pam_tool", "label": "Privileged access management (PAM) tool controls admin credentials", "gap": False},
            {"value": "limited_admins", "label": "Admin access is limited to a small number of IT staff", "gap": False},
            {"value": "shared_admin", "label": "Admin credentials are shared among IT staff", "gap": True, "severity": "HIGH"},
        ],
        "Least privilege means privileged access is only granted when necessary and individually attributable. Assessors will ask who has admin access and how it is tracked.",
        branching={"shared_admin": {"alert": "Shared admin accounts prevent individual accountability. Each admin needs a unique privileged account under 3.1.5."}},
    ),
    _q(
        "m1_q07", SECTION_ACCT, ["AC.L2-3.1.6"],
        "Do administrators use separate non-privileged accounts for daily tasks like email, web browsing, and document editing?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "yes_separate", "label": "Yes — admins have a standard account for daily work and a separate admin account", "gap": False},
            {"value": "yes_but_inconsistent", "label": "Policy exists but not consistently followed", "gap": True, "severity": "HIGH"},
            {"value": "no_same_account", "label": "No — admins use their admin account for everything", "gap": True, "severity": "HIGH"},
        ],
        "Using admin accounts for email and web browsing dramatically increases attack surface. Assessors specifically check whether admin accounts are used for non-security functions.",
    ),
    _q(
        "m1_q08", SECTION_ACCT, ["AC.L2-3.1.7"],
        "Can standard (non-admin) users install software, change system settings, or disable security tools?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "no_prevented", "label": "No — these actions require admin credentials and are logged", "gap": False},
            {"value": "partially_restricted", "label": "Some restrictions in place but users can install certain software", "gap": True, "severity": "MEDIUM"},
            {"value": "yes_local_admin", "label": "Yes — users have local admin rights on their workstations", "gap": True, "severity": "CRITICAL"},
        ],
        "Standard users must not be able to execute privileged functions. When they attempt to, the system should deny the action and log the attempt. Local admin rights on CUI endpoints is a common audit failure.",
        branching={"yes_local_admin": {"alert": "Local admin rights allow users to disable security tools, install malware, and bypass controls. Critical gap affecting multiple control families."}},
    ),

    # ── SECTION 2: login_session (3.1.8, 3.1.9, 3.1.10, 3.1.11) ──────────
    _q(
        "m1_q09", SECTION_LOGIN, ["AC.L2-3.1.8"],
        "What happens after multiple failed login attempts?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "lockout_configured", "label": "Account locks out after a set number of failures (e.g., 3-5 attempts)", "gap": False},
            {"value": "increasing_delay", "label": "Progressive delays between attempts (throttling)", "gap": False},
            {"value": "alert_only", "label": "Alert is generated but no lockout", "gap": True, "severity": "MEDIUM"},
            {"value": "nothing", "label": "No lockout or rate limiting configured", "gap": True, "severity": "HIGH"},
        ],
        "Account lockout policies are directly testable by assessors. Common settings: 3-5 attempts, 15-30 minute lockout. This applies to all CUI system authentication points.",
    ),
    _q(
        "m1_q10", SECTION_LOGIN, ["AC.L2-3.1.8"],
        "Where is the account lockout policy enforced?",
        QuestionType.MULTI_CHOICE,
        [
            {"value": "domain_gpo", "label": "Active Directory / Entra ID (domain-level GPO or conditional access)", "gap": False},
            {"value": "vpn_gateway", "label": "VPN gateway / remote access portal", "gap": False},
            {"value": "local_workstation", "label": "Local workstation security policy", "gap": False},
            {"value": "cloud_apps", "label": "Cloud applications (M365, line-of-business apps)", "gap": False},
        ],
        "Lockout policy must be enforced at every authentication point for CUI systems. Assessors may test multiple entry points — don't forget VPN, cloud apps, and local logon.",
    ),
    _q(
        "m1_q11", SECTION_LOGIN, ["AC.L2-3.1.9"],
        "Do CUI systems display a login banner or notice before granting access?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "yes_banner", "label": "Yes — a banner warns about authorized use, monitoring, and consent", "gap": False},
            {"value": "generic_banner", "label": "There is a banner but it does not mention CUI or monitoring", "gap": True, "severity": "MEDIUM"},
            {"value": "no_banner", "label": "No login banner is displayed", "gap": True, "severity": "MEDIUM"},
        ],
        "The banner must notify users that the system processes CUI, that usage may be monitored, and that unauthorized use is prohibited. This is a 1-point control but easy to implement and commonly checked.",
    ),
    _q(
        "m1_q12", SECTION_LOGIN, ["AC.L2-3.1.10"],
        "Do CUI workstations and systems lock after a period of inactivity?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "yes_15_or_less", "label": "Yes — screen locks after 15 minutes or less with pattern-hiding display", "gap": False},
            {"value": "yes_longer", "label": "Yes — but timeout is longer than 15 minutes", "gap": True, "severity": "MEDIUM"},
            {"value": "user_discretion", "label": "Users are expected to lock manually but no auto-lock is enforced", "gap": True, "severity": "HIGH"},
            {"value": "no_session_lock", "label": "No session lock configured", "gap": True, "severity": "HIGH"},
        ],
        "Session lock must activate automatically after inactivity AND hide screen content (screensaver or lock screen). 15 minutes is the typical threshold. Enforced via GPO or MDM, not user configuration.",
    ),
    _q(
        "m1_q13", SECTION_LOGIN, ["AC.L2-3.1.11"],
        "Are user sessions automatically terminated after a defined condition (e.g., end of business day, extended inactivity, or connection timeout)?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "yes_policy_enforced", "label": "Yes — sessions auto-terminate based on defined timeout or conditions", "gap": False},
            {"value": "vpn_timeout_only", "label": "VPN sessions timeout, but local sessions persist indefinitely", "gap": True, "severity": "MEDIUM"},
            {"value": "no_termination", "label": "No automatic session termination — sessions persist until user logs off", "gap": True, "severity": "MEDIUM"},
        ],
        "This is different from session lock (3.1.10). Session termination actually ends the session, requiring re-authentication. Think VPN timeouts, RDP disconnects, and idle web session expiry.",
    ),

    # ── SECTION 3: remote_access (3.1.12, 3.1.13, 3.1.14, 3.1.15) ────────
    _q(
        "m1_q14", SECTION_REMOTE, ["AC.L2-3.1.12", "AC.L2-3.1.14"],
        "How do remote workers connect to internal systems that store or process CUI?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "vpn_always_on", "label": "Always-on VPN with MFA", "gap": False},
            {"value": "vpn_manual", "label": "Manual VPN connection with MFA", "gap": False},
            {"value": "vpn_no_mfa", "label": "VPN without MFA", "gap": True, "severity": "CRITICAL"},
            {"value": "rdp_direct", "label": "Direct RDP/SSH without VPN", "gap": True, "severity": "CRITICAL"},
            {"value": "no_remote", "label": "No remote access permitted — all work is on-site only", "gap": False},
        ],
        "NIST 800-171 requires all remote access sessions to be monitored, controlled, encrypted, and routed through managed access control points. A VPN concentrator with MFA is the standard approach.",
        branching={
            "vpn_no_mfa": {"alert": "MFA is required for all remote access to CUI systems under AC.L2-3.1.12 and IA.L2-3.5.3."},
            "rdp_direct": {"alert": "Direct RDP/SSH exposure without VPN violates 3.1.14 (managed access control points) and 3.1.13 (encrypted sessions). Critical finding."},
            "no_remote": {"skip_to": "m1_q19"},
        },
    ),
    _q(
        "m1_q15", SECTION_REMOTE, ["AC.L2-3.1.12"],
        "How is remote access activity monitored?",
        QuestionType.MULTI_CHOICE,
        [
            {"value": "vpn_logs_siem", "label": "VPN logs forwarded to SIEM for monitoring and alerting", "gap": False},
            {"value": "vpn_logs_reviewed", "label": "VPN connection logs reviewed periodically", "gap": False},
            {"value": "connection_alerts", "label": "Alerts on unusual remote access patterns (off-hours, new locations)", "gap": False},
            {"value": "no_monitoring", "label": "Remote access is not specifically monitored", "gap": True, "severity": "HIGH"},
        ],
        "Monitoring means more than just having logs exist. Assessors want to see that remote access events are reviewed and that anomalies would be detected.",
    ),
    _q(
        "m1_q16", SECTION_REMOTE, ["AC.L2-3.1.13"],
        "What encryption is used for remote access sessions?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "fips_validated", "label": "FIPS 140-2/140-3 validated cryptographic modules (e.g., IKEv2/IPsec, TLS 1.2+)", "gap": False},
            {"value": "strong_crypto", "label": "Strong encryption (AES-256, TLS 1.2+) but not FIPS-validated", "gap": False},
            {"value": "unknown", "label": "Not sure what encryption the VPN uses", "gap": True, "severity": "MEDIUM"},
            {"value": "weak_or_none", "label": "Weak encryption or unencrypted connections are possible", "gap": True, "severity": "CRITICAL"},
        ],
        "Remote access sessions must use cryptographic mechanisms to protect confidentiality. FIPS-validated crypto is ideal for CMMC but strong encryption (TLS 1.2+, AES-256) meets the minimum bar. Assessors may verify VPN configuration directly.",
    ),
    _q(
        "m1_q17", SECTION_REMOTE, ["AC.L2-3.1.14"],
        "How many remote access entry points exist (VPN concentrators, remote desktop gateways, web portals)?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "single_point", "label": "One managed access point (single VPN gateway or portal)", "gap": False},
            {"value": "few_managed", "label": "A few access points, all centrally managed and monitored", "gap": False},
            {"value": "multiple_unmanaged", "label": "Multiple entry points, some not centrally managed", "gap": True, "severity": "HIGH"},
            {"value": "unknown", "label": "Not sure how many remote access paths exist", "gap": True, "severity": "HIGH"},
        ],
        "All remote access must be routed through a limited number of managed access control points. Shadow IT remote access tools (TeamViewer, AnyDesk) that bypass the VPN are a common finding.",
    ),
    _q(
        "m1_q18", SECTION_REMOTE, ["AC.L2-3.1.15"],
        "Can administrators perform privileged actions (server administration, firewall changes, domain admin tasks) remotely?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "yes_authorized_documented", "label": "Yes — specific administrators are authorized in writing for remote privileged access", "gap": False},
            {"value": "yes_vpn_only", "label": "Yes — but only through VPN, not documented who is authorized", "gap": True, "severity": "MEDIUM"},
            {"value": "yes_unrestricted", "label": "Yes — any admin can do anything remotely without additional authorization", "gap": True, "severity": "HIGH"},
            {"value": "no_onsite_only", "label": "No — privileged administration is only performed on-site", "gap": False},
        ],
        "Remote execution of privileged commands and access to security-relevant information must be explicitly authorized. The authorization should document who, what systems, and what actions are permitted.",
    ),

    # ── SECTION 4: wireless_mobile (3.1.16, 3.1.17, 3.1.18, 3.1.19) ──────
    _q(
        "m1_q19", SECTION_WIRELESS, ["AC.L2-3.1.16", "AC.L2-3.1.17"],
        "Does your office environment have wireless (Wi-Fi) networks?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "yes_managed", "label": "Yes — managed corporate Wi-Fi with WPA3 or WPA2-Enterprise (802.1X)", "gap": False},
            {"value": "yes_wpa2_psk", "label": "Yes — WPA2 with a pre-shared key (password)", "gap": True, "severity": "MEDIUM"},
            {"value": "yes_open_or_weak", "label": "Yes — open network or WEP/WPA1 encryption", "gap": True, "severity": "CRITICAL"},
            {"value": "no_wireless", "label": "No wireless networks — wired only", "gap": False},
        ],
        "Wireless access must be authorized before allowing connections (3.1.16) and protected using authentication and encryption (3.1.17). WPA2-Enterprise with RADIUS/802.1X is the gold standard.",
        branching={
            "no_wireless": {"skip_to": "m1_q22"},
            "yes_open_or_weak": {"alert": "Open or weakly encrypted wireless on a CUI network is a critical finding. WPA2-Enterprise or WPA3 is required under 3.1.17."},
        },
    ),
    _q(
        "m1_q20", SECTION_WIRELESS, ["AC.L2-3.1.16"],
        "Is the wireless network segmented from the CUI network?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "yes_segmented", "label": "Yes — wireless is on a separate VLAN with firewall rules restricting CUI access", "gap": False},
            {"value": "yes_guest_separate", "label": "Guest Wi-Fi is separate, but corporate Wi-Fi is on the same network as CUI systems", "gap": True, "severity": "MEDIUM"},
            {"value": "no_flat_network", "label": "No segmentation — wireless and wired share the same network", "gap": True, "severity": "HIGH"},
        ],
        "Even with strong wireless encryption, network segmentation limits what wireless clients can reach. If CUI systems are on the same flat network as Wi-Fi, a compromised wireless device has direct access.",
    ),
    _q(
        "m1_q21", SECTION_WIRELESS, ["AC.L2-3.1.16", "AC.L2-3.1.17"],
        "How do you detect and handle unauthorized wireless access points (rogue APs)?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "wids_active", "label": "Wireless intrusion detection (WIDS) or access point management actively scans for rogues", "gap": False},
            {"value": "periodic_scan", "label": "Periodic manual scans or physical inspections for unauthorized APs", "gap": False},
            {"value": "no_detection", "label": "No rogue AP detection in place", "gap": True, "severity": "MEDIUM"},
        ],
        "Unauthorized access points can bypass network security. Most enterprise wireless controllers include rogue AP detection. For smaller environments, periodic scanning with a tool like NetSpot or Kismet demonstrates due diligence.",
    ),
    _q(
        "m1_q22", SECTION_WIRELESS, ["AC.L2-3.1.18"],
        "Are employees permitted to use mobile devices (phones, tablets) to access CUI or CUI systems?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "yes_managed_mdm", "label": "Yes — company-managed devices enrolled in MDM (Intune, JAMF, etc.)", "gap": False},
            {"value": "yes_byod_managed", "label": "Yes — personal devices with MDM enrollment or containerized access (e.g., Intune MAM)", "gap": False},
            {"value": "yes_unmanaged", "label": "Yes — personal devices without management or security controls", "gap": True, "severity": "CRITICAL"},
            {"value": "no_mobile", "label": "No — mobile devices cannot access CUI systems", "gap": False},
        ],
        "Mobile device connections to CUI systems must be controlled. This typically means MDM enrollment with enforced policies: PIN/biometric, encryption, remote wipe capability.",
        branching={
            "no_mobile": {"skip_to": "m1_q24"},
            "yes_unmanaged": {"alert": "Unmanaged mobile devices accessing CUI violate 3.1.18 (mobile device control) and 3.1.19 (CUI encryption on mobile). MDM or MAM enrollment is required."},
        },
    ),
    _q(
        "m1_q23", SECTION_WIRELESS, ["AC.L2-3.1.19"],
        "Is CUI encrypted on mobile devices?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "yes_device_encryption", "label": "Yes — full device encryption enforced via MDM (BitLocker, FileVault, iOS/Android native)", "gap": False},
            {"value": "yes_container_only", "label": "Yes — CUI is only accessible in an encrypted container (Intune MAM, managed apps)", "gap": False},
            {"value": "no_encryption", "label": "No encryption enforced on mobile devices", "gap": True, "severity": "HIGH"},
        ],
        "CUI stored on or accessible from mobile devices must be encrypted. Modern iOS and Android devices encrypt by default when a passcode is set, but this must be enforced via policy, not left to user choice.",
    ),

    # ── SECTION 5: external_cui_flow (3.1.3, 3.1.20, 3.1.21, 3.1.22) ─────
    _q(
        "m1_q24", SECTION_EXT, ["AC.L2-3.1.3"],
        "How do you control where CUI can flow within and outside your network?",
        QuestionType.MULTI_CHOICE,
        [
            {"value": "dlp_policies", "label": "Data Loss Prevention (DLP) policies in M365 or email gateway", "gap": False},
            {"value": "sensitivity_labels", "label": "Sensitivity labels / classification markings on CUI documents", "gap": False},
            {"value": "network_segmentation", "label": "Network segmentation (CUI systems on separate VLAN/subnet)", "gap": False},
            {"value": "firewall_rules", "label": "Firewall rules restricting CUI system traffic to approved destinations", "gap": False},
            {"value": "no_controls", "label": "No specific controls on CUI data flow", "gap": True, "severity": "CRITICAL"},
        ],
        "CUI flow control means ensuring CUI only moves through approved channels. The combination of network segmentation, DLP, and sensitivity labels provides layered protection. Assessors will ask how you prevent CUI from being emailed to personal accounts or copied to unapproved storage.",
        branching={"no_controls": {"alert": "CUI flow control (3.1.3) is a 5-point control. Without DLP, segmentation, or labeling, CUI can be exfiltrated without detection."}},
    ),
    _q(
        "m1_q25", SECTION_EXT, ["AC.L2-3.1.3"],
        "Can users send CUI to personal email accounts, personal cloud storage (Dropbox, Google Drive), or USB drives?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "blocked_all", "label": "All three are blocked by policy and technical controls", "gap": False},
            {"value": "some_blocked", "label": "Some are blocked but not all (e.g., USB blocked but personal email not)", "gap": True, "severity": "HIGH"},
            {"value": "policy_only", "label": "Policy prohibits it but no technical enforcement", "gap": True, "severity": "HIGH"},
            {"value": "not_restricted", "label": "No restrictions on where users can send CUI", "gap": True, "severity": "CRITICAL"},
        ],
        "Policy alone is not sufficient — assessors look for technical enforcement. Common controls: M365 DLP blocking external sharing, USB port disablement via GPO/MDM, web content filtering blocking personal cloud storage.",
    ),
    _q(
        "m1_q26", SECTION_EXT, ["AC.L2-3.1.20"],
        "How do you control connections between your CUI environment and external systems (customer portals, subcontractor networks, SaaS applications)?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "approved_list", "label": "Approved list of external systems with documented security requirements and review", "gap": False},
            {"value": "firewall_controlled", "label": "Firewall rules limit outbound connections but no formal approval process", "gap": True, "severity": "MEDIUM"},
            {"value": "unrestricted", "label": "No restrictions on external system connections", "gap": True, "severity": "HIGH"},
        ],
        "External information systems include any system not under your direct control. Assessors check that you verify external systems meet security requirements before allowing connections, especially if CUI is transmitted.",
    ),
    _q(
        "m1_q27", SECTION_EXT, ["AC.L2-3.1.21"],
        "Are employees allowed to use company-owned portable storage (USB drives, external hard drives) on non-company systems?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "prohibited_enforced", "label": "Prohibited by policy and reinforced through training", "gap": False},
            {"value": "encrypted_allowed", "label": "Allowed only with encrypted, company-approved devices", "gap": False},
            {"value": "no_policy", "label": "No policy or restrictions on portable storage use", "gap": True, "severity": "MEDIUM"},
        ],
        "This control limits the use of organization-controlled portable storage on external systems. If an employee plugs a company USB drive into a home computer, any CUI on that drive is now on an uncontrolled system.",
    ),
    _q(
        "m1_q28", SECTION_EXT, ["AC.L2-3.1.22"],
        "Do you have any publicly accessible systems (public website, public-facing portals, marketing servers) that are part of or connected to your CUI environment?",
        QuestionType.SINGLE_CHOICE,
        [
            {"value": "no_public_systems", "label": "No — public-facing systems are completely separated from CUI environment", "gap": False},
            {"value": "yes_separated", "label": "Yes — but public systems are in a DMZ with no direct access to CUI", "gap": False},
            {"value": "yes_connected", "label": "Yes — public systems share the network or have access to CUI systems", "gap": True, "severity": "CRITICAL"},
        ],
        "CUI must not be posted or processed on publicly accessible systems. If public-facing systems exist, they must be isolated from the CUI environment. Assessors will verify network architecture diagrams and firewall rules.",
        branching={"yes_connected": {"alert": "Publicly accessible systems connected to CUI systems create a direct attack path. Immediate segmentation required under 3.1.22."}},
    ),
]


# Derive AC control IDs from the questions (preserves source of truth).
_AC_CONTROLS = sorted({cid for q in QUESTIONS for cid in q.control_ids})


register_module(ModuleDefinition(
    number=1,
    name="Access Control",
    description="22 NIST 800-171 Access Control requirements — account management, session controls, remote access, wireless/mobile, and CUI flow control.",
    families=["AC"],
    control_ids=_AC_CONTROLS,
    doc_templates=["policy_manual"],
    estimated_minutes=20,
    questions=QUESTIONS,
))
