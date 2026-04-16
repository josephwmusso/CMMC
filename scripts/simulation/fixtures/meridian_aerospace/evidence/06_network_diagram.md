---
artifact_id: meridian_ev_06
title: Meridian Aerospace Network Diagram
evidence_type: POLICY_DOCUMENT
file_format: pdf
page_count: 1
last_updated: "2025-09-01"
owner: jbell@meridian-aero.com
maps_to_controls: [SC.L2-3.13.1, SC.L2-3.13.5]
content_summary: |
  The network diagram is a single-page PDF that was originally hand-drawn
  on paper by Jason Bell and then scanned/digitized. It was last updated
  in September 2025 and represents the entire Meridian Aerospace network
  topology.

  The diagram shows the following linear path: ISP connection (cable
  modem) → SonicWall TZ370 firewall → single flat LAN on the
  192.168.10.0/24 subnet. All devices are depicted on this single subnet
  with no segmentation.

  Devices shown on the 192.168.10.0/24 network include: 6 office
  workstations (Windows 10/11), 2 shop floor CNC controller PCs, 1
  Synology NAS labeled "dev-nas" used for local file sharing and CNC
  program storage, 1 network printer/copier, and 1 wireless access point
  providing Wi-Fi for the office area. The SonicWall TZ370 is depicted as
  the sole boundary device between the internet and the internal network.

  Handwritten annotations on the diagram note "SonicWall manages
  firewall rules" and "all machines get DHCP from SonicWall." The Wi-Fi
  access point is noted as using WPA2-PSK with a shared passphrase. No
  guest Wi-Fi network is depicted.

  DELIBERATELY ABSENT: There is no CUI boundary or enclave labeled
  anywhere on the diagram. There is no DMZ. There is no VLAN segmentation
  — shop floor CNC machines, office workstations, the NAS, and the Wi-Fi
  access point all share the same flat 192.168.10.0/24 subnet. There is
  no intrusion detection or intrusion prevention system shown. There is no
  network monitoring or logging appliance depicted. There is no VPN
  concentrator or remote access gateway. There is no indication of where
  CUI flows or is stored on the network. The diagram does not depict any
  cloud connections to Google Workspace or external services.
---
