"""
src/agents/hallucination_detector.py
Post-generation verification for SSP narratives.

Checks for:
1. Fabricated IP addresses not present in evidence or org profile
2. Fabricated hostnames / server names
3. Fabricated software versions
4. Fabricated file paths / registry keys
5. Fabricated dates (specific dates not in evidence)
6. Claims about evidence that doesn't exist

Returns a VerificationResult with pass/fail and specific findings.
"""

import re
from dataclasses import dataclass, field


@dataclass
class HallucinationFinding:
    """A single suspected hallucination."""
    finding_type: str          # ip_address, hostname, version, path, date, phantom_evidence
    value: str                 # The suspicious value found
    context: str               # Surrounding text
    severity: str              # critical, warning, info


@dataclass
class VerificationResult:
    """Result of hallucination verification on an SSP section."""
    control_id: str
    passed: bool
    findings: list[HallucinationFinding] = field(default_factory=list)
    critical_count: int = 0
    warning_count: int = 0

    def summary(self) -> str:
        if self.passed:
            return f"[PASS] {self.control_id}: No hallucination indicators detected"
        return (
            f"[FAIL] {self.control_id}: {self.critical_count} critical, "
            f"{self.warning_count} warning findings"
        )


# =============================================================================
# Known-good values from the Apex Defense Solutions org profile
# These would be loaded from the DB in production; hardcoded for demo org.
# =============================================================================

KNOWN_ORG_IPS = set()  # No specific IPs in org profile — any IP is suspect

KNOWN_ORG_HOSTNAMES = {
    "apex defense solutions",
    "microsoft 365", "m365", "gcc high",
    "microsoft entra id", "entra id", "azure ad",
    "crowdstrike falcon", "crowdstrike",
    "palo alto pa-450", "palo alto",
    "microsoft sentinel", "sentinel",
    "bitlocker",
    "knowbe4",
    "jira",
    "hid",
}

KNOWN_SOFTWARE = {
    "microsoft 365 gcc high",
    "crowdstrike falcon edr",
    "palo alto pa-450",
    "microsoft sentinel",
    "bitlocker",
    "knowbe4",
    "jira",
    "tls 1.2",
    "tls 1.3",
}


# =============================================================================
# Detection patterns
# =============================================================================

# RFC 1918 private IPs and general IPs
IP_PATTERN = re.compile(
    r'\b(?:(?:10|172\.(?:1[6-9]|2[0-9]|3[01])|192\.168)\.\d{1,3}\.\d{1,3})\b'
    r'|'
    r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
)

# Hostnames: require structural signals (hyphen + alphanumeric, or FQDN).
# Never flag bare acronyms like AD, CA, PKI, DNS, MFA, EDR, etc.
SAFE_ACRONYMS = {
    "AD", "AAD", "MFA", "SSO", "PKI", "CAC", "PIV", "SAML", "OAUTH", "LDAP", "RADIUS",
    "EDR", "XDR", "MDR", "SIEM", "SOAR", "DLP", "IDS", "IPS", "WAF", "NAC", "MDM",
    "AV", "EPP", "NGFW", "UTM", "VPN", "ZTNA", "CASB", "UEBA",
    "AWS", "GCP", "CSP", "VM", "VDI",
    "CUI", "CTI", "CDI", "FCI", "CMMC", "NIST", "FIPS", "DFARS", "ITAR", "EAR",
    "RMF", "ATO", "ATC", "SSP", "RAR", "SAR", "SAP", "POA", "POAM",
    "SPRS", "DIBCAC", "DIB", "ISSO", "ISSM", "CISO", "CIO",
    "TCP", "UDP", "IP", "DNS", "NTP", "DHCP", "SNMP", "HTTP", "HTTPS",
    "TLS", "SSL", "SSH", "FTP", "SFTP", "SCP", "RDP", "SMB", "LDAPS",
    "VLAN", "WLAN", "LAN", "WAN", "DMZ", "NAT", "VPC", "ACL",
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
    "LLC", "INC", "LTD", "GCC", "NAS", "SAN", "UPS",
    "API", "SDK", "CLI", "GUI", "SQL", "PDF", "CSV", "JSON", "XML", "YAML",
    "CPU", "GPU", "RAM", "SSD", "HDD",
    "DB", "FS",  # Database, FileSystem — NOT hostnames by themselves
}


# Compound adjectives/terms that contain hyphens but aren't hostnames
_COMPOUND_EXCLUDE = {
    "role-based", "risk-based", "need-to-know", "deny-by-default",
    "least-privilege", "multi-factor", "two-factor", "non-compliant",
    "real-time", "end-to-end", "up-to-date", "out-of-date", "day-to-day",
    "on-premises", "on-premise", "air-gapped", "off-site", "on-site",
    "pass-through", "write-once", "read-only", "sign-in", "log-in",
    "third-party", "single-factor", "time-based", "cloud-based",
    "web-based", "host-based", "network-based", "file-based",
    "agent-based", "policy-based", "compliance-based", "evidence-based",
    "security-aware", "cyber-aware", "well-known", "re-evaluate",
    "pre-defined", "co-located", "de-provision", "re-provision",
    "access-control", "change-management", "incident-response",
}


def _is_potential_hostname(token: str) -> bool:
    """True only if token structurally looks like a hostname, not an acronym."""
    if token.upper() in SAFE_ACRONYMS:
        return False
    if token.isupper() and len(token) <= 5:
        return False
    if token.lower() in _COMPOUND_EXCLUDE:
        return False
    # Hyphenated: dev-nas, shop-pc-03, dc-primary-01
    # Require at least one segment to contain a digit OR be a known host prefix
    if "-" in token and re.match(r'^[a-zA-Z][a-zA-Z0-9-]+[a-zA-Z0-9]$', token):
        parts = token.lower().split("-")
        has_digit = any(any(c.isdigit() for c in p) for p in parts)
        has_host_prefix = parts[0] in {"dev", "srv", "dc", "fs", "web", "app", "db",
                                         "mail", "file", "print", "shop", "owner",
                                         "server", "win", "exchange", "sql"}
        if has_digit or has_host_prefix:
            return True
        return False
    # FQDN: server.domain.local
    if re.match(r'^[a-zA-Z][a-zA-Z0-9-]*\.[a-zA-Z0-9.-]+$', token):
        return True
    # Mixed alpha+digit >=6 chars: server01, win2019
    if len(token) >= 6 and re.match(r'^[a-zA-Z][a-zA-Z0-9]+$', token) and any(c.isdigit() for c in token):
        return True
    return False


# Inline assertion battery — runs on import
_MUST_NOT_MATCH = [
    "AD", "MFA", "EDR", "CUI", "DLP", "SIEM", "KS", "MD", "VA", "PKI",
    "RMF", "ATO", "SSO", "TLS", "SSH", "FTP", "RDP", "NTP", "DNS", "VLAN",
    "CSP", "MDM", "SOC", "MSP", "ISSO", "ISSM", "GCC", "LLC", "CA", "NAS",
    "VPN", "ACL", "DMZ", "NAT", "SQL", "PDF", "API", "SDK", "CLI", "DB", "FS",
    # Compound adjectives
    "role-based", "need-to-know", "deny-by-default", "real-time",
    "multi-factor", "on-premises", "air-gapped", "third-party",
    "access-control", "least-privilege", "risk-based",
]
_MUST_MATCH = [
    "dev-nas", "shop-pc-03", "owner-laptop", "dc-primary-01",
    "server-backup-02", "win2019srv", "exchange01",
]
for _t in _MUST_NOT_MATCH:
    assert not _is_potential_hostname(_t), f"SAFE_ACRONYMS failed: '{_t}' should not match"
for _t in _MUST_MATCH:
    assert _is_potential_hostname(_t), f"Hostname detection failed: '{_t}' should match"


# Token extraction pattern — finds word-like tokens to test
_TOKEN_PATTERN = re.compile(r'\b[a-zA-Z][a-zA-Z0-9._-]{1,30}\b')

# Specific version numbers (e.g., "version 10.4.2", "v3.2.1")
VERSION_PATTERN = re.compile(
    r'\b[vV]?\d+\.\d+\.\d+(?:\.\d+)?\b'
)

# Windows registry keys
REGISTRY_PATTERN = re.compile(
    r'HKEY_(?:LOCAL_MACHINE|CURRENT_USER|CLASSES_ROOT)\\[\w\\]+',
    re.IGNORECASE
)

# File paths (Windows or Linux)
FILE_PATH_PATTERN = re.compile(
    r'(?:[A-Z]:\\(?:[\w\s.-]+\\){2,}[\w\s.-]+)'
    r'|'
    r'(?:/(?:etc|var|usr|opt|home)/(?:[\w.-]+/){1,}[\w.-]+)',
    re.IGNORECASE
)

# Specific dates (e.g., "March 15, 2025", "2025-03-15", "03/15/2025")
SPECIFIC_DATE_PATTERN = re.compile(
    r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)'
    r'\s+\d{1,2},?\s+\d{4}\b'
    r'|'
    r'\b\d{4}-\d{2}-\d{2}\b'
    r'|'
    r'\b\d{1,2}/\d{1,2}/\d{4}\b'
)

# Subnet masks / CIDR
SUBNET_PATTERN = re.compile(
    r'\b(?:\d{1,3}\.){3}\d{1,3}/\d{1,2}\b'
)

# MAC addresses
MAC_PATTERN = re.compile(
    r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b'
)


def verify_narrative(
    control_id: str,
    narrative: str,
    evidence_artifacts: list[dict],
    org_profile: dict = None,
) -> VerificationResult:
    """
    Verify an SSP narrative for hallucination indicators.
    """
    findings = []

    # Build set of known-good values from evidence
    evidence_text_corpus = ""
    evidence_ids = set()
    for artifact in evidence_artifacts:
        evidence_ids.add(artifact.get("id", ""))
        for field_name in ("title", "description", "source_system"):
            val = artifact.get(field_name, "")
            if val:
                evidence_text_corpus += f" {val}"

    # --- Check 1: IP addresses ---
    for match in IP_PATTERN.finditer(narrative):
        ip = match.group()
        if ip in evidence_text_corpus:
            continue
        if ip in ("0.0.0.0", "127.0.0.1", "255.255.255.255"):
            continue
        context = narrative[max(0, match.start()-40):match.end()+40]
        findings.append(HallucinationFinding(
            finding_type="ip_address",
            value=ip,
            context=f"...{context}...",
            severity="critical"
        ))

    # --- Check 2: Fabricated hostnames ---
    for match in _TOKEN_PATTERN.finditer(narrative):
        token = match.group()
        if not _is_potential_hostname(token):
            continue
        if token.lower() in evidence_text_corpus.lower():
            continue
        context = narrative[max(0, match.start()-40):match.end()+40]
        findings.append(HallucinationFinding(
            finding_type="hostname",
            value=token,
            context=f"...{context}...",
            severity="critical"
        ))

    # --- Check 3: Specific version numbers ---
    for match in VERSION_PATTERN.finditer(narrative):
        version = match.group()
        if version in ("1.2", "1.3"):  # TLS versions from org profile
            continue
        if version in evidence_text_corpus:
            continue
        # NIST control ID suffixes (3.1.1, 3.5.3, 3.13.11) are legitimate
        pre = narrative[max(0, match.start()-5):match.start()]
        if "L2-" in pre or "800-" in pre or "171" in pre:
            continue
        context = narrative[max(0, match.start()-40):match.end()+40]
        findings.append(HallucinationFinding(
            finding_type="version",
            value=version,
            context=f"...{context}...",
            severity="warning"
        ))

    # --- Check 4: Registry keys / file paths ---
    for pattern, ftype in [
        (REGISTRY_PATTERN, "registry_key"),
        (FILE_PATH_PATTERN, "file_path"),
    ]:
        for match in pattern.finditer(narrative):
            value = match.group()
            if value in evidence_text_corpus:
                continue
            context = narrative[max(0, match.start()-40):match.end()+40]
            findings.append(HallucinationFinding(
                finding_type=ftype,
                value=value,
                context=f"...{context}...",
                severity="warning"
            ))

    # --- Check 5: Specific fabricated dates ---
    # Well-known publication dates that should never be flagged
    _KNOWN_PUB_DATES = {
        "February 2020", "June 2018", "May 2024", "November 2025",
        "December 2024",  # CMMC final rule publication
    }
    for match in SPECIFIC_DATE_PATTERN.finditer(narrative):
        date_str = match.group()
        if date_str in evidence_text_corpus:
            continue
        # Skip well-known NIST/CMMC publication dates
        if any(kd in date_str or date_str in kd for kd in _KNOWN_PUB_DATES):
            continue
        # Fuzzy year-month grounding: extract year from the date and check
        # if the year appears in evidence context (most legitimate dates
        # reference the same timeframe as evidence artifacts)
        year_match = re.search(r'(\d{4})', date_str)
        if year_match and year_match.group(1) in evidence_text_corpus:
            continue
        context = narrative[max(0, match.start()-40):match.end()+40]
        findings.append(HallucinationFinding(
            finding_type="ungrounded_date",
            value=date_str,
            context=f"...{context}...",
            severity="warning"
        ))

    # --- Check 6: Subnet/CIDR and MAC addresses ---
    for pattern, ftype in [
        (SUBNET_PATTERN, "subnet"),
        (MAC_PATTERN, "mac_address"),
    ]:
        for match in pattern.finditer(narrative):
            value = match.group()
            if value in evidence_text_corpus:
                continue
            context = narrative[max(0, match.start()-40):match.end()+40]
            findings.append(HallucinationFinding(
                finding_type=ftype,
                value=value,
                context=f"...{context}...",
                severity="critical"
            ))

    # --- Tally results ---
    critical_count = sum(1 for f in findings if f.severity == "critical")
    warning_count = sum(1 for f in findings if f.severity == "warning")

    return VerificationResult(
        control_id=control_id,
        passed=(critical_count == 0),
        findings=findings,
        critical_count=critical_count,
        warning_count=warning_count,
    )


def verify_evidence_references(
    control_id: str,
    claimed_artifact_ids: list[str],
    actual_artifact_ids: set[str],
) -> list[HallucinationFinding]:
    """
    Check that every artifact_id referenced in the narrative
    actually exists in the evidence linked to this control.
    """
    findings = []
    for claimed_id in claimed_artifact_ids:
        if claimed_id and claimed_id not in actual_artifact_ids:
            findings.append(HallucinationFinding(
                finding_type="phantom_evidence",
                value=claimed_id,
                context=f"Narrative references artifact '{claimed_id}' which is not linked to {control_id}",
                severity="critical"
            ))
    return findings


def run_verification(
    control_id: str,
    parsed_output: dict,
    evidence_artifacts: list[dict],
    org_profile: dict = None,
) -> VerificationResult:
    """
    Full verification pipeline for a parsed SSP section.
    """
    narrative = parsed_output.get("narrative", "")

    # Step 1: Check narrative for fabricated values
    result = verify_narrative(control_id, narrative, evidence_artifacts, org_profile)

    # Step 2: Check evidence references
    actual_ids = {a.get("id", "") for a in evidence_artifacts}
    claimed_ids = [
        ref.get("artifact_id")
        for ref in parsed_output.get("evidence_references", [])
        if ref.get("artifact_id")
    ]
    phantom_findings = verify_evidence_references(control_id, claimed_ids, actual_ids)
    result.findings.extend(phantom_findings)
    result.critical_count += sum(1 for f in phantom_findings if f.severity == "critical")
    result.passed = result.passed and (len(phantom_findings) == 0)

    return result
