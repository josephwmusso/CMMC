"""
src/api/intake_modules/module4_ir_ma.py

Module 4 — Incident Response (IR) + Maintenance (MA).
9 CONTROL_STATUS questions (IR=3, MA=6).
"""
from src.api.intake_modules import ModuleDefinition, register_module
from src.api.intake_modules._shared import status_q


M = 4
SECTION_IR = "Incident Response"
SECTION_MA = "Maintenance"


QUESTIONS = [
    # ── IR ───────────────────────────────────────────────────────────────
    status_q(M, "IR", "3.6.1", "IR.L2-3.6.1", "Incident Handling",
        SECTION_IR, 3,
        "Operational incident-handling capability covering preparation, detection, analysis, "
        "containment, recovery, and user response. A mature program uses a documented IR plan; SIEM "
        "generates detections; CrowdStrike Real Time Response is used for containment; a "
        "dedicated Teams channel is the comms hub during incidents.",
    ),
    status_q(M, "IR", "3.6.2", "IR.L2-3.6.2", "Incident Reporting",
        SECTION_IR, 3,
        "Track, document, and report incidents to designated officials and authorities. "
        "Internal tickets drive the playbook; DFARS 7012 reports go to DoD DC3 via the "
        "DIB Cyber Security reporting portal within 72 hours of a reportable cyber incident.",
    ),
    status_q(M, "IR", "3.6.3", "IR.L2-3.6.3", "Incident Response Testing",
        SECTION_IR, 1,
        "Test the organization's incident response capability. Annual tabletop exercise led "
        "by the ISSO with execs and IT; CrowdStrike Falcon OverWatch or a Sentinel "
        "breach-and-attack-simulation pack provides the technical drill.",
    ),

    # ── MA ───────────────────────────────────────────────────────────────
    status_q(M, "MA", "3.7.1", "MA.L2-3.7.1", "Perform Maintenance",
        SECTION_MA, 3,
        "Perform maintenance on organizational systems. Windows patching via Intune Update "
        "Rings (critical, broad); Palo Alto PAN-OS updates during scheduled maintenance "
        "windows; Veeam software updates after validation in test.",
    ),
    status_q(M, "MA", "3.7.2", "MA.L2-3.7.2", "System Maintenance Control",
        SECTION_MA, 1,
        "Control tools, techniques, mechanisms, and personnel used for system maintenance. "
        "Approved-tool list lives in the CM plan; maintenance personnel must hold an Entra "
        "ID account and be Intune-enrolled before touching CUI systems.",
    ),
    status_q(M, "MA", "3.7.3", "MA.L2-3.7.3", "Equipment Sanitization",
        SECTION_MA, 1,
        "Ensure equipment removed for off-site maintenance is sanitized of CUI. NIST 800-88 "
        "purge procedure for drives; a certificate of destruction is archived per asset "
        "in the asset management system.",
    ),
    status_q(M, "MA", "3.7.4", "MA.L2-3.7.4", "Check Media for Malicious Code",
        SECTION_MA, 1,
        "Check media containing diagnostic and test programs for malicious code before use. "
        "Dedicated CrowdStrike-protected kiosk scans vendor USBs before they can be plugged "
        "into production systems; Intune device-control blocks non-approved USBs by default.",
    ),
    status_q(M, "MA", "3.7.5", "MA.L2-3.7.5", "Nonlocal Maintenance",
        SECTION_MA, 1,
        "Require MFA to establish nonlocal maintenance sessions and terminate them when "
        "complete. Vendors connect via Palo Alto GlobalProtect (SAML + Entra MFA); sessions "
        "auto-terminate on idle and at ticket close.",
    ),
    status_q(M, "MA", "3.7.6", "MA.L2-3.7.6", "Maintenance Personnel",
        SECTION_MA, 1,
        "Supervise maintenance activities performed by personnel without required access. "
        "Escort policy documented; CCTV covers the server closet; temp Entra guest accounts "
        "are time-boxed and disabled on task completion.",
    ),
]


register_module(ModuleDefinition(
    number=M,
    name="Incident Response + Maintenance",
    description="IR and MA control families — incident handling, reporting, and maintenance control.",
    families=["IR", "MA"],
    control_ids=[q.control_id for q in QUESTIONS],
    doc_templates=["ir_plan"],
    estimated_minutes=12,
    questions=QUESTIONS,
))
