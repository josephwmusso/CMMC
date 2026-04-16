# Meridian Aerospace Components, LLC — Simulation Fixture

## Overview

Meridian is a 14-person precision CNC machining shop in Wichita, KS that
subcontracts for Spirit AeroSystems (DFARS 252.204-7012 flows down). They
handle CTI (technical drawings) and are mid-journey toward CMMC Level 2 —
the owner knows it's coming, has run Nessus and CIS-CAT at a prime's
suggestion, but has no consultant, no SSP, no POA&M, and lean documentation.

**Authored against:** schema commit `96437f5`

**Note:** Phase 1 schema extraction reported 128 unique question IDs, but the
running intake engine asks 135 questions including sub-questions for
IA.L2-3.5.3 scope (`m3_ia_3.5.3_mfa_scope`) and SC.L2-3.13.11 scope
(`m7_sc_3.13.11_fips_scope`) which drive partial-credit scoring. Fixture has
135 entries to match runtime behavior.

## Tool Stack

| Category | Tool | Notes |
|----------|------|-------|
| Identity | Google Workspace (Google Identity) | 2-Step Verification org-wide, BUT legacy IMAP/SMTP not blocked |
| Email | Google Workspace (commercial) | NOT GCC High — this is a real CUI gap |
| EDR | MS Defender Antivirus (free built-in) | Not Defender for Endpoint. No cloud management. |
| Firewall | SonicWall TZ370 | Basic UTM. Single perimeter device. |
| SIEM | None | No log collection whatsoever |
| Backup | Google Drive + local USB | Ad-hoc, no verification, no off-site rotation |
| Training | Google Forms (ad-hoc) | Annual generic 30-min video. 12/14 completed. |

## 4 Contradiction Seeds

| ID | Detection Layer | What's Claimed | What's Real |
|----|----------------|---------------|-------------|
| **SC_01** | intake_contradiction_engine | Firewall exists (SonicWall) | SC.L2-3.13.8 + 3.13.11 Not Implemented |
| **CM_01** | intake_contradiction_engine | CM.L2-3.4.1 Fully Implemented | CM.L2-3.4.8 Not Implemented + 3.4.9 Planned |
| **IA_01** | resolution_engine | MFA fully enforced, all users | Nessus 153953: legacy IMAP/SMTP bypasses 2SV |
| **AC_01** | resolution_engine | Quarterly access reviews | Zero evidence of any review ever conducted |

## Scan Findings — Tier 1 vs Tier 2

Nessus scan: 12 findings across 3 hosts. Two test Tier 1 exact baseline match:
- **96982** (SMBv1 Client Driver) → CIS 18.4.1, `SC.L2-3.13.8`
- **58453** (RDP NLA) → CIS 18.9.1, `AC.L2-3.1.12, IA.L2-3.5.2`

CIS-CAT: 25 rules, 9 pass / 15 fail / 1 error (~36% pass).

## File Inventory

| File | Contents |
|------|----------|
| `company.yaml` | Onboarding wizard payload — org profile + tech stack |
| `company_profile.yaml` | Canonical persona reference (matches company.yaml) |
| `intake.yaml` | Original Phase 2 intake answers with rationale |
| `intake_answers.yaml` | Generated 135 answers (from _gen_meridian_answers.py) |
| `evidence_artifacts.yaml` | 8 evidence artifact definitions |
| `evidence/01-08_*.md` | Evidence content summaries (hallucination detector ground truth) |
| `scans/sample_scan.nessus` | 12 Nessus findings across 3 hosts |
| `scans/sample_ciscat.json` | 25 CIS Win11 rules |
| `contradictions.yaml` | 4 contradictions split by detection_layer |
| `expected_outputs.yaml` | Expected platform state, split intake vs resolution |
| `forbidden.yaml` | Hallucination detector forbidden list |

## Network

Single flat LAN: `192.168.10.0/24`

| Host | IP | Notes |
|------|----|-------|
| sonicwall-gw | 192.168.10.1 | SonicWall TZ370 |
| owner-laptop | 192.168.10.12 | Win11, BitLocker |
| dev-nas | 192.168.10.20 | Synology NAS, TLS 1.0 |
| machine-shop-01-11 | 192.168.10.30-40 | Shop floor PCs |
| shop-pc-03 | 192.168.10.45 | Win10, behind on patches |
| (printer) | 192.168.10.50 | Default credentials |
