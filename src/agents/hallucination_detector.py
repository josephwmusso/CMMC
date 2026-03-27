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

# Hostnames that look fabricated (e.g., SRV-DC01, FILESERVER-01, etc.)
HOSTNAME_PATTERN = re.compile(
    r'\b(?:SRV|DC|FS|FILE|MAIL|WEB|APP|DB|SQL|AD|DNS|DHCP|CA|PKI|WSUS|SCCM|PRINT)'
    r'[-_]?\d{0,3}\b',
    re.IGNORECASE
)

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
    for match in HOSTNAME_PATTERN.finditer(narrative):
        hostname = match.group()
        if hostname.lower() in evidence_text_corpus.lower():
            continue
        context = narrative[max(0, match.start()-40):match.end()+40]
        findings.append(HallucinationFinding(
            finding_type="hostname",
            value=hostname,
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
    for match in SPECIFIC_DATE_PATTERN.finditer(narrative):
        date_str = match.group()
        if date_str in evidence_text_corpus:
            continue
        context = narrative[max(0, match.start()-40):match.end()+40]
        findings.append(HallucinationFinding(
            finding_type="specific_date",
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
