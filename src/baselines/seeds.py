"""
src/baselines/seeds.py

Seed two hand-curated security baselines into the shared catalog:
  - CIS Microsoft Windows 11 Enterprise L1 v3.0  (25 items, each keyed to
    known Nessus plugin IDs for precision matching)
  - CIS Microsoft 365 Foundations L1 v3.1        (20 items, keyword only —
    Nessus doesn't scan M365; CIS-CAT JSON will drive these later)

Called from scripts/render_startup.py after tables exist. Re-seeds when
the baselines are stale (no match_plugin_ids populated) by wiping
dependent rows first.
"""
from __future__ import annotations

import hashlib
import logging

logger = logging.getLogger(__name__)


def _bid(seed: bytes | str) -> str:
    if isinstance(seed, str):
        seed = seed.encode()
    return hashlib.sha256(seed).hexdigest()[:20]


def _item_id(baseline_id: str, cis_id: str) -> str:
    return _bid(f"{baseline_id}:{cis_id}")


# ── Windows 11 L1 v3.0 ─────────────────────────────────────────────────────
# Tuple shape:
#   (cis_id, section, title, expected_value, severity,
#    control_ids, match_keywords, match_plugin_families, match_plugin_ids)
WIN11_BASELINE_ID = _bid("cis-win11-l1-v3.0")

WIN11_ITEMS = [
    ("1.1.1", "Account Policies > Password Policy", "Enforce password history",
     "24 or more passwords remembered", "MEDIUM",
     ["IA.L2-3.5.7"],
     ["password history", "password policy"],
     ["Windows", "Policy Compliance"],
     ["63063"]),
    ("1.1.2", "Account Policies > Password Policy", "Maximum password age",
     "365 or fewer days", "MEDIUM",
     ["IA.L2-3.5.8"],
     ["password age", "password expir"],
     ["Windows", "Policy Compliance"],
     ["63064"]),
    ("1.1.3", "Account Policies > Password Policy", "Minimum password age",
     "1 or more days", "LOW",
     ["IA.L2-3.5.8"],
     ["minimum password age"],
     ["Windows", "Policy Compliance"],
     ["63065"]),
    ("1.1.4", "Account Policies > Password Policy", "Minimum password length",
     "14 or more characters", "HIGH",
     ["IA.L2-3.5.7"],
     ["password length", "minimum password"],
     ["Windows", "Policy Compliance"],
     ["63060"]),
    ("1.1.5", "Account Policies > Password Policy", "Password must meet complexity requirements",
     "Enabled", "HIGH",
     ["IA.L2-3.5.7"],
     ["password complexity", "complexity requirements"],
     ["Windows", "Policy Compliance"],
     ["63061"]),
    ("1.2.1", "Account Policies > Account Lockout Policy", "Account lockout duration",
     "15 or more minutes", "MEDIUM",
     ["AC.L2-3.1.8"],
     ["account lockout", "lockout duration"],
     ["Windows", "Policy Compliance"],
     ["63066"]),
    ("1.2.2", "Account Policies > Account Lockout Policy", "Account lockout threshold",
     "5 or fewer invalid logon attempts", "HIGH",
     ["AC.L2-3.1.8"],
     ["lockout threshold", "failed logon"],
     ["Windows", "Policy Compliance"],
     ["63062"]),
    ("2.2.1", "Local Policies > User Rights Assignment", "Deny access to this computer from the network — Guest",
     "Configured to include Guests", "HIGH",
     ["AC.L2-3.1.1"],
     ["guest account", "deny access", "network access"],
     ["Windows", "Policy Compliance"],
     ["44690"]),
    ("2.3.1", "Local Policies > Security Options", "Audit: Force audit policy subcategory settings",
     "Enabled", "MEDIUM",
     ["AU.L2-3.3.1"],
     ["audit policy", "subcategory"],
     ["Windows", "Policy Compliance"],
     ["78430"]),
    ("5.1.1", "System Services", "Disable unnecessary system services",
     "Per benchmark recommendation", "MEDIUM",
     ["CM.L2-3.4.7"],
     ["unnecessary service", "disable service"],
     ["Windows", "Policy Compliance"],
     ["55901"]),
    ("9.1.1", "Windows Defender Firewall > Domain Profile", "Firewall state",
     "On", "CRITICAL",
     ["SC.L2-3.13.1", "SC.L2-3.13.5"],
     ["windows firewall", "firewall domain", "firewall state"],
     ["Windows", "Firewalls"],
     ["56210", "56211"]),
    ("9.2.1", "Windows Defender Firewall > Private Profile", "Firewall state",
     "On", "CRITICAL",
     ["SC.L2-3.13.1", "SC.L2-3.13.5"],
     ["windows firewall", "firewall private"],
     ["Windows", "Firewalls"],
     ["56212", "56213"]),
    ("9.3.1", "Windows Defender Firewall > Public Profile", "Firewall state",
     "On", "CRITICAL",
     ["SC.L2-3.13.1", "SC.L2-3.13.5"],
     ["windows firewall", "firewall public"],
     ["Windows", "Firewalls"],
     ["56214", "56215"]),
    ("17.1.1", "Advanced Audit Policy > Account Logon", "Audit Credential Validation",
     "Success and Failure", "MEDIUM",
     ["AU.L2-3.3.1", "AU.L2-3.3.2"],
     ["credential validation", "audit logon"],
     ["Windows", "Policy Compliance"],
     ["78432"]),
    ("17.2.1", "Advanced Audit Policy > Account Management", "Audit Application Group Management",
     "Success and Failure", "MEDIUM",
     ["AU.L2-3.3.1"],
     ["group management", "audit account"],
     ["Windows", "Policy Compliance"],
     ["78435"]),
    ("17.5.1", "Advanced Audit Policy > Logon/Logoff", "Audit Logoff",
     "Success", "LOW",
     ["AU.L2-3.3.1", "AU.L2-3.3.2"],
     ["audit logoff"],
     ["Windows", "Policy Compliance"],
     ["78437"]),
    ("17.5.2", "Advanced Audit Policy > Logon/Logoff", "Audit Logon",
     "Success and Failure", "MEDIUM",
     ["AU.L2-3.3.1", "AU.L2-3.3.2"],
     ["audit logon", "logon events"],
     ["Windows", "Policy Compliance"],
     ["78433"]),
    ("17.9.1", "Advanced Audit Policy > Object Access", "Audit Removable Storage",
     "Success and Failure", "MEDIUM",
     ["AU.L2-3.3.1", "MP.L2-3.8.7"],
     ["removable storage", "usb audit"],
     ["Windows", "Policy Compliance"],
     ["78440"]),
    ("18.4.1", "Administrative Templates > MS Security Guide", "Configure SMB v1 client driver",
     "Disable driver", "CRITICAL",
     ["SC.L2-3.13.8"],
     ["smb v1", "smbv1", "smb1"],
     ["Windows", "Misc."],
     ["96982"]),
    ("18.5.1", "Administrative Templates > MSS (Legacy)", "MSS: Screen saver grace period",
     "5 seconds or less", "MEDIUM",
     ["AC.L2-3.1.10"],
     ["screen saver", "screensaver", "session lock"],
     ["Windows", "Policy Compliance"],
     ["63070"]),
    ("18.8.1", "Administrative Templates > BitLocker Drive Encryption", "Require encryption on all fixed drives",
     "Enabled", "HIGH",
     ["MP.L2-3.8.6", "SC.L2-3.13.16"],
     ["bitlocker", "drive encryption"],
     ["Windows", "Policy Compliance"],
     ["82034"]),
    ("18.9.1", "Administrative Templates > Remote Desktop Services", "Require user authentication for remote connections by using Network Level Authentication",
     "Enabled", "HIGH",
     ["AC.L2-3.1.12", "IA.L2-3.5.2"],
     ["remote desktop", "nla", "network level auth"],
     ["Windows", "Policy Compliance"],
     ["58453"]),
    ("18.9.2", "Administrative Templates > Remote Desktop Services", "Set client connection encryption level",
     "High Level", "HIGH",
     ["SC.L2-3.13.8"],
     ["rdp encryption", "remote desktop encrypt"],
     ["Windows", "Policy Compliance"],
     ["58454"]),
    ("18.10.1", "Administrative Templates > AutoPlay Policies", "Turn off Autoplay",
     "Enabled (disable Autoplay)", "MEDIUM",
     ["CM.L2-3.4.6"],
     ["autorun", "autoplay"],
     ["Windows", "Policy Compliance"],
     ["55803"]),
    ("18.10.2", "Administrative Templates > Windows Defender", "Turn off Microsoft Defender Antivirus",
     "Disabled (Defender enabled)", "HIGH",
     ["SI.L2-3.14.2"],
     ["windows defender", "antimalware", "real-time protection"],
     ["Windows", "Policy Compliance"],
     ["91301"]),
]


# ── Microsoft 365 Foundations L1 v3.1 ──────────────────────────────────────
# Nessus doesn't scan M365 cloud configs, so plugin_ids is None for every
# item — these fall back to keyword matching (used by CIS-CAT in Phase 3.2).
M365_BASELINE_ID = _bid("cis-m365-l1-v3.1")

M365_ITEMS = [
    ("1.1.1", "Identity > Multi-Factor Authentication", "Enable MFA for all users",
     "Enabled", "CRITICAL",
     ["IA.L2-3.5.3"],
     ["multi-factor", "mfa", "conditional access"],
     None,
     None),
    ("1.1.2", "Identity > Conditional Access", "Security defaults or Conditional Access configured",
     "Configured", "CRITICAL",
     ["IA.L2-3.5.3", "AC.L2-3.1.1"],
     ["security defaults", "conditional access"],
     None,
     None),
    ("1.1.3", "Identity > Authentication", "Block legacy authentication protocols",
     "Enabled", "HIGH",
     ["AC.L2-3.1.1", "IA.L2-3.5.3"],
     ["legacy auth", "legacy protocol", "basic auth"],
     None,
     None),
    ("1.2.1", "Identity > Privileged Accounts", "Privileged accounts are cloud-only",
     "Configured", "HIGH",
     ["AC.L2-3.1.5", "AC.L2-3.1.6"],
     ["privileged account", "admin account", "cloud-only"],
     None,
     None),
    ("1.3.1", "Identity > Password Management", "Self-service password reset configured",
     "Configured", "MEDIUM",
     ["IA.L2-3.5.8"],
     ["self-service password", "sspr"],
     None,
     None),
    ("2.1.1", "Auditing > Unified Audit Log", "Audit log search enabled",
     "Enabled", "HIGH",
     ["AU.L2-3.3.1", "AU.L2-3.3.2"],
     ["audit log", "unified audit"],
     None,
     None),
    ("2.1.2", "Auditing > Retention", "Audit log retention ≥ 1 year",
     "1 year minimum", "HIGH",
     ["AU.L2-3.3.1"],
     ["audit retention", "log retention"],
     None,
     None),
    ("3.1.1", "Data Protection > SharePoint Sharing", "External sharing restricted",
     "Limited", "HIGH",
     ["AC.L2-3.1.3", "AC.L2-3.1.22"],
     ["external sharing", "sharepoint sharing"],
     None,
     None),
    ("3.2.1", "Data Protection > Guest Access", "SharePoint guest access controlled",
     "Restricted", "MEDIUM",
     ["AC.L2-3.1.3", "AC.L2-3.1.22"],
     ["guest access", "external user"],
     None,
     None),
    ("4.1.1", "Data Protection > DLP", "DLP policies configured for CUI",
     "Configured", "HIGH",
     ["MP.L2-3.8.1", "MP.L2-3.8.2"],
     ["data loss prevention", "dlp", "sensitivity label"],
     None,
     None),
    ("4.2.1", "Data Protection > Sensitivity Labels", "Sensitivity labels for CUI",
     "Configured", "HIGH",
     ["MP.L2-3.8.1"],
     ["sensitivity label", "classification"],
     None,
     None),
    ("5.1.1", "Device Management > MDM", "Mobile device management configured",
     "Configured", "HIGH",
     ["AC.L2-3.1.18", "MP.L2-3.8.1"],
     ["mobile device", "mdm", "intune"],
     None,
     None),
    ("5.2.1", "Device Management > Compliance", "Device compliance policies configured",
     "Configured", "MEDIUM",
     ["CM.L2-3.4.1", "CM.L2-3.4.2"],
     ["device compliance", "compliance policy"],
     None,
     None),
    ("6.1.1", "Email > Anti-Malware", "Anti-malware protection for Exchange Online",
     "Enabled", "HIGH",
     ["SI.L2-3.14.2", "SI.L2-3.14.5"],
     ["anti-malware", "malware filter", "exchange protection"],
     None,
     None),
    ("6.2.1", "Email > Safe Attachments", "Safe Attachments policy enabled",
     "Enabled", "HIGH",
     ["SI.L2-3.14.2"],
     ["safe attachments", "atp"],
     None,
     None),
    ("6.3.1", "Email > Safe Links", "Safe Links policy enabled",
     "Enabled", "MEDIUM",
     ["SI.L2-3.14.2"],
     ["safe links", "url protection"],
     None,
     None),
    ("7.1.1", "Teams > External Access", "Teams external access restricted",
     "Restricted", "MEDIUM",
     ["AC.L2-3.1.3", "AC.L2-3.1.20"],
     ["teams external", "external access", "federation"],
     None,
     None),
    ("7.2.1", "Teams > Guest Access", "Teams guest access controlled",
     "Controlled", "MEDIUM",
     ["AC.L2-3.1.3"],
     ["teams guest", "guest access teams"],
     None,
     None),
    ("8.1.1", "Identity Protection > Sign-in Risk", "Azure AD sign-in risk policy configured",
     "Configured", "HIGH",
     ["SI.L2-3.14.6", "SI.L2-3.14.7"],
     ["sign-in risk", "risk policy", "identity protection"],
     None,
     None),
    ("8.2.1", "Identity Protection > User Risk", "Azure AD user risk policy configured",
     "Configured", "HIGH",
     ["SI.L2-3.14.6", "SI.L2-3.14.7"],
     ["user risk", "compromised account"],
     None,
     None),
]


# ── Seeding ────────────────────────────────────────────────────────────────

_INSERT_BASELINE = """
INSERT INTO baselines (id, name, version, source, platform, description, item_count)
VALUES (%s, %s, %s, %s, %s, %s, 0)
ON CONFLICT (id) DO NOTHING
"""

_INSERT_ITEM = """
INSERT INTO baseline_items
    (id, baseline_id, cis_id, section, title, expected_value,
     severity, control_ids, match_keywords, match_plugin_families,
     match_plugin_ids)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (id) DO NOTHING
"""


def _insert_baseline(cur, baseline_id: str, name: str, version: str,
                     source: str, platform: str, description: str,
                     items: list) -> None:
    cur.execute(_INSERT_BASELINE, (baseline_id, name, version, source, platform, description))
    for row in items:
        (cis_id, section, title, expected_value, severity,
         control_ids, match_keywords, match_plugin_families,
         match_plugin_ids) = row
        cur.execute(
            _INSERT_ITEM,
            (
                _item_id(baseline_id, cis_id),
                baseline_id,
                cis_id,
                section,
                title,
                expected_value,
                severity,
                control_ids,
                match_keywords,
                match_plugin_families,
                match_plugin_ids,
            ),
        )


def _catalog_is_fresh(cur) -> bool:
    """True iff any baseline_items row has match_plugin_ids populated —
    signal that the 3.3C seed has already been applied."""
    cur.execute("""
        SELECT COUNT(*) FROM baseline_items
        WHERE match_plugin_ids IS NOT NULL
          AND array_length(match_plugin_ids, 1) > 0
    """)
    return (cur.fetchone()[0] or 0) > 0


def _wipe_catalog(cur) -> None:
    """Drop dependent rows then the catalog so we can re-seed cleanly.

    Safe because:
      - baseline_deviations is regenerated on the next /match call
      - org_baselines is cheap to re-adopt (UI click)
      - the catalog itself is shared seed data, not user content
    """
    cur.execute("DELETE FROM baseline_deviations")
    cur.execute("DELETE FROM org_baselines")
    cur.execute("DELETE FROM baseline_items")
    cur.execute("DELETE FROM baselines")


def seed_baselines(cur) -> None:
    """Seed baselines + baseline_items.

    Idempotent guard: if the catalog already has match_plugin_ids
    populated it's up to date; otherwise wipe the stale catalog (and
    everything that depends on it) and reseed with plugin IDs.
    """
    cur.execute("SELECT COUNT(*) FROM baselines")
    existing = cur.fetchone()[0]

    if existing > 0:
        if _catalog_is_fresh(cur):
            logger.info(f"  baselines: {existing} already seeded with plugin IDs, skipping")
            return
        logger.info(f"  baselines: stale catalog detected, wiping and re-seeding for 3.3C")
        _wipe_catalog(cur)

    _insert_baseline(
        cur,
        WIN11_BASELINE_ID,
        "CIS Microsoft Windows 11 Enterprise Benchmark L1",
        "3.0.0",
        "CIS",
        "Windows 11 Enterprise",
        "Level 1 hardening baseline for Windows 11 Enterprise endpoints.",
        WIN11_ITEMS,
    )
    _insert_baseline(
        cur,
        M365_BASELINE_ID,
        "CIS Microsoft 365 Foundations Benchmark L1",
        "3.1.0",
        "CIS",
        "Microsoft 365",
        "Level 1 foundational configuration baseline for Microsoft 365 tenants.",
        M365_ITEMS,
    )

    cur.execute("""
        UPDATE baselines b
        SET item_count = sub.cnt
        FROM (
            SELECT baseline_id, COUNT(*) AS cnt
            FROM baseline_items
            GROUP BY baseline_id
        ) sub
        WHERE b.id = sub.baseline_id
    """)

    cur.execute("SELECT COUNT(*) FROM baselines")
    baselines_ct = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM baseline_items")
    items_ct = cur.fetchone()[0]
    cur.execute("""
        SELECT COUNT(*) FROM baseline_items
        WHERE match_plugin_ids IS NOT NULL
          AND array_length(match_plugin_ids, 1) > 0
    """)
    with_pids = cur.fetchone()[0]
    logger.info(
        f"  baselines: seeded {baselines_ct} baselines, {items_ct} items "
        f"({with_pids} with plugin IDs)"
    )
