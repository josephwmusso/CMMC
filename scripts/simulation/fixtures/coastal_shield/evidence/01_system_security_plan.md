---
artifact_id: cs_ev_01
title: Coastal Shield System Security Plan v2
evidence_type: POLICY_DOCUMENT
file_format: pdf
page_count: 42
last_updated: "2026-03-01"
owner: mthompson@coastalshield.com
maps_to_controls: [CA.L2-3.12.4, CA.L2-3.12.1]
---
The Coastal Shield Technologies SSP is a 42-page document covering all
110 NIST 800-171 Rev 2 controls. Version 2 was published March 2026
after the initial CMMC Level 2 self-assessment. The SSP describes the
CUI enclave hosted on Microsoft 365 GCC High with Palo Alto PA-450
perimeter enforcement, CrowdStrike Falcon endpoint protection on all
28 endpoints, and Microsoft Sentinel SIEM for centralized audit logging.
The system boundary encompasses 28 domain-joined Windows 11 Enterprise
workstations, 3 Windows Server 2022 servers (CS-DC01, CS-FS01, CS-SENT01),
and the M365 GCC High tenant. Remote access is via Palo Alto GlobalProtect
VPN with Entra ID Conditional Access requiring FIDO2 or Microsoft
Authenticator for all sessions.
