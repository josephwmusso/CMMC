"""
src/scanners/nessus_parser.py

Parse .nessus XML and map each finding to NIST 800-171 controls.

Nessus severity scale: 0=Info, 1=Low, 2=Medium, 3=High, 4=Critical.
"""
from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Union

logger = logging.getLogger(__name__)

SEVERITY_MAP = {0: "INFO", 1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}


@dataclass
class NessusFinding:
    host_ip: str
    hostname: Optional[str]
    port: int
    protocol: str
    plugin_id: str
    plugin_name: str
    plugin_family: str
    severity: int
    severity_label: str
    cvss_base_score: Optional[float]
    cvss3_base_score: Optional[float]
    cve_ids: list[str]
    synopsis: str
    description: str
    solution: str
    risk_factor: str
    mapped_control_ids: list[str] = field(default_factory=list)


@dataclass
class NessusScanResult:
    scan_name: str
    scanner_version: Optional[str]
    scan_date: Optional[datetime]
    hosts: list[str]
    findings: list[NessusFinding]
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0


# ── Control-mapping engine ─────────────────────────────────────────────────
# Every successful scan is itself evidence for RA.L2-3.11.2 (vuln scanning
# exists). Individual findings then map to additional controls.

UNIVERSAL_SCAN_CONTROLS = ["RA.L2-3.11.2"]

FAMILY_CONTROL_MAP: dict[str, list[str]] = {
    # Patch management / software flaws
    "Windows": ["SI.L2-3.14.1", "CM.L2-3.4.1"],
    "Ubuntu Local Security Checks": ["SI.L2-3.14.1", "CM.L2-3.4.1"],
    "Red Hat Local Security Checks": ["SI.L2-3.14.1", "CM.L2-3.4.1"],
    "Debian Local Security Checks": ["SI.L2-3.14.1", "CM.L2-3.4.1"],
    "CentOS Local Security Checks": ["SI.L2-3.14.1", "CM.L2-3.4.1"],
    "SuSE Local Security Checks": ["SI.L2-3.14.1", "CM.L2-3.4.1"],
    "MacOS X Local Security Checks": ["SI.L2-3.14.1", "CM.L2-3.4.1"],
    "Misc.": ["SI.L2-3.14.1"],
    # Firewall / network
    "Firewalls": ["SC.L2-3.13.1", "SC.L2-3.13.6"],
    "Junos Local Security Checks": ["SC.L2-3.13.1"],
    "Palo Alto Local Security Checks": ["SC.L2-3.13.1"],
    "CISCO": ["SC.L2-3.13.1"],
    # Configuration / hardening
    "Policy Compliance": ["CM.L2-3.4.1", "CM.L2-3.4.2"],
    "Windows : Microsoft Bulletins": ["SI.L2-3.14.1", "CM.L2-3.4.1"],
    "Windows : User management": ["AC.L2-3.1.1", "AC.L2-3.1.2"],
    # Web
    "Web Servers": ["SC.L2-3.13.1", "SI.L2-3.14.1"],
    "CGI abuses": ["SI.L2-3.14.1"],
    "CGI abuses : XSS": ["SI.L2-3.14.1"],
    # Malware / AV
    "Backdoors": ["SI.L2-3.14.2", "SI.L2-3.14.4"],
    # DNS / Service detection
    "DNS": ["SC.L2-3.13.1"],
    "Service detection": [],
    "Port scanners": [],
    "Settings": [],
    "General": [],
}

# Keyword substring → controls. Used when plugin family doesn't map by itself.
KEYWORD_CONTROL_MAP: dict[str, list[str]] = {
    "ssl": ["SC.L2-3.13.8"],           # CUI in transit
    "tls": ["SC.L2-3.13.8"],
    "certificate": ["SC.L2-3.13.8"],
    "smb signing": ["SC.L2-3.13.8"],
    "password": ["IA.L2-3.5.7"],
    "default credentials": ["IA.L2-3.5.7", "CM.L2-3.4.2"],
    "encryption": ["SC.L2-3.13.11"],   # FIPS crypto
    "antivirus": ["SI.L2-3.14.2"],
    "malware": ["SI.L2-3.14.2"],
    "audit": ["AU.L2-3.3.1"],
    "log": ["AU.L2-3.3.1"],
    "remote desktop": ["AC.L2-3.1.12"],
    "rdp": ["AC.L2-3.1.12"],
    "snmp": ["CM.L2-3.4.2"],
    "telnet": ["CM.L2-3.4.2", "AC.L2-3.1.12"],
    "ftp": ["CM.L2-3.4.2"],
    "ssh": ["AC.L2-3.1.12", "SC.L2-3.13.8"],
    # Legacy authentication protocols → IA (identification & authentication)
    "legacy auth": ["IA.L2-3.5.3"],
    "imap": ["IA.L2-3.5.3"],
    "smtp": ["IA.L2-3.5.3"],
    "pop3": ["IA.L2-3.5.3"],
    "basic auth": ["IA.L2-3.5.3"],
    "less secure app": ["IA.L2-3.5.3"],
    "multi-factor": ["IA.L2-3.5.3"],
    "mfa": ["IA.L2-3.5.3"],
    "two-factor": ["IA.L2-3.5.3"],
    "2-step verification": ["IA.L2-3.5.3"],
}


def map_finding_to_controls(finding: NessusFinding) -> list[str]:
    """Return the list of NIST control IDs this finding contributes to."""
    controls: set[str] = set()

    # Family-based mapping
    controls.update(FAMILY_CONTROL_MAP.get(finding.plugin_family, []))

    # Keyword search over plugin_name + synopsis
    search_text = f"{finding.plugin_name} {finding.synopsis}".lower()
    for keyword, kw_controls in KEYWORD_CONTROL_MAP.items():
        if keyword in search_text:
            controls.update(kw_controls)

    # High/Critical with a patch-worded solution → flaw remediation.
    if finding.severity >= 3 and finding.solution and "patch" in finding.solution.lower():
        controls.add("RA.L2-3.11.3")

    # Medium+ with no other mapping → default to SI.L2-3.14.1.
    if finding.severity >= 2 and not controls:
        controls.add("SI.L2-3.14.1")

    return sorted(controls)


# ── Parser ────────────────────────────────────────────────────────────────

def _parse_scan_date(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    # Nessus format: "Wed Apr 10 14:30:00 2026"
    try:
        return datetime.strptime(raw, "%a %b %d %H:%M:%S %Y")
    except ValueError:
        return None


def parse_nessus_xml(xml_content: Union[bytes, str]) -> NessusScanResult:
    """Parse a .nessus XML payload and return a structured NessusScanResult.

    Raises ET.ParseError on malformed XML and ValueError when the file
    isn't actually a Nessus export.
    """
    if isinstance(xml_content, bytes):
        xml_content = xml_content.decode("utf-8", errors="replace")

    root = ET.fromstring(xml_content)

    report = root.find(".//Report")
    if report is None:
        raise ValueError("No <Report> element — not a valid .nessus file")

    scan_name = report.get("name", "Unknown Scan")

    # Try to pull a version tag from Policy.
    scanner_version: Optional[str] = None
    policy_name = root.find(".//Policy/policyName")
    if policy_name is not None and policy_name.text:
        scanner_version = policy_name.text

    hosts: list[str] = []
    findings: list[NessusFinding] = []
    scan_date: Optional[datetime] = None
    severity_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}

    for report_host in report.findall("ReportHost"):
        host_name = report_host.get("name", "unknown")
        host_ip = host_name
        hostname: Optional[str] = None

        props = report_host.find("HostProperties")
        if props is not None:
            for tag in props.findall("tag"):
                tname = tag.get("name", "")
                if tname == "host-ip" and tag.text:
                    host_ip = tag.text
                elif tname == "hostname" and tag.text:
                    hostname = tag.text
                elif tname == "HOST_START" and tag.text and scan_date is None:
                    scan_date = _parse_scan_date(tag.text)

        if host_ip not in hosts:
            hosts.append(host_ip)

        for item in report_host.findall("ReportItem"):
            severity = int(item.get("severity", "0"))
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            # Skip purely informational findings from the per-finding list
            # (still counted in summary totals).
            if severity == 0:
                continue

            # CVEs — can be multiple <cve> elements.
            cve_ids: list[str] = []
            for cve_elem in item.findall("cve"):
                if cve_elem.text:
                    cve_ids.append(cve_elem.text.strip())

            def _float_text(tag: str) -> Optional[float]:
                el = item.find(tag)
                if el is not None and el.text:
                    try:
                        return float(el.text)
                    except ValueError:
                        return None
                return None

            finding = NessusFinding(
                host_ip=host_ip,
                hostname=hostname,
                port=int(item.get("port", "0")),
                protocol=item.get("protocol", ""),
                plugin_id=item.get("pluginID", "0"),
                plugin_name=item.get("pluginName", "Unknown"),
                plugin_family=item.get("pluginFamily", "General"),
                severity=severity,
                severity_label=SEVERITY_MAP.get(severity, "INFO"),
                cvss_base_score=_float_text("cvss_base_score"),
                cvss3_base_score=_float_text("cvss3_base_score"),
                cve_ids=cve_ids,
                synopsis=(item.findtext("synopsis") or "").strip(),
                description=(item.findtext("description") or "").strip(),
                solution=(item.findtext("solution") or "").strip(),
                risk_factor=(item.findtext("risk_factor") or "None").strip(),
            )

            finding.mapped_control_ids = map_finding_to_controls(finding)
            findings.append(finding)

    return NessusScanResult(
        scan_name=scan_name,
        scanner_version=scanner_version,
        scan_date=scan_date,
        hosts=hosts,
        findings=findings,
        critical_count=severity_counts.get(4, 0),
        high_count=severity_counts.get(3, 0),
        medium_count=severity_counts.get(2, 0),
        low_count=severity_counts.get(1, 0),
        info_count=severity_counts.get(0, 0),
    )


def generate_scan_summary(result: NessusScanResult) -> str:
    """Short human-readable report — used as description on the evidence
    artifact and as the scan_imports.summary_text column."""
    total_actionable = (
        result.critical_count + result.high_count
        + result.medium_count + result.low_count
    )
    all_controls: set[str] = set()
    for f in result.findings:
        all_controls.update(f.mapped_control_ids)

    top = sorted(result.findings, key=lambda f: (-f.severity, f.plugin_id))[:10]

    lines = [
        f"Vulnerability Scan Report: {result.scan_name}",
        f"Scan Date: {result.scan_date.strftime('%Y-%m-%d %H:%M') if result.scan_date else 'Unknown'}",
        f"Hosts Scanned: {len(result.hosts)}",
        "",
        "Severity Summary:",
        f"  Critical: {result.critical_count}",
        f"  High:     {result.high_count}",
        f"  Medium:   {result.medium_count}",
        f"  Low:      {result.low_count}",
        f"  Info:     {result.info_count}",
        f"  Total Actionable: {total_actionable}",
        "",
        f"NIST 800-171 Controls Affected: {len(all_controls)}",
        f"  {', '.join(sorted(all_controls))}" if all_controls else "  (none)",
        "",
        "Top Findings:",
    ]
    for i, f in enumerate(top, 1):
        cve_str = f" ({', '.join(f.cve_ids)})" if f.cve_ids else ""
        lines.append(f"  {i}. [{f.severity_label}] {f.plugin_name}{cve_str}")
        lines.append(f"     Host: {f.host_ip}:{f.port}/{f.protocol}")
        if f.synopsis:
            lines.append(f"     {f.synopsis[:120]}")

    return "\n".join(lines)
