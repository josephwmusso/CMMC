"""
src/api/intake_modules/module5_mp_pe_ps.py

Module 5 — Media Protection (MP) + Physical Protection (PE) + Personnel Security (PS).
17 CONTROL_STATUS questions (MP=9, PE=6, PS=2).
"""
from src.api.intake_modules import ModuleDefinition, register_module
from src.api.intake_modules._shared import status_q


M = 5
SECTION_MP = "Media Protection"
SECTION_PE = "Physical Protection"
SECTION_PS = "Personnel Security"


QUESTIONS = [
    # ── MP ───────────────────────────────────────────────────────────────
    status_q(M, "MP", "3.8.1", "MP.L2-3.8.1", "Media Protection",
        SECTION_MP, 3,
        "Protect CUI on both paper and digital media. Locked cabinets for paper CUI; "
        "BitLocker full-disk encryption enforced on every laptop through Intune compliance "
        "policies; tamper-evident seals on transport cases.",
    ),
    status_q(M, "MP", "3.8.2", "MP.L2-3.8.2", "Media Access",
        SECTION_MP, 3,
        "Limit access to CUI media to authorized users. Entra security groups gate access to "
        "CUI SharePoint sites; building badge logs track server-room entry; printed CUI is "
        "kept in locked file cabinets controlled by the ISSO.",
    ),
    status_q(M, "MP", "3.8.3", "MP.L2-3.8.3", "Media Sanitization",
        SECTION_MP, 1,
        "Sanitize or destroy media containing CUI before disposal or reuse. NIST 800-88 "
        "purge for drives; paper CUI goes to a cross-cut shredder; certificates of "
        "destruction archived by the ISSO.",
    ),
    status_q(M, "MP", "3.8.4", "MP.L2-3.8.4", "Media Markings",
        SECTION_MP, 1,
        "Mark media containing CUI with applicable markings and distribution limits. "
        "M365 Purview sensitivity labels auto-apply to documents tagged as CUI; printed "
        "documents carry CUI cover sheets per DoDI 5200.48.",
    ),
    status_q(M, "MP", "3.8.5", "MP.L2-3.8.5", "Media Accountability",
        SECTION_MP, 1,
        "Control access to media outside of controlled areas. Encrypted USB sign-out log; "
        "RMA tracker for returning drives; courier service only for off-site CUI transport.",
    ),
    status_q(M, "MP", "3.8.6", "MP.L2-3.8.6", "Portable Storage Encryption",
        SECTION_MP, 1,
        "Implement cryptographic mechanisms to protect CUI on portable storage. BitLocker "
        "To Go enforced via Intune; non-encrypted USB writes blocked by GPO/Intune "
        "device-control policies.",
    ),
    status_q(M, "MP", "3.8.7", "MP.L2-3.8.7", "Removable Media Use",
        SECTION_MP, 1,
        "Control the use of removable media on system components. Intune device-control "
        "policies whitelist approved USB VIDs/PIDs; CrowdStrike device-control module logs "
        "connect/disconnect events.",
    ),
    status_q(M, "MP", "3.8.8", "MP.L2-3.8.8", "Prohibit Ownerless Media",
        SECTION_MP, 1,
        "Prohibit the use of portable storage devices when no identifiable owner exists. "
        "Company policy requires an asset-tagged device; personal USBs are blocked via "
        "Intune device-control.",
    ),
    status_q(M, "MP", "3.8.9", "MP.L2-3.8.9", "Protect Backup CUI",
        SECTION_MP, 1,
        "Protect the confidentiality of backup CUI at storage locations. Veeam backups are "
        "encrypted (AES-256) with keys in Azure Key Vault; immutable/air-gapped copies "
        "stored offsite in Azure with Entra RBAC.",
    ),

    # ── PE ───────────────────────────────────────────────────────────────
    status_q(M, "PE", "3.10.1", "PE.L2-3.10.1", "Limit Physical Access",
        SECTION_PE, 3,
        "Limit physical access to systems, equipment, and operating environments to "
        "authorized individuals. Badge-access building with visitor log; server closet "
        "behind a secondary lock whose key is held by the ISSO.",
    ),
    status_q(M, "PE", "3.10.2", "PE.L2-3.10.2", "Monitor Facility",
        SECTION_PE, 1,
        "Protect and monitor the physical facility and support infrastructure. CCTV with "
        "30-day retention covers ingress/egress and server room; monitored alarm system "
        "with 24/7 response via the landlord's contracted provider.",
    ),
    status_q(M, "PE", "3.10.3", "PE.L2-3.10.3", "Escort Visitors",
        SECTION_PE, 1,
        "Escort visitors and monitor their activity. Sign-in sheet at reception; temp "
        "visitor badge; documented escort policy requiring an employee present at all "
        "times for visitors in CUI-processing areas.",
    ),
    status_q(M, "PE", "3.10.4", "PE.L2-3.10.4", "Physical Access Records",
        SECTION_PE, 1,
        "Maintain audit logs of physical access. Badge-system event log archived 12 months "
        "minimum; visitor sign-in sheets scanned into SharePoint weekly.",
    ),
    status_q(M, "PE", "3.10.5", "PE.L2-3.10.5", "Control Physical Access Devices",
        SECTION_PE, 1,
        "Control and manage physical access devices (badges, keys, combinations). Badge "
        "issuance log; quarterly badge audit; lost-badge revocation within 1 business day.",
    ),
    status_q(M, "PE", "3.10.6", "PE.L2-3.10.6", "Alternate Work Sites",
        SECTION_PE, 1,
        "Enforce safeguarding measures for CUI at alternate work sites. Remote worker "
        "policy requires locked room, clean-desk discipline, BitLockered laptop, and "
        "quarterly self-attestation.",
    ),

    # ── PS ───────────────────────────────────────────────────────────────
    status_q(M, "PS", "3.9.1", "PS.L2-3.9.1", "Screen Individuals",
        SECTION_PS, 3,
        "Screen individuals before authorizing access to CUI systems. Pre-employment "
        "background check owned by HR; NDA signed at onboarding; citizenship verification "
        "for ITAR-covered work before Entra ID account activation.",
    ),
    status_q(M, "PS", "3.9.2", "PS.L2-3.9.2", "Personnel Termination",
        SECTION_PS, 3,
        "Ensure CUI systems are protected during and after personnel actions. Offboarding "
        "runbook disables the Entra account, retrieves the device, and revokes the building "
        "badge within 24 hours of separation; badges and assets logged as returned.",
    ),
]


register_module(ModuleDefinition(
    number=M,
    name="Media, Physical & Personnel Security",
    description="MP, PE, and PS control families — media handling, physical security, and personnel screening.",
    families=["MP", "PE", "PS"],
    control_ids=[q.control_id for q in QUESTIONS],
    doc_templates=["policy_manual"],
    estimated_minutes=18,
    questions=QUESTIONS,
))
