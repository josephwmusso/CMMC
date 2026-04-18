---
artifact_id: cs_ev_05
title: Microsoft Sentinel Audit Log Configuration
evidence_type: CONFIG_EXPORT
last_updated: "2026-04-01"
maps_to_controls: [AU.L2-3.3.1, AU.L2-3.3.2, AU.L2-3.3.5]
---
Microsoft Sentinel workspace configuration showing data connectors
for Entra ID sign-in logs, Windows Security Events, CrowdStrike
Falcon alerts, and Palo Alto PA-450 threat logs. Retention: 90-day
hot storage in Log Analytics, 365-day archive in Azure Storage.
NTP synchronization configured across all endpoints via domain
Group Policy pointing to time.windows.com.
