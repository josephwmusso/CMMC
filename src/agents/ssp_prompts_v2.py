"""
src/agents/ssp_prompts_v2.py
Evidence-gated SSP generation prompts.

WHAT CHANGED from ssp_prompts.py:
1. System prompt now includes structured output schema and anti-fabrication rules
2. User prompt template now includes evidence inventory per control
3. When no evidence exists, prompt explicitly instructs gap report generation
4. DEMO_ORG_PROFILE unchanged — still used for inherited evidence claims

Drop-in replacement: rename this to ssp_prompts.py after testing,
or update imports in ssp_generator.py to point here.
"""

from src.agents.ssp_schemas import get_output_schema_prompt


# =============================================================================
# DEMO ORG PROFILE — unchanged from original
# =============================================================================

DEMO_ORG_PROFILE = {
    "org_id": "9de53b587b23450b87af",
    "name": "Apex Defense Solutions",
    "description": "45-employee defense subcontractor specializing in radar signal processing",
    "employee_count": 45,
    "facilities": "Single facility in Columbia, MD with server room and secure workspace",
    "systems": {
        "identity": "Microsoft Entra ID with MFA enforced for all users",
        "email_collaboration": "Microsoft 365 GCC High",
        "endpoint_protection": "CrowdStrike Falcon EDR on all endpoints",
        "network_security": "Palo Alto PA-450 next-gen firewall",
        "siem": "Microsoft Sentinel SIEM with 90-day log retention",
        "network_architecture": "VLAN-segmented network (Corporate, CUI, Guest, Management)",
        "encryption": "BitLocker on all endpoints, TLS 1.2+ for all network traffic",
        "training": "KnowBe4 security awareness platform with monthly phishing simulations",
        "ticketing": "Jira for change management and incident tracking",
        "physical_security": "HID badge readers at all entry points, visitor logs maintained",
    },
    "cui_types": "Technical data (ITAR), specifications, test results",
    "contracts": "DoD subcontractor under DFARS 7012 clause",
}


def format_org_context(org_profile: dict = None) -> str:
    """Format organization profile for prompt inclusion."""
    profile = org_profile or DEMO_ORG_PROFILE
    systems = profile.get("systems", {})

    lines = [
        f"Organization: {profile['name']}",
        f"Description: {profile.get('description', 'N/A')}",
        f"Employee Count: {profile.get('employee_count', 'N/A')}",
        f"Facilities: {profile.get('facilities', 'N/A')}",
        f"CUI Types: {profile.get('cui_types', 'N/A')}",
        f"Contracts: {profile.get('contracts', 'N/A')}",
        "",
        "Technology Stack:",
    ]
    for system_name, system_desc in systems.items():
        lines.append(f"  - {system_name}: {system_desc}")

    return "\n".join(lines)


# =============================================================================
# EVIDENCE-GATED SYSTEM PROMPT
# =============================================================================

SSP_SYSTEM_PROMPT = f"""You are a CMMC Level 2 compliance expert generating System Security Plan
(SSP) implementation narratives for defense contractors. You produce assessor-grade
documentation aligned with NIST SP 800-171 Rev 2 and NIST SP 800-171A assessment methodology.

CRITICAL ANTI-FABRICATION RULES:
1. NEVER fabricate IP addresses, hostnames, MAC addresses, software version numbers,
   configuration file paths, registry keys, usernames, or any technical specifics
   not explicitly present in the provided evidence or organization profile.

2. If a control has NO linked evidence artifacts AND the organization profile does not
   contain information relevant to the control, you MUST:
   - Set implementation_status to "Not Implemented"
   - Write the narrative as a GAP REPORT (see format below)
   - List specific gaps with remediation steps
   - Mark all assessment objectives as "not_met"

3. If a control has PARTIAL evidence (some objectives covered, others not), you MUST:
   - Set implementation_status to "Partially Implemented"
   - Write the narrative covering ONLY what evidence supports
   - Clearly identify which objectives lack evidence
   - List gaps for uncovered objectives

4. You MAY reference the organization profile for "inherited" evidence claims
   (e.g., "Organization uses Microsoft 365 GCC High" -> IA controls for Entra ID).
   These claims must be marked with confidence "inherited" in evidence_references.

5. Every factual claim in the narrative MUST trace to either:
   - A specific evidence artifact (confidence: "direct"), OR
   - A fact stated in the organization profile (confidence: "inherited")
   Claims without traceability are FABRICATION and are NOT ALLOWED.

GAP REPORT FORMAT (for controls without sufficient evidence):
When evidence is insufficient, write the narrative in this structure:
"[CONTROL TITLE] — EVIDENCE GAP REPORT

Current State: [What IS known about the organization's posture for this control,
based on the org profile. If nothing is known, state that explicitly.]

Evidence Needed: [Specific artifacts, screenshots, configs, or policies that would
satisfy this control's assessment objectives.]

Assessment Objectives Not Met: [List each objective ID and what it requires.]

Recommended Actions: [Concrete steps to achieve compliance.]"

{get_output_schema_prompt()}
"""


# =============================================================================
# EVIDENCE-GATED USER PROMPT TEMPLATE
# =============================================================================

SSP_USER_PROMPT_TEMPLATE = """Generate the SSP implementation narrative for the following control.

=== ORGANIZATION CONTEXT ===
{org_context}

=== CONTROL DETAILS ===
Control ID: {control_id}
Control Title: {control_title}
NIST Description: {control_description}
SPRS Point Value: {sprs_points}
POA&M Eligible: {poam_eligible}

=== ASSESSMENT OBJECTIVES ===
{objectives_text}

=== LINKED EVIDENCE ({evidence_count} artifacts) ===
{evidence_section}

=== INSTRUCTIONS ===
{generation_mode_instructions}

Respond with ONLY the JSON object. No other text."""


def build_evidence_section(evidence_artifacts: list[dict]) -> tuple[str, str]:
    """
    Build the evidence section for the prompt and determine generation mode.

    Returns:
        (evidence_text, mode_instructions)
    """
    if not evidence_artifacts:
        evidence_text = "NO EVIDENCE LINKED TO THIS CONTROL.\n"
        mode_instructions = (
            "This control has NO linked evidence. You MUST:\n"
            "1. Set implementation_status to 'Not Implemented'\n"
            "2. Write the narrative as a GAP REPORT (see system prompt format)\n"
            "3. List all assessment objectives as not_met\n"
            "4. Provide specific remediation steps\n"
            "5. DO NOT fabricate any implementation details\n\n"
            "You MAY reference the organization profile for general context about\n"
            "the organization's technology stack, but do NOT claim specific\n"
            "implementation details without evidence."
        )
        return evidence_text, mode_instructions

    # Build evidence inventory
    lines = []
    for i, artifact in enumerate(evidence_artifacts, 1):
        state = artifact.get("state", "UNKNOWN")
        state_warning = ""
        if state != "PUBLISHED":
            state_warning = f" WARNING: STATE={state} (not final - cannot be cited as published evidence)"

        lines.append(
            f"Evidence #{i}:\n"
            f"  Artifact ID: {artifact.get('id', 'N/A')}\n"
            f"  Title: {artifact.get('title', 'N/A')}\n"
            f"  Type: {artifact.get('evidence_type', 'N/A')}\n"
            f"  Source: {artifact.get('source_system', 'N/A')}\n"
            f"  Description: {artifact.get('description', 'N/A')}\n"
            f"  State: {state}{state_warning}\n"
            f"  SHA-256: {artifact.get('sha256_hash', 'N/A')}\n"
        )

    evidence_text = "\n".join(lines)

    # Determine if evidence is sufficient
    published_count = sum(
        1 for a in evidence_artifacts
        if a.get("state", "").upper() == "PUBLISHED"
    )
    total_count = len(evidence_artifacts)

    if published_count == total_count:
        mode_instructions = (
            f"This control has {total_count} PUBLISHED evidence artifact(s).\n"
            "Write an implementation narrative that references these artifacts.\n"
            "Every claim must trace to a specific artifact or the org profile.\n"
            "If the evidence does not cover ALL assessment objectives,\n"
            "mark uncovered objectives as not_met and list gaps."
        )
    elif published_count > 0:
        mode_instructions = (
            f"This control has {total_count} evidence artifact(s), but only "
            f"{published_count} are PUBLISHED (final).\n"
            "Per CMMC scoring rules, only PUBLISHED evidence counts.\n"
            "Write the narrative referencing PUBLISHED artifacts only.\n"
            "Non-published artifacts should be noted as pending review.\n"
            "Set status to 'Partially Implemented' if published evidence\n"
            "doesn't cover all objectives."
        )
    else:
        mode_instructions = (
            f"This control has {total_count} evidence artifact(s), but NONE are PUBLISHED.\n"
            "Per CMMC scoring rules, draft/review evidence cannot support compliance claims.\n"
            "Set implementation_status to 'Not Implemented'.\n"
            "Write the narrative as a GAP REPORT noting that evidence exists but\n"
            "has not completed the review/approval pipeline.\n"
            "List all assessment objectives as not_met."
        )

    return evidence_text, mode_instructions


def build_user_prompt(
    control_id: str,
    control_title: str,
    control_description: str,
    objectives_text: str,
    sprs_points: int,
    poam_eligible: bool,
    evidence_artifacts: list[dict],
    org_profile: dict = None,
) -> str:
    """
    Build the complete user prompt for a single control.
    """
    evidence_section, mode_instructions = build_evidence_section(evidence_artifacts)

    return SSP_USER_PROMPT_TEMPLATE.format(
        org_context=format_org_context(org_profile),
        control_id=control_id,
        control_title=control_title,
        control_description=control_description,
        sprs_points=sprs_points,
        poam_eligible="Yes" if poam_eligible else "No (CA.L2-3.12.4 hard-block)" if control_id == "CA.L2-3.12.4" else "No",
        objectives_text=objectives_text,
        evidence_count=len(evidence_artifacts),
        evidence_section=evidence_section,
        generation_mode_instructions=mode_instructions,
    )
