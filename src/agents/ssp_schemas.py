"""
src/agents/ssp_schemas.py
Structured output schemas for SSP generation.
Forces the LLM to produce typed, verifiable output instead of free-form text.
"""

from pydantic import BaseModel, Field, field_validator
from enum import Enum
from typing import Optional


class ImplementationStatus(str, Enum):
    IMPLEMENTED = "Implemented"
    PARTIALLY_IMPLEMENTED = "Partially Implemented"
    NOT_IMPLEMENTED = "Not Implemented"
    NOT_APPLICABLE = "Not Applicable"


class EvidenceConfidence(str, Enum):
    """How confident we are that evidence supports this claim."""
    DIRECT = "direct"          # Evidence explicitly linked to this control
    INHERITED = "inherited"    # Evidence inferred from org profile (e.g., "uses M365 GCC High")
    NONE = "none"              # No evidence available


class EvidenceReference(BaseModel):
    """A single evidence reference in an SSP narrative."""
    artifact_id: Optional[str] = Field(None, description="ID from evidence_artifacts table, if linked")
    artifact_title: Optional[str] = Field(None, description="Human-readable title of the evidence")
    confidence: EvidenceConfidence = Field(
        default=EvidenceConfidence.NONE,
        description="How this evidence was sourced"
    )
    description: str = Field(
        description="What this evidence demonstrates for this control"
    )


class GapFinding(BaseModel):
    """A specific gap identified for a control."""
    gap_type: str = Field(
        description="One of: missing_evidence, partial_implementation, "
                    "no_implementation, configuration_gap, documentation_gap"
    )
    description: str = Field(description="Plain-English description of the gap")
    remediation: str = Field(description="Suggested remediation action")
    sprs_impact: int = Field(
        description="SPRS point value at risk (1, 3, or 5)"
    )


class SSPSectionOutput(BaseModel):
    """
    Structured output for a single SSP control section.
    The LLM MUST populate every field — no free-form narrative without structure.
    """
    control_id: str = Field(description="e.g., AC.L2-3.1.1")
    control_title: str = Field(description="Human-readable control title")
    implementation_status: ImplementationStatus
    narrative: str = Field(
        description="Implementation narrative. MUST reference only evidence "
                    "listed in evidence_references. MUST NOT fabricate IP addresses, "
                    "hostnames, software versions, or configuration details not present "
                    "in the provided evidence or organization profile."
    )
    evidence_references: list[EvidenceReference] = Field(
        default_factory=list,
        description="Every piece of evidence supporting this narrative. "
                    "If empty, implementation_status MUST be 'Not Implemented' "
                    "and narrative MUST be a gap report."
    )
    gaps: list[GapFinding] = Field(
        default_factory=list,
        description="Gaps identified. Required if status is NOT 'Implemented'."
    )
    assessment_objectives_met: list[str] = Field(
        default_factory=list,
        description="List of 800-171A objective IDs satisfied (e.g., 3.1.1[a], 3.1.1[b])"
    )
    assessment_objectives_not_met: list[str] = Field(
        default_factory=list,
        description="Objective IDs NOT satisfied — drives gap reporting"
    )

    @field_validator("narrative")
    @classmethod
    def narrative_not_empty(cls, v):
        if not v or len(v.strip()) < 50:
            raise ValueError("Narrative must be at least 50 characters")
        return v.strip()

    @field_validator("gaps")
    @classmethod
    def gaps_required_for_partial(cls, v, info):
        status = info.data.get("implementation_status")
        if status in (
            ImplementationStatus.PARTIALLY_IMPLEMENTED,
            ImplementationStatus.NOT_IMPLEMENTED,
        ) and not v:
            raise ValueError(
                f"Gaps are required when status is {status}"
            )
        return v


# --- JSON schema for prompt injection ---

def get_output_schema_prompt() -> str:
    """
    Returns a string describing the required JSON output format
    for inclusion in the LLM system prompt.
    """
    return """You MUST respond with ONLY a valid JSON object matching this exact schema.
Do NOT include any text before or after the JSON. No markdown fences.

{
  "control_id": "AC.L2-3.1.1",
  "control_title": "Authorized Access Control",
  "implementation_status": "Implemented | Partially Implemented | Not Implemented | Not Applicable",
  "narrative": "Implementation description referencing ONLY provided evidence...",
  "evidence_references": [
    {
      "artifact_id": "abc123 or null if no artifact linked",
      "artifact_title": "Human-readable name",
      "confidence": "direct | inherited | none",
      "description": "What this evidence proves for this control"
    }
  ],
  "gaps": [
    {
      "gap_type": "missing_evidence | partial_implementation | no_implementation | configuration_gap | documentation_gap",
      "description": "What is missing",
      "remediation": "How to fix it",
      "sprs_impact": 1
    }
  ],
  "assessment_objectives_met": ["3.1.1[a]", "3.1.1[b]"],
  "assessment_objectives_not_met": ["3.1.1[c]"]
}

RULES:
- If NO evidence is linked to this control, set implementation_status to "Not Implemented"
  and write the narrative as a GAP REPORT explaining what evidence is needed.
- NEVER fabricate IP addresses, hostnames, software versions, usernames, or configuration
  details. If you don't have evidence for a specific claim, report it as a gap.
- evidence_references with confidence "direct" MUST have a valid artifact_id from the
  provided evidence list.
- evidence_references with confidence "inherited" may use null artifact_id but MUST
  reference a fact from the organization profile.
- Every claim in the narrative MUST trace to either an evidence_reference or the
  organization profile. No unsupported claims."""
