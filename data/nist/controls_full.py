"""
NIST SP 800-171 Rev 2 — All 110 CUI Security Requirements
Mapped to CMMC Level 2 control IDs with SPRS point weights.

Source: NIST SP 800-171 Rev 2 (Feb 2020, updated Jan 2021)
        DoD Assessment Methodology v1.2.1
        CMMC Level 2 Scoping Guide

SPRS Scoring: Start at 110, subtract weight for each NOT MET control.
  - 5-point controls: Most critical (11 controls)
  - 3-point controls: Important (22 controls)
  - 1-point controls: Standard (77 controls)
  - Floor: -203

POA&M eligibility: "yes" = can be on POA&M, "no" = cannot (must be MET),
  "conditional" = only if certain conditions apply.
  SSP-related controls (3.12.4) cannot be POA&M'd.
"""

NIST_800_171_CONTROLS = [
    # =========================================================================
    # 3.1 ACCESS CONTROL (AC) — 22 requirements
    # =========================================================================
    {
        "id": "AC.L2-3.1.1",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.1",
        "title": "Authorized Access Control",
        "description": "Limit system access to authorized users, processes acting on behalf of authorized users, and devices (including other systems).",
        "discussion": "Access control policies control access between active entities or subjects and passive entities or objects in systems. Access enforcement mechanisms can be employed at the application and service level to provide increased information security. Other systems include systems internal and external to the organization. This requirement focuses on account management for systems and applications. The definition of and enforcement of access authorizations, other than those determined by account type, are addressed in requirement 3.1.2.",
        "points": 5,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.2",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.2",
        "title": "Transaction & Function Control",
        "description": "Limit system access to the types of transactions and functions that authorized users are permitted to execute.",
        "discussion": "Organizations may choose to define access privileges or other attributes by account, by type of account, or a combination of both. System account types include individual, shared, group, system, guest, anonymous, emergency, developer, manufacturer, vendor, and temporary. Other attributes required for authorizing access include restrictions on time-of-day, day-of-week, and point-of-origin. In defining other account attributes, organizations consider system-related requirements and applicability of such requirements to specific organizational systems.",
        "points": 5,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.3",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.3",
        "title": "Control CUI Flow",
        "description": "Control the flow of CUI in accordance with approved authorizations.",
        "discussion": "Information flow control regulates where CUI can travel within a system and between systems. Flow control restrictions include keeping CUI from being transmitted in the clear to the internet, blocking outside traffic that claims to be from within the organization, restricting requests to the internet that are not from the internal web proxy server, and limiting information transfers between organizations based on data structures and content.",
        "points": 3,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.4",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.4",
        "title": "Separation of Duties",
        "description": "Separate the duties of individuals to reduce the risk of malevolent activity without collusion.",
        "discussion": "Separation of duties addresses the potential for abuse of authorized privileges and helps to reduce the risk of malevolent activity without collusion. Separation of duties includes dividing mission functions and system support functions among different individuals or roles; conducting system support functions with different individuals; and ensuring that security personnel administering access control functions do not also administer audit functions.",
        "points": 3,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.5",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.5",
        "title": "Least Privilege",
        "description": "Employ the principle of least privilege, including for specific security functions and privileged accounts.",
        "discussion": "Organizations employ the principle of least privilege for specific duties and authorized accesses for users and processes. The principle of least privilege is applied with the goal of authorized privileges no higher than necessary to accomplish required organizational missions or business functions. Organizations consider the creation of additional processes, roles, and system accounts as necessary to achieve least privilege.",
        "points": 3,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.6",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.6",
        "title": "Non-Privileged Account Use",
        "description": "Use non-privileged accounts or roles when accessing nonsecurity functions.",
        "discussion": "This requirement limits exposure when operating from within privileged accounts or roles. The inclusion of roles addresses situations where organizations implement access control policies such as role-based access control and where a change of role provides the same degree of assurance in the change of access authorizations for the user and the processes acting on behalf of the user as would be provided by a change between a privileged and non-privileged account.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.7",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.7",
        "title": "Privileged Functions",
        "description": "Prevent non-privileged users from executing privileged functions and capture the execution of such functions in audit logs.",
        "discussion": "Privileged functions include establishing system accounts, performing system integrity checks, conducting patching operations, or administering cryptographic key management activities. Non-privileged users are individuals that do not possess appropriate authorizations. Circumventing intrusion detection and prevention mechanisms or malicious code protection mechanisms are examples of privileged functions that require protection from non-privileged users.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.8",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.8",
        "title": "Unsuccessful Logon Attempts",
        "description": "Limit unsuccessful logon attempts.",
        "discussion": "This requirement applies regardless of whether the logon occurs via a local or network connection. Due to the potential for denial of service, automatic lockouts initiated by systems are usually temporary and automatically release after a predetermined period established by the organization.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.9",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.9",
        "title": "Privacy & Security Notices",
        "description": "Provide privacy and security notices consistent with applicable CUI rules.",
        "discussion": "System use notifications can be implemented using messages or warning banners displayed before individuals log in to organizational systems. System use notifications are used only for access via logon interfaces with human users and are not required when human interfaces do not exist.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.10",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.10",
        "title": "Session Lock",
        "description": "Use session lock with pattern-hiding displays to prevent access and viewing of data after a period of inactivity.",
        "discussion": "Session locks are temporary actions taken when users stop work and move away from the immediate vicinity of the system but do not want to log out because of the temporary nature of their absences. Session locks are implemented where session activities can be determined, typically at the operating system level.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.11",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.11",
        "title": "Session Termination",
        "description": "Terminate (automatically) a user session after a defined condition.",
        "discussion": "This requirement addresses the termination of user-initiated logical sessions in contrast to the termination of network connections that are associated with communications sessions. A logical session (for local, network, and remote access) is initiated whenever a user accesses an organizational system. Such user sessions can be terminated without terminating network sessions. Session termination terminates all processes associated with a user's logical session except those processes that are specifically created by the user to continue after the session is terminated.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.12",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.12",
        "title": "Control Remote Access",
        "description": "Monitor and control remote access sessions.",
        "discussion": "Remote access is access to organizational systems by users communicating through external networks. Remote access methods include dial-up, broadband, and wireless. Organizations can restrict the use of remote access methods. Monitoring and controlling of remote access involves automated mechanisms and also examining audit logs.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.13",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.13",
        "title": "Remote Access Confidentiality",
        "description": "Employ cryptographic mechanisms to protect the confidentiality of remote access sessions.",
        "discussion": "Cryptographic standards include FIPS-validated cryptography and NSA-approved cryptography.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.14",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.14",
        "title": "Remote Access Routing",
        "description": "Route remote access via managed access control points.",
        "discussion": "Routing remote access through managed access control points enhances explicit, organizational control over such connections, reducing the susceptibility to unauthorized access to organizational systems resulting in the unauthorized disclosure of CUI.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.15",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.15",
        "title": "Privileged Remote Access",
        "description": "Authorize remote execution of privileged commands and remote access to security-relevant information.",
        "discussion": "A privileged command is a human-initiated command executed on a system that involves the control, monitoring, or administration of the system including security functions and associated security-relevant information.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.16",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.16",
        "title": "Wireless Access Authorization",
        "description": "Authorize wireless access prior to allowing such connections.",
        "discussion": "Establishing usage restrictions and configuration/connection requirements for wireless access to the system provides criteria for organizations to support wireless access authorization decisions. Such restrictions and requirements reduce the susceptibility to unauthorized access to the system through wireless technologies.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.17",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.17",
        "title": "Wireless Access Protection",
        "description": "Protect wireless access using authentication and encryption.",
        "discussion": "Organizations authenticate individuals and devices to help protect wireless access to the system. Special attention is given to the wide variety of devices that are part of the Internet of Things with potential wireless access to organizational systems.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.18",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.18",
        "title": "Mobile Device Connection",
        "description": "Control connection of mobile devices.",
        "discussion": "A mobile device is a computing device that has a small form factor such that it can easily be carried by a single individual; is designed to operate without a physical connection; possesses local, non-removable or removable data storage; and includes a self-contained power source. Mobile devices may also include voice communication capabilities.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.19",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.19",
        "title": "Encrypt CUI on Mobile",
        "description": "Encrypt CUI on mobile devices and mobile computing platforms.",
        "discussion": "Organizations can employ full-device encryption or container-based encryption to protect the confidentiality of CUI on mobile devices and computing platforms. Container-based encryption provides a more fine-grained approach to the encryption of data and information including encrypting selected data structures such as files, records, or fields.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.20",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.20",
        "title": "External Connections",
        "description": "Verify and control/limit connections to and use of external systems.",
        "discussion": "External systems are systems or components of systems for which organizations typically have no direct supervision and authority over the application of security requirements and controls or the determination of the effectiveness of implemented controls on those systems. External systems include personally owned systems, components, or devices and privately owned computing and communications devices resident in commercial or public facilities.",
        "points": 5,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.21",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.21",
        "title": "Portable Storage Use",
        "description": "Limit use of portable storage devices on external systems.",
        "discussion": "Limits on the use of organization-controlled portable storage devices in external systems include complete prohibition of the use of such devices or restrictions on how the devices may be used and under what conditions the devices may be used.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AC.L2-3.1.22",
        "family": "Access Control",
        "family_id": "AC",
        "nist_id": "3.1.22",
        "title": "Control Public Information",
        "description": "Control information posted or processed on publicly accessible systems.",
        "discussion": "In accordance with laws, Executive Orders, directives, policies, regulations, or standards, the public is not authorized access to nonpublic information. This requirement addresses systems that are controlled by the organization and accessible to the public, typically without identification or authentication.",
        "points": 1,
        "poam_eligible": "yes"
    },

    # =========================================================================
    # 3.2 AWARENESS AND TRAINING (AT) — 3 requirements
    # =========================================================================
    {
        "id": "AT.L2-3.2.1",
        "family": "Awareness and Training",
        "family_id": "AT",
        "nist_id": "3.2.1",
        "title": "Role-Based Risk Awareness",
        "description": "Ensure that managers, systems administrators, and users of organizational systems are made aware of the security risks associated with their activities and of the applicable policies, standards, and procedures related to the security of those systems.",
        "discussion": "Organizations determine the content and frequency of security awareness training and security awareness techniques based on the specific organizational requirements and the systems to which personnel have authorized access.",
        "points": 3,
        "poam_eligible": "yes"
    },
    {
        "id": "AT.L2-3.2.2",
        "family": "Awareness and Training",
        "family_id": "AT",
        "nist_id": "3.2.2",
        "title": "Role-Based Training",
        "description": "Ensure that personnel are trained to carry out their assigned information security-related duties and responsibilities.",
        "discussion": "Organizations provide role-based security training to personnel with assigned security roles and responsibilities before authorizing access to the system or performing assigned duties and at the frequency defined by the organization thereafter.",
        "points": 3,
        "poam_eligible": "yes"
    },
    {
        "id": "AT.L2-3.2.3",
        "family": "Awareness and Training",
        "family_id": "AT",
        "nist_id": "3.2.3",
        "title": "Insider Threat Awareness",
        "description": "Provide security awareness training on recognizing and reporting potential indicators of insider threat.",
        "discussion": "Insider threat awareness training includes information directed at understanding the types and sources of insider threats, the associated risk to the organization, and the actions personnel can take to prevent, detect, and report potential insider threats.",
        "points": 1,
        "poam_eligible": "yes"
    },

    # =========================================================================
    # 3.3 AUDIT AND ACCOUNTABILITY (AU) — 9 requirements
    # =========================================================================
    {
        "id": "AU.L2-3.3.1",
        "family": "Audit and Accountability",
        "family_id": "AU",
        "nist_id": "3.3.1",
        "title": "System Auditing",
        "description": "Create and retain system audit logs and records to the extent needed to enable the monitoring, analysis, investigation, and reporting of unlawful or unauthorized system activity.",
        "discussion": "An event is any observable occurrence in a system. Audit events include those events which are relevant to the security of organizational systems. Audit records can be generated at various levels of abstraction including at the packet level as information traverses the network.",
        "points": 5,
        "poam_eligible": "yes"
    },
    {
        "id": "AU.L2-3.3.2",
        "family": "Audit and Accountability",
        "family_id": "AU",
        "nist_id": "3.3.2",
        "title": "User Accountability",
        "description": "Ensure that the actions of individual system users can be uniquely traced to those users so they can be held accountable for their actions.",
        "discussion": "This requirement ensures that the contents of the audit record include the information needed to trace an action to an individual user of a system. Audit record content that may be necessary to satisfy this requirement includes event descriptions, timestamps, source and destination addresses, user/process identifiers, success/fail indications, filenames involved, and access control or flow control rules invoked.",
        "points": 3,
        "poam_eligible": "yes"
    },
    {
        "id": "AU.L2-3.3.3",
        "family": "Audit and Accountability",
        "family_id": "AU",
        "nist_id": "3.3.3",
        "title": "Event Review",
        "description": "Review and update logged events.",
        "discussion": "The intent of this requirement is to periodically re-evaluate which logged events will continue to be retained. This is necessary to ensure that events which were initially determined as significant remain significant.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AU.L2-3.3.4",
        "family": "Audit and Accountability",
        "family_id": "AU",
        "nist_id": "3.3.4",
        "title": "Audit Failure Alerting",
        "description": "Alert in the event of an audit logging process failure.",
        "discussion": "Audit logging process failures include software and hardware errors, failures in the audit capturing mechanisms, and reaching or exceeding audit log storage capacity.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AU.L2-3.3.5",
        "family": "Audit and Accountability",
        "family_id": "AU",
        "nist_id": "3.3.5",
        "title": "Audit Correlation",
        "description": "Correlate audit record review, analysis, and reporting processes for investigation and response to indications of unlawful, unauthorized, suspicious, or unusual activity.",
        "discussion": "Correlating audit record review, analysis, and reporting processes helps to ensure that they do not operate independently but rather collectively. Regarding the assessment of a given organizational system, the requirement is met whenever audit records are reviewed, analyzed, and correlated.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AU.L2-3.3.6",
        "family": "Audit and Accountability",
        "family_id": "AU",
        "nist_id": "3.3.6",
        "title": "Audit Reduction & Reporting",
        "description": "Provide audit record reduction and report generation to support on-demand analysis and reporting.",
        "discussion": "Audit record reduction is a process that manipulates collected audit information and organizes such information in a summary format that is more meaningful to analysts. Audit record reduction and report generation capabilities do not always emanate from the same system or from the same organizational entities conducting auditing activities.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AU.L2-3.3.7",
        "family": "Audit and Accountability",
        "family_id": "AU",
        "nist_id": "3.3.7",
        "title": "Authoritative Time Source",
        "description": "Provide a system capability that compares and synchronizes internal system clocks with an authoritative source to generate time stamps for audit records.",
        "discussion": "Internal system clocks are used to generate time stamps which include date and time. Time is commonly expressed in Coordinated Universal Time (UTC), a modern continuation of Greenwich Mean Time (GMT), or local time with an offset from UTC.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AU.L2-3.3.8",
        "family": "Audit and Accountability",
        "family_id": "AU",
        "nist_id": "3.3.8",
        "title": "Audit Protection",
        "description": "Protect audit information and audit logging tools from unauthorized access, modification, and deletion.",
        "discussion": "Audit information includes all information (e.g., audit records, audit settings, and audit reports) needed to successfully audit system activity. Audit logging tools are those programs and devices used to conduct audit and logging activities.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "AU.L2-3.3.9",
        "family": "Audit and Accountability",
        "family_id": "AU",
        "nist_id": "3.3.9",
        "title": "Audit Management",
        "description": "Limit management of audit logging functionality to a subset of privileged users.",
        "discussion": "Individuals with privileged access to a system and who are also the subject of an audit by that system may affect the reliability of audit information by inhibiting audit activities or modifying audit records.",
        "points": 1,
        "poam_eligible": "yes"
    },

    # =========================================================================
    # 3.4 CONFIGURATION MANAGEMENT (CM) — 9 requirements
    # =========================================================================
    {
        "id": "CM.L2-3.4.1",
        "family": "Configuration Management",
        "family_id": "CM",
        "nist_id": "3.4.1",
        "title": "System Baselining",
        "description": "Establish and maintain baseline configurations and inventories of organizational systems (including hardware, software, firmware, and documentation) throughout the respective system development life cycles.",
        "discussion": "Baseline configurations are documented, formally reviewed, and agreed-upon specifications for systems or configuration items within those systems. Baseline configurations serve as a basis for future builds, releases, and changes to systems.",
        "points": 5,
        "poam_eligible": "yes"
    },
    {
        "id": "CM.L2-3.4.2",
        "family": "Configuration Management",
        "family_id": "CM",
        "nist_id": "3.4.2",
        "title": "Security Configuration Enforcement",
        "description": "Establish and enforce security configuration settings for information technology products employed in organizational systems.",
        "discussion": "Configuration settings are the set of parameters that can be changed in hardware, software, or firmware components of the system that affect the security posture or functionality of the system. Information technology products for which security-related configuration settings can be defined include mainframe computers, servers, workstations, input and output devices, network components, and mobile devices.",
        "points": 5,
        "poam_eligible": "yes"
    },
    {
        "id": "CM.L2-3.4.3",
        "family": "Configuration Management",
        "family_id": "CM",
        "nist_id": "3.4.3",
        "title": "System Change Management",
        "description": "Track, review, approve or disapprove, and log changes to organizational systems.",
        "discussion": "Tracking, reviewing, approving/disapproving, and logging changes is called configuration change control. Configuration change control for organizational systems involves the systematic proposal, justification, implementation, testing, review, and disposition of changes to the systems, including system upgrades and modifications.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "CM.L2-3.4.4",
        "family": "Configuration Management",
        "family_id": "CM",
        "nist_id": "3.4.4",
        "title": "Impact Analysis",
        "description": "Analyze the security impact of changes prior to implementation.",
        "discussion": "Organizational personnel with information security responsibilities conduct security impact analyses. Individuals conducting security impact analyses possess the necessary skills and technical expertise to analyze the changes to systems and the associated security ramifications.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "CM.L2-3.4.5",
        "family": "Configuration Management",
        "family_id": "CM",
        "nist_id": "3.4.5",
        "title": "Access Restrictions for Change",
        "description": "Define, document, approve, and enforce physical and logical access restrictions associated with changes to organizational systems.",
        "discussion": "Any changes to the hardware, software, or firmware components of systems can potentially have significant effects on the overall security of the systems. Therefore, organizations permit only qualified and authorized individuals to access systems for purposes of initiating changes.",
        "points": 3,
        "poam_eligible": "yes"
    },
    {
        "id": "CM.L2-3.4.6",
        "family": "Configuration Management",
        "family_id": "CM",
        "nist_id": "3.4.6",
        "title": "Least Functionality",
        "description": "Employ the principle of least functionality by configuring organizational systems to provide only essential capabilities.",
        "discussion": "Systems can provide a wide variety of functions and services. Some of the functions and services routinely provided by default may not be necessary to support essential organizational missions, functions, or operations. It is sometimes convenient to provide multiple services from single system components. However, doing so increases risk over limiting the services provided by any one component.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "CM.L2-3.4.7",
        "family": "Configuration Management",
        "family_id": "CM",
        "nist_id": "3.4.7",
        "title": "Nonessential Functionality",
        "description": "Restrict, disable, or prevent the use of nonessential programs, functions, ports, protocols, and services.",
        "discussion": "Restricting the use of nonessential software (programs) includes restricting the roles allowed to approve program execution; prohibiting auto-execute; program blacklisting and whitelisting; or restricting the use of non-approved browser plugins.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "CM.L2-3.4.8",
        "family": "Configuration Management",
        "family_id": "CM",
        "nist_id": "3.4.8",
        "title": "Application Execution Policy",
        "description": "Apply deny-by-exception (blacklisting) policy to prevent the use of unauthorized software or deny-all, permit-by-exception (whitelisting) policy to allow the execution of authorized software.",
        "discussion": "The process used to identify software programs that are not authorized to execute on systems is commonly referred to as blacklisting. The process used to identify software programs that are authorized to execute on systems is commonly referred to as whitelisting.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "CM.L2-3.4.9",
        "family": "Configuration Management",
        "family_id": "CM",
        "nist_id": "3.4.9",
        "title": "User-Installed Software",
        "description": "Control and monitor user-installed software.",
        "discussion": "Users can install software in organizational systems if provided the necessary privileges. To maintain control over the types of software installed, organizations identify permitted and prohibited actions regarding software installation.",
        "points": 1,
        "poam_eligible": "yes"
    },

    # =========================================================================
    # 3.5 IDENTIFICATION AND AUTHENTICATION (IA) — 11 requirements
    # =========================================================================
    {
        "id": "IA.L2-3.5.1",
        "family": "Identification and Authentication",
        "family_id": "IA",
        "nist_id": "3.5.1",
        "title": "Identification",
        "description": "Identify system users, processes acting on behalf of users, and devices.",
        "discussion": "Common device identifiers include Media Access Control (MAC) addresses, Internet Protocol (IP) addresses, or device-unique token identifiers. Management of individual identifiers is not applicable to shared system accounts. Typically, individual identifiers are the user names of the system accounts assigned to those individuals.",
        "points": 5,
        "poam_eligible": "yes"
    },
    {
        "id": "IA.L2-3.5.2",
        "family": "Identification and Authentication",
        "family_id": "IA",
        "nist_id": "3.5.2",
        "title": "Authentication",
        "description": "Authenticate (or verify) the identities of users, processes, or devices, as a prerequisite to allowing access to organizational systems.",
        "discussion": "Individual authenticators include passwords, key cards, cryptographic devices, and one-time password devices. Initial authenticator content is the actual content of the authenticator, for example, the initial password. In contrast, the requirements about authenticator content include the minimum password length.",
        "points": 5,
        "poam_eligible": "yes"
    },
    {
        "id": "IA.L2-3.5.3",
        "family": "Identification and Authentication",
        "family_id": "IA",
        "nist_id": "3.5.3",
        "title": "Multifactor Authentication",
        "description": "Use multifactor authentication for local and network access to privileged accounts and for network access to non-privileged accounts.",
        "discussion": "Multifactor authentication requires the use of two or more different factors to achieve authentication. The factors are defined as something you know (e.g., password/PIN); something you have (e.g., cryptographic identification device, token); or something you are (e.g., biometric). Multifactor authentication solutions that feature physical authenticators include hardware authenticators providing time-based or challenge-response one-time tokens and smart cards.",
        "points": 3,
        "poam_eligible": "yes"
    },
    {
        "id": "IA.L2-3.5.4",
        "family": "Identification and Authentication",
        "family_id": "IA",
        "nist_id": "3.5.4",
        "title": "Replay-Resistant Authentication",
        "description": "Employ replay-resistant authentication mechanisms for network access to privileged and non-privileged accounts.",
        "discussion": "Authentication processes resist replay attacks if it is impractical to successfully authenticate by recording or replaying previous authentication messages. Replay-resistant techniques include protocols that use nonces or challenges such as Transport Layer Security (TLS).",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "IA.L2-3.5.5",
        "family": "Identification and Authentication",
        "family_id": "IA",
        "nist_id": "3.5.5",
        "title": "Identifier Reuse",
        "description": "Prevent reuse of identifiers for a defined period.",
        "discussion": "Identifiers are provided for users, processes acting on behalf of users, or devices.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "IA.L2-3.5.6",
        "family": "Identification and Authentication",
        "family_id": "IA",
        "nist_id": "3.5.6",
        "title": "Identifier Handling",
        "description": "Disable identifiers after a defined period of inactivity.",
        "discussion": "Inactive identifiers pose a risk to organizational systems and applications. Owners of the inactive accounts may not have noticed that the accounts are no longer being used. Attackers that are able to exploit inactive accounts may be able to access the systems and sensitive information.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "IA.L2-3.5.7",
        "family": "Identification and Authentication",
        "family_id": "IA",
        "nist_id": "3.5.7",
        "title": "Password Complexity",
        "description": "Enforce a minimum password complexity and change of characters when new passwords are created.",
        "discussion": "This requirement applies to single-factor authentication of individuals using passwords as individual or group authenticators, and in a similar manner, when passwords are used as part of multifactor authenticators.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "IA.L2-3.5.8",
        "family": "Identification and Authentication",
        "family_id": "IA",
        "nist_id": "3.5.8",
        "title": "Password Reuse",
        "description": "Prohibit password reuse for a specified number of generations.",
        "discussion": "Password lifetime restrictions do not apply to temporary passwords.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "IA.L2-3.5.9",
        "family": "Identification and Authentication",
        "family_id": "IA",
        "nist_id": "3.5.9",
        "title": "Temporary Passwords",
        "description": "Allow temporary password use for system logons with an immediate change to a permanent password.",
        "discussion": "Changing temporary passwords to permanent passwords immediately after system logon ensures that the necessary strength of the authentication mechanism is implemented at the earliest opportunity, reducing the susceptibility to authenticator compromises.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "IA.L2-3.5.10",
        "family": "Identification and Authentication",
        "family_id": "IA",
        "nist_id": "3.5.10",
        "title": "Cryptographic Password Protection",
        "description": "Store and transmit only cryptographically-protected passwords.",
        "discussion": "Cryptographically-protected passwords use salted one-way cryptographic hashes of passwords.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "IA.L2-3.5.11",
        "family": "Identification and Authentication",
        "family_id": "IA",
        "nist_id": "3.5.11",
        "title": "Obscure Feedback",
        "description": "Obscure feedback of authentication information.",
        "discussion": "The feedback from systems does not provide information that would allow unauthorized individuals to compromise authentication mechanisms. For some types of systems or system components, for example, desktop or notebook computers with relatively large monitors, the threat (often referred to as shoulder surfing) may be significant.",
        "points": 1,
        "poam_eligible": "yes"
    },

    # =========================================================================
    # 3.6 INCIDENT RESPONSE (IR) — 3 requirements
    # =========================================================================
    {
        "id": "IR.L2-3.6.1",
        "family": "Incident Response",
        "family_id": "IR",
        "nist_id": "3.6.1",
        "title": "Incident Handling",
        "description": "Establish an operational incident-handling capability for organizational systems that includes preparation, detection, analysis, containment, recovery, and user response activities.",
        "discussion": "Organizations recognize that incident response capabilities are dependent on the capabilities of organizational systems and the mission/business processes being supported by those systems. Organizations may need to provide incident response support in terms of the breadth and depth of the incident handling process.",
        "points": 3,
        "poam_eligible": "yes"
    },
    {
        "id": "IR.L2-3.6.2",
        "family": "Incident Response",
        "family_id": "IR",
        "nist_id": "3.6.2",
        "title": "Incident Reporting",
        "description": "Track, document, and report incidents to designated officials and/or authorities both internal and external to the organization.",
        "discussion": "Tracking and documenting system security incidents includes maintaining records about each incident, the status of the incident, and other pertinent information necessary for forensics, evaluating incident details, trends, and handling.",
        "points": 3,
        "poam_eligible": "yes"
    },
    {
        "id": "IR.L2-3.6.3",
        "family": "Incident Response",
        "family_id": "IR",
        "nist_id": "3.6.3",
        "title": "Incident Response Testing",
        "description": "Test the organizational incident response capability.",
        "discussion": "Organizations test incident response capabilities to determine the effectiveness of the capabilities and to identify potential weaknesses or deficiencies. Testing includes the use of checklists, walk-through or tabletop exercises, simulations, and comprehensive exercises.",
        "points": 1,
        "poam_eligible": "yes"
    },

    # =========================================================================
    # 3.7 MAINTENANCE (MA) — 6 requirements
    # =========================================================================
    {
        "id": "MA.L2-3.7.1",
        "family": "Maintenance",
        "family_id": "MA",
        "nist_id": "3.7.1",
        "title": "Perform Maintenance",
        "description": "Perform maintenance on organizational systems.",
        "discussion": "This requirement addresses the information security aspects of the system maintenance program and applies to all types of maintenance to any system component including hardware, firmware, applications, or when necessary, a temporary/loaner system.",
        "points": 3,
        "poam_eligible": "yes"
    },
    {
        "id": "MA.L2-3.7.2",
        "family": "Maintenance",
        "family_id": "MA",
        "nist_id": "3.7.2",
        "title": "System Maintenance Control",
        "description": "Provide controls on the tools, techniques, mechanisms, and personnel used to conduct system maintenance.",
        "discussion": "This requirement addresses security-related issues with maintenance tools that are not within system authorization boundaries and are used specifically for diagnostic and repair actions on organizational systems.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "MA.L2-3.7.3",
        "family": "Maintenance",
        "family_id": "MA",
        "nist_id": "3.7.3",
        "title": "Equipment Sanitization",
        "description": "Ensure equipment removed for off-site maintenance is sanitized of any CUI.",
        "discussion": "This requirement addresses the information security aspects of system maintenance that are performed off-site and applies to all types of maintenance to any system component.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "MA.L2-3.7.4",
        "family": "Maintenance",
        "family_id": "MA",
        "nist_id": "3.7.4",
        "title": "Media Inspection",
        "description": "Check media containing diagnostic and test programs for malicious code before the media are used in organizational systems.",
        "discussion": "If upon inspection of media containing maintenance diagnostic and test programs, organizations determine that the media contain malicious code, the incident is handled consistent with organizational incident handling policies and procedures.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "MA.L2-3.7.5",
        "family": "Maintenance",
        "family_id": "MA",
        "nist_id": "3.7.5",
        "title": "Nonlocal Maintenance",
        "description": "Require multifactor authentication to establish nonlocal maintenance sessions via external network connections and terminate such connections when nonlocal maintenance is complete.",
        "discussion": "Nonlocal maintenance and diagnostic activities are those activities conducted by individuals communicating through an external network. The authentication techniques employed in the establishment of these nonlocal maintenance and diagnostic sessions reflect the network access requirements in 3.5.3.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "MA.L2-3.7.6",
        "family": "Maintenance",
        "family_id": "MA",
        "nist_id": "3.7.6",
        "title": "Maintenance Personnel",
        "description": "Supervise the maintenance activities of maintenance personnel without required access authorization.",
        "discussion": "This requirement applies to individuals performing hardware or software maintenance on organizational systems, while 3.10.1 addresses physical access for individuals whose maintenance duties place them within the physical protection perimeter of the systems.",
        "points": 1,
        "poam_eligible": "yes"
    },

    # =========================================================================
    # 3.8 MEDIA PROTECTION (MP) — 9 requirements
    # =========================================================================
    {
        "id": "MP.L2-3.8.1",
        "family": "Media Protection",
        "family_id": "MP",
        "nist_id": "3.8.1",
        "title": "Media Protection",
        "description": "Protect (i.e., physically control and securely store) system media containing CUI, both paper and digital.",
        "discussion": "System media includes digital and non-digital media. Digital media includes diskettes, magnetic tapes, flash drives, compact disks, digital video disks, and removable hard disk drives. Non-digital media includes paper and microfilm.",
        "points": 3,
        "poam_eligible": "yes"
    },
    {
        "id": "MP.L2-3.8.2",
        "family": "Media Protection",
        "family_id": "MP",
        "nist_id": "3.8.2",
        "title": "Media Access",
        "description": "Limit access to CUI on system media to authorized users.",
        "discussion": "Access can be limited by physically controlling system media and secure storage areas. Physically controlling system media includes conducting inventories, maintaining accountability for stored media, and ensuring procedures are in place to allow individuals to check out and return system media to the media library.",
        "points": 3,
        "poam_eligible": "yes"
    },
    {
        "id": "MP.L2-3.8.3",
        "family": "Media Protection",
        "family_id": "MP",
        "nist_id": "3.8.3",
        "title": "Media Disposal",
        "description": "Sanitize or destroy system media containing CUI before disposal or release for reuse.",
        "discussion": "This requirement applies to all system media, digital and non-digital, subject to disposal or reuse. Organizations can provide this protection by destroying the media, clearing the media by overwriting all addressable locations with random or fixed patterns, or by degaussing magnetic media.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "MP.L2-3.8.4",
        "family": "Media Protection",
        "family_id": "MP",
        "nist_id": "3.8.4",
        "title": "Media Markings",
        "description": "Mark media with necessary CUI markings and distribution limitations.",
        "discussion": "The term security marking refers to the application or use of human-readable security attributes. System media includes digital and non-digital media. Marking of system media reflects applicable federal laws, Executive Orders, directives, policies, and regulations.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "MP.L2-3.8.5",
        "family": "Media Protection",
        "family_id": "MP",
        "nist_id": "3.8.5",
        "title": "Media Accountability",
        "description": "Control access to media containing CUI and maintain accountability for media during transport outside of controlled areas.",
        "discussion": "Controlled areas are areas or spaces for which organizations provide sufficient physical or procedural controls to meet the requirements established for protecting systems and information.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "MP.L2-3.8.6",
        "family": "Media Protection",
        "family_id": "MP",
        "nist_id": "3.8.6",
        "title": "Portable Storage Encryption",
        "description": "Implement cryptographic mechanisms to protect the confidentiality of CUI stored on digital media during transport unless otherwise protected by alternative physical safeguards.",
        "discussion": "This requirement addresses the protection of CUI on portable digital media during transport. Cryptographic mechanisms applied to digital media include FIPS-validated encryption standards.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "MP.L2-3.8.7",
        "family": "Media Protection",
        "family_id": "MP",
        "nist_id": "3.8.7",
        "title": "Removable Media",
        "description": "Control the use of removable media on system components.",
        "discussion": "In contrast to requirement 3.8.1 which restricts user access to media, this requirement restricts the use of certain types of media on systems, for example, restricting or prohibiting the use of flash drives or external hard disk drives.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "MP.L2-3.8.8",
        "family": "Media Protection",
        "family_id": "MP",
        "nist_id": "3.8.8",
        "title": "Shared Media",
        "description": "Prohibit the use of portable storage devices when such devices have no identifiable owner.",
        "discussion": "Requiring identifiable owners for portable storage devices reduces the risk of using such technology by allowing organizations to assign responsibility and accountability for addressing known vulnerabilities in the devices.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "MP.L2-3.8.9",
        "family": "Media Protection",
        "family_id": "MP",
        "nist_id": "3.8.9",
        "title": "Protect Backups",
        "description": "Protect the confidentiality of backup CUI at storage locations.",
        "discussion": "Organizations can employ cryptographic mechanisms or alternative physical controls to protect the confidentiality of backup information at designated storage locations. Backed-up information containing CUI may include system-level information and user-level information.",
        "points": 1,
        "poam_eligible": "yes"
    },

    # =========================================================================
    # 3.9 PERSONNEL SECURITY (PS) — 2 requirements
    # =========================================================================
    {
        "id": "PS.L2-3.9.1",
        "family": "Personnel Security",
        "family_id": "PS",
        "nist_id": "3.9.1",
        "title": "Screen Individuals",
        "description": "Screen individuals prior to authorizing access to organizational systems containing CUI.",
        "discussion": "Personnel security screening activities include, for example, checks on personal references, employment history, and verification of qualifications.",
        "points": 3,
        "poam_eligible": "yes"
    },
    {
        "id": "PS.L2-3.9.2",
        "family": "Personnel Security",
        "family_id": "PS",
        "nist_id": "3.9.2",
        "title": "Personnel Actions",
        "description": "Ensure that organizational systems containing CUI are protected during and after personnel actions such as terminations and transfers.",
        "discussion": "Protecting CUI during and after personnel actions may include returning system-related property and conducting exit interviews. System-related property includes hardware authentication tokens, system administration technical manuals, keys, identification cards, and building passes.",
        "points": 3,
        "poam_eligible": "yes"
    },

    # =========================================================================
    # 3.10 PHYSICAL PROTECTION (PE) — 6 requirements
    # =========================================================================
    {
        "id": "PE.L2-3.10.1",
        "family": "Physical Protection",
        "family_id": "PE",
        "nist_id": "3.10.1",
        "title": "Limit Physical Access",
        "description": "Limit physical access to organizational systems, equipment, and the respective operating environments to authorized individuals.",
        "discussion": "This requirement applies to employees, individuals with permanent physical access authorization credentials, and visitors. Authorized individuals include personnel with required clearances, access authorizations, and need to know.",
        "points": 3,
        "poam_eligible": "yes"
    },
    {
        "id": "PE.L2-3.10.2",
        "family": "Physical Protection",
        "family_id": "PE",
        "nist_id": "3.10.2",
        "title": "Physical Access Logs",
        "description": "Protect and monitor the physical facility and support infrastructure for organizational systems.",
        "discussion": "Monitoring includes physical access monitoring and intrusion detection monitoring of areas in which systems containing CUI are stored or maintained.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "PE.L2-3.10.3",
        "family": "Physical Protection",
        "family_id": "PE",
        "nist_id": "3.10.3",
        "title": "Escort Visitors",
        "description": "Escort visitors and monitor visitor activity.",
        "discussion": "Individuals with permanent physical access authorization credentials are not considered visitors. Organizations determine the types of escorts required for visits to facilities containing CUI.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "PE.L2-3.10.4",
        "family": "Physical Protection",
        "family_id": "PE",
        "nist_id": "3.10.4",
        "title": "Physical Access Logs",
        "description": "Maintain audit logs of physical access.",
        "discussion": "Organizations have flexibility in the types of audit logs maintained and the access log format, with provisions for accessing information needed for investigations and correlating with other system audit activities.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "PE.L2-3.10.5",
        "family": "Physical Protection",
        "family_id": "PE",
        "nist_id": "3.10.5",
        "title": "Manage Physical Access",
        "description": "Control and manage physical access devices.",
        "discussion": "Physical access devices include keys, locks, combinations, and card readers.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "PE.L2-3.10.6",
        "family": "Physical Protection",
        "family_id": "PE",
        "nist_id": "3.10.6",
        "title": "Alternative Work Sites",
        "description": "Enforce safeguarding measures for CUI at alternate work sites.",
        "discussion": "Alternate work sites may include government facilities or the private residences of employees. Organizations may define different security requirements for specific alternate work sites or types of sites.",
        "points": 1,
        "poam_eligible": "yes"
    },

    # =========================================================================
    # 3.11 RISK ASSESSMENT (RA) — 3 requirements
    # =========================================================================
    {
        "id": "RA.L2-3.11.1",
        "family": "Risk Assessment",
        "family_id": "RA",
        "nist_id": "3.11.1",
        "title": "Risk Assessments",
        "description": "Periodically assess the risk to organizational operations (including mission, functions, image, or reputation), organizational assets, and individuals, resulting from the operation of organizational systems and the associated processing, storage, or transmission of CUI.",
        "discussion": "Clearly defined authorization boundaries are a prerequisite for effective risk assessments. Risk assessments take into account threats, vulnerabilities, likelihood, and impact to organizational operations and assets, individuals, other organizations, and the Nation.",
        "points": 3,
        "poam_eligible": "yes"
    },
    {
        "id": "RA.L2-3.11.2",
        "family": "Risk Assessment",
        "family_id": "RA",
        "nist_id": "3.11.2",
        "title": "Vulnerability Scan",
        "description": "Scan for vulnerabilities in organizational systems and applications periodically and when new vulnerabilities affecting those systems and applications are identified.",
        "discussion": "Organizations determine the required vulnerability scanning for all system components, ensuring that potential sources of vulnerabilities such as networked printers, scanners, and copiers are not overlooked.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "RA.L2-3.11.3",
        "family": "Risk Assessment",
        "family_id": "RA",
        "nist_id": "3.11.3",
        "title": "Vulnerability Remediation",
        "description": "Remediate vulnerabilities in accordance with risk assessments.",
        "discussion": "Vulnerabilities discovered during the assessment and monitoring of compliance and through the vulnerability scanning process are remediated with consideration of the related assessment of risk.",
        "points": 1,
        "poam_eligible": "yes"
    },

    # =========================================================================
    # 3.12 SECURITY ASSESSMENT (CA) — 4 requirements
    # =========================================================================
    {
        "id": "CA.L2-3.12.1",
        "family": "Security Assessment",
        "family_id": "CA",
        "nist_id": "3.12.1",
        "title": "Security Control Assessment",
        "description": "Periodically assess the security controls in organizational systems to determine if the controls are effective in their application.",
        "discussion": "Organizations assess security controls in organizational systems and the environments in which those systems operate as part of the system development life cycle. Security controls are the safeguards or countermeasures organizations implement to satisfy security requirements.",
        "points": 3,
        "poam_eligible": "yes"
    },
    {
        "id": "CA.L2-3.12.2",
        "family": "Security Assessment",
        "family_id": "CA",
        "nist_id": "3.12.2",
        "title": "Plan of Action",
        "description": "Develop and implement plans of action designed to correct deficiencies and reduce or eliminate vulnerabilities in organizational systems.",
        "discussion": "Plans of action are key documents in security authorization packages and are subject to federal reporting requirements. Organizations develop plans of action that describe how any unimplemented security requirements will be met and how any planned mitigations will be implemented.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "CA.L2-3.12.3",
        "family": "Security Assessment",
        "family_id": "CA",
        "nist_id": "3.12.3",
        "title": "Security Control Monitoring",
        "description": "Monitor security controls on an ongoing basis to ensure the continued effectiveness of the controls.",
        "discussion": "Continuous monitoring programs facilitate ongoing awareness of threats, vulnerabilities, and information security to support organizational risk management decisions.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "CA.L2-3.12.4",
        "family": "Security Assessment",
        "family_id": "CA",
        "nist_id": "3.12.4",
        "title": "System Security Plan",
        "description": "Develop, document, and periodically update system security plans that describe system boundaries, system environments of operation, how security requirements are implemented, and the relationships with or connections to other systems.",
        "discussion": "System security plans relate security requirements to a set of security controls. System security plans also describe, at a high level, how the security controls meet those security requirements but do not provide detailed, technical descriptions of the design or implementation of the controls.",
        "points": 3,
        "poam_eligible": "no"
    },

    # =========================================================================
    # 3.13 SYSTEM AND COMMUNICATIONS PROTECTION (SC) — 16 requirements
    # =========================================================================
    {
        "id": "SC.L2-3.13.1",
        "family": "System and Communications Protection",
        "family_id": "SC",
        "nist_id": "3.13.1",
        "title": "Boundary Protection",
        "description": "Monitor, control, and protect communications (i.e., information transmitted or received by organizational systems) at the external boundaries and key internal boundaries of organizational systems.",
        "discussion": "Communications can be monitored, controlled, and protected at boundary components and by restricting or prohibiting interfaces in organizational systems. Boundary components include gateways, routers, firewalls, guards, network-based malicious code analysis and exfiltration systems, virtualization systems, and encrypted tunnels implemented within a system security architecture.",
        "points": 5,
        "poam_eligible": "yes"
    },
    {
        "id": "SC.L2-3.13.2",
        "family": "System and Communications Protection",
        "family_id": "SC",
        "nist_id": "3.13.2",
        "title": "Security Engineering",
        "description": "Employ architectural designs, software development techniques, and systems engineering principles that promote effective information security within organizational systems.",
        "discussion": "Organizations apply systems security engineering principles to new development systems or systems undergoing major upgrades. For legacy systems, organizations apply systems security engineering principles to system upgrades and modifications to the extent feasible, given the current state of hardware, software, and firmware components within those systems.",
        "points": 3,
        "poam_eligible": "yes"
    },
    {
        "id": "SC.L2-3.13.3",
        "family": "System and Communications Protection",
        "family_id": "SC",
        "nist_id": "3.13.3",
        "title": "Role Separation",
        "description": "Separate user functionality from system management functionality.",
        "discussion": "System management functionality includes functions necessary to administer databases, network components, workstations, or servers, and typically requires privileged user access.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "SC.L2-3.13.4",
        "family": "System and Communications Protection",
        "family_id": "SC",
        "nist_id": "3.13.4",
        "title": "Shared Resource Control",
        "description": "Prevent unauthorized and unintended information transfer via shared system resources.",
        "discussion": "The control of information in shared system resources (e.g., registers, cache memory, main memory, hard disks) is also commonly referred to as object reuse and residual information protection.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "SC.L2-3.13.5",
        "family": "System and Communications Protection",
        "family_id": "SC",
        "nist_id": "3.13.5",
        "title": "Public-Access System Separation",
        "description": "Implement subnetworks for publicly accessible system components that are physically or logically separated from internal networks.",
        "discussion": "Subnetworks that are physically or logically separated from internal networks are referred to as demilitarized zones (DMZs). DMZs are typically implemented with boundary control devices and techniques.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "SC.L2-3.13.6",
        "family": "System and Communications Protection",
        "family_id": "SC",
        "nist_id": "3.13.6",
        "title": "Network Communication by Exception",
        "description": "Deny network communications traffic by default and allow network communications traffic by exception (i.e., deny all, permit by exception).",
        "discussion": "This requirement applies to inbound and outbound network communications traffic at the system boundary and at identified points within the system.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "SC.L2-3.13.7",
        "family": "System and Communications Protection",
        "family_id": "SC",
        "nist_id": "3.13.7",
        "title": "Split Tunneling",
        "description": "Prevent remote devices from simultaneously establishing non-remote connections with organizational systems and communicating via some other connection to resources in external networks (i.e., split tunneling).",
        "discussion": "Split tunneling might be desirable by remote users to communicate with local system resources such as printers or file servers. However, split tunneling allows unauthorized external connections, making the system more vulnerable to attack and to exfiltration of organizational information.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "SC.L2-3.13.8",
        "family": "System and Communications Protection",
        "family_id": "SC",
        "nist_id": "3.13.8",
        "title": "Data in Transit",
        "description": "Implement cryptographic mechanisms to prevent unauthorized disclosure of CUI during transmission unless otherwise protected by alternative physical safeguards.",
        "discussion": "This requirement applies to internal and external networks and any system components that can transmit information including servers, notebook computers, desktop computers, mobile devices, printers, copiers, scanners, and facsimile machines.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "SC.L2-3.13.9",
        "family": "System and Communications Protection",
        "family_id": "SC",
        "nist_id": "3.13.9",
        "title": "Network Disconnect",
        "description": "Terminate network connections associated with communications sessions at the end of the sessions or after a defined period of inactivity.",
        "discussion": "This requirement applies to internal and external networks. Terminating network connections associated with communications sessions include de-allocating associated TCP/IP address or port pairs at the operating system level, or de-allocating networking assignments at the application level if multiple application sessions are using a single operating system level network connection.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "SC.L2-3.13.10",
        "family": "System and Communications Protection",
        "family_id": "SC",
        "nist_id": "3.13.10",
        "title": "Key Management",
        "description": "Establish and manage cryptographic keys for cryptography employed in organizational systems.",
        "discussion": "Cryptographic key management and establishment can be performed using manual procedures or automated mechanisms with supporting manual procedures.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "SC.L2-3.13.11",
        "family": "System and Communications Protection",
        "family_id": "SC",
        "nist_id": "3.13.11",
        "title": "CUI Encryption",
        "description": "Employ FIPS-validated cryptography when used to protect the confidentiality of CUI.",
        "discussion": "Cryptography can be employed to support many security solutions including the protection of controlled unclassified information, the provision of digital signatures, and the enforcement of information separation when authorized individuals have the necessary clearances for such information but lack the necessary formal access approvals.",
        "points": 5,
        "poam_eligible": "yes"
    },
    {
        "id": "SC.L2-3.13.12",
        "family": "System and Communications Protection",
        "family_id": "SC",
        "nist_id": "3.13.12",
        "title": "Collaborative Device Control",
        "description": "Prohibit remote activation of collaborative computing devices and provide indication of devices in use to users present at the device.",
        "discussion": "Collaborative computing devices include networked white boards, cameras, and microphones. Indication of use includes signals to users when collaborative computing devices are activated.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "SC.L2-3.13.13",
        "family": "System and Communications Protection",
        "family_id": "SC",
        "nist_id": "3.13.13",
        "title": "Mobile Code",
        "description": "Control and monitor the use of mobile code.",
        "discussion": "Decisions regarding the employment of mobile code within organizational systems are based on the potential for the code to cause damage to the systems if used maliciously. Mobile code technologies include Java, JavaScript, ActiveX, Postscript, PDF, Flash animations, and VBScript.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "SC.L2-3.13.14",
        "family": "System and Communications Protection",
        "family_id": "SC",
        "nist_id": "3.13.14",
        "title": "Voice over Internet Protocol",
        "description": "Control and monitor the use of Voice over Internet Protocol (VoIP) technologies.",
        "discussion": "VoIP has different security implications, some of which are location-dependent. Additional security in VoIP systems include the ability to encrypt the voice stream and to be cognizant of the following types of attacks: eavesdropping, traffic analysis, impersonation, and replay.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "SC.L2-3.13.15",
        "family": "System and Communications Protection",
        "family_id": "SC",
        "nist_id": "3.13.15",
        "title": "Communications Authenticity",
        "description": "Protect the authenticity of communications sessions.",
        "discussion": "Authenticity protection includes protecting against man-in-the-middle attacks, session hijacking, and the insertion of false information into communications sessions. This requirement addresses communications protection at the session versus packet level.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "SC.L2-3.13.16",
        "family": "System and Communications Protection",
        "family_id": "SC",
        "nist_id": "3.13.16",
        "title": "Data at Rest",
        "description": "Protect the confidentiality of CUI at rest.",
        "discussion": "Information at rest refers to the state of information when it is not in process or in transit and is located on storage devices as specific components of systems. The focus of protection at rest is not on the type of storage device or the frequency of access but rather the state of the information.",
        "points": 1,
        "poam_eligible": "yes"
    },

    # =========================================================================
    # 3.14 SYSTEM AND INFORMATION INTEGRITY (SI) — 7 requirements
    # =========================================================================
    {
        "id": "SI.L2-3.14.1",
        "family": "System and Information Integrity",
        "family_id": "SI",
        "nist_id": "3.14.1",
        "title": "Flaw Remediation",
        "description": "Identify, report, and correct system flaws in a timely manner.",
        "discussion": "Organizations identify systems affected by announced software and firmware flaws including potential vulnerabilities resulting from those flaws and report this information to designated personnel with information security responsibilities.",
        "points": 5,
        "poam_eligible": "yes"
    },
    {
        "id": "SI.L2-3.14.2",
        "family": "System and Information Integrity",
        "family_id": "SI",
        "nist_id": "3.14.2",
        "title": "Malicious Code Protection",
        "description": "Provide protection from malicious code at designated locations within organizational systems.",
        "discussion": "Designated locations include system entry and exit points which may include firewalls, remote-access servers, workstations, electronic mail servers, web servers, proxy servers, notebook computers, and mobile devices. Malicious code includes viruses, worms, Trojan horses, and spyware.",
        "points": 3,
        "poam_eligible": "yes"
    },
    {
        "id": "SI.L2-3.14.3",
        "family": "System and Information Integrity",
        "family_id": "SI",
        "nist_id": "3.14.3",
        "title": "Security Alerts & Advisories",
        "description": "Monitor system security alerts and advisories and take action in response.",
        "discussion": "There are many publicly available sources of system security alerts and advisories. The United States Computer Emergency Readiness Team (US-CERT) generates security alerts and advisories to maintain situational awareness across the federal government and in nonfederal organizations.",
        "points": 3,
        "poam_eligible": "yes"
    },
    {
        "id": "SI.L2-3.14.4",
        "family": "System and Information Integrity",
        "family_id": "SI",
        "nist_id": "3.14.4",
        "title": "Update Malicious Code Protection",
        "description": "Update malicious code protection mechanisms when new releases are available.",
        "discussion": "Malicious code protection mechanisms include anti-virus signature definitions. Due to information integrity concerns, malicious code protection mechanisms are typically protected from unauthorized, unapproved changes by configuring and locking host-based security software.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "SI.L2-3.14.5",
        "family": "System and Information Integrity",
        "family_id": "SI",
        "nist_id": "3.14.5",
        "title": "System & File Scanning",
        "description": "Perform periodic scans of organizational systems and real-time scans of files from external sources as files are downloaded, opened, or executed.",
        "discussion": "Periodic scanning of organizational systems and real-time scans of files from external sources can detect malicious code.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "SI.L2-3.14.6",
        "family": "System and Information Integrity",
        "family_id": "SI",
        "nist_id": "3.14.6",
        "title": "Monitor Communications for Attacks",
        "description": "Monitor organizational systems, including inbound and outbound communications traffic, to detect attacks and indicators of potential attacks.",
        "discussion": "System monitoring includes external and internal monitoring. External monitoring includes the observation of events occurring at the system boundary. Internal monitoring includes the observation of events occurring within the system.",
        "points": 1,
        "poam_eligible": "yes"
    },
    {
        "id": "SI.L2-3.14.7",
        "family": "System and Information Integrity",
        "family_id": "SI",
        "nist_id": "3.14.7",
        "title": "Identify Unauthorized Use",
        "description": "Identify unauthorized use of organizational systems.",
        "discussion": "System monitoring includes external and internal monitoring. Unusual or unauthorized activities or conditions related to inbound and outbound communications traffic include internal traffic that indicates the presence of malicious code in systems or propagating among system components.",
        "points": 1,
        "poam_eligible": "yes"
    },
]

# =========================================================================
# Validation helpers
# =========================================================================
FAMILY_COUNTS = {
    "Access Control": 22,
    "Awareness and Training": 3,
    "Audit and Accountability": 9,
    "Configuration Management": 9,
    "Identification and Authentication": 11,
    "Incident Response": 3,
    "Maintenance": 6,
    "Media Protection": 9,
    "Personnel Security": 2,
    "Physical Protection": 6,
    "Risk Assessment": 3,
    "Security Assessment": 4,
    "System and Communications Protection": 16,
    "System and Information Integrity": 7,
}

def validate_controls():
    """Validate the control dataset integrity."""
    assert len(NIST_800_171_CONTROLS) == 110, \
        f"Expected 110 controls, got {len(NIST_800_171_CONTROLS)}"

    # Check family counts
    from collections import Counter
    family_counts = Counter(c["family"] for c in NIST_800_171_CONTROLS)
    for family, expected in FAMILY_COUNTS.items():
        actual = family_counts.get(family, 0)
        assert actual == expected, \
            f"{family}: expected {expected}, got {actual}"

    # Check SPRS total possible deduction
    total_points = sum(c["points"] for c in NIST_800_171_CONTROLS)
    # Max deduction = total_points, floor = 110 - total_points
    print(f"Total controls: {len(NIST_800_171_CONTROLS)}")
    print(f"Total SPRS deduction points: {total_points}")
    print(f"SPRS score range: {110 - total_points} to 110")
    print(f"  5-point controls: {sum(1 for c in NIST_800_171_CONTROLS if c['points'] == 5)}")
    print(f"  3-point controls: {sum(1 for c in NIST_800_171_CONTROLS if c['points'] == 3)}")
    print(f"  1-point controls: {sum(1 for c in NIST_800_171_CONTROLS if c['points'] == 1)}")

    # Check unique IDs
    ids = [c["id"] for c in NIST_800_171_CONTROLS]
    assert len(ids) == len(set(ids)), "Duplicate control IDs found"

    # Check no POA&M for SSP
    ssp_control = next(c for c in NIST_800_171_CONTROLS if c["nist_id"] == "3.12.4")
    assert ssp_control["poam_eligible"] == "no", "SSP (3.12.4) must not be POA&M eligible"

    print("All validations passed!")


if __name__ == "__main__":
    validate_controls()
