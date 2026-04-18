---
artifact_id: cs_ev_03
title: MFA Configuration Export
evidence_type: CONFIG_EXPORT
last_updated: "2026-04-01"
maps_to_controls: [IA.L2-3.5.1, IA.L2-3.5.2, IA.L2-3.5.3]
---
Entra ID Conditional Access policy export showing 100% MFA enrollment
across all 28 users. Privileged accounts (3) require FIDO2 hardware
keys. Standard users use Microsoft Authenticator with number matching.
All access to CUI resources requires phishing-resistant MFA via
Conditional Access policy "Require MFA - CUI Enclave."
