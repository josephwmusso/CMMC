---
artifact_id: cs_ev_07
title: Network Architecture Diagram v2
evidence_type: CONFIG_EXPORT
last_updated: "2026-03-15"
maps_to_controls: [SC.L2-3.13.1, SC.L2-3.13.5, CA.L2-3.12.4]
---
Visio network diagram showing Palo Alto PA-450 at perimeter with 4
security zones: CUI-LAN (10.10.2.0/24), Server-LAN (10.10.1.0/24),
Guest-WiFi (10.10.99.0/24), and WAN. Deny-by-default inter-zone
policy. IPS signatures updated daily. GlobalProtect VPN for remote
access with split-tunnel disabled for CUI traffic. CUI enclave
boundary marked with dashed red line encompassing Server-LAN and
CUI-LAN segments.
