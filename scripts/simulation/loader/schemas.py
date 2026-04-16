"""Pydantic models for simulation fixture files. Strict — extra fields raise."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CompanyProfile(BaseModel, extra="forbid"):
    company_name: str
    cage_code: Optional[str] = None
    uei: Optional[str] = None
    duns_number: Optional[str] = None
    employee_count: int
    facility_count: int = 1
    primary_location: str
    system_name: Optional[str] = None
    cui_types: List[str] = []
    cui_flow: Optional[str] = None
    dfars_7012_clause: bool = False
    has_remote_workers: bool = False
    has_wireless: bool = False
    identity_provider: Optional[str] = None
    email_platform: Optional[str] = None
    edr_product: Optional[str] = None
    firewall_product: Optional[str] = None
    siem_product: Optional[str] = None
    backup_solution: Optional[str] = None
    training_tool: Optional[str] = None
    existing_ssp: bool = False
    existing_poam: bool = False
    prior_assessment: bool = False


class IntakeAnswer(BaseModel, extra="allow"):
    id: Optional[str] = Field(None, alias="question_id")
    question_id: Optional[str] = None
    module: int
    answer_value: str
    rationale: Optional[str] = None
    contradiction_seed: Optional[str] = None
    controls: Optional[List[str]] = None


class EvidenceArtifact(BaseModel, extra="allow"):
    id: str
    filename: str
    evidence_type: str
    source_system: Optional[str] = None
    state: str = "DRAFT"
    controls: List[str] = []
    content_summary: Optional[str] = None


class Contradiction(BaseModel, extra="allow"):
    contradiction_id: str
    name: str
    detection_layer: Optional[str] = None
    affected_controls: List[str] = []
    expected_severity: Optional[str] = None
    expected_contradiction_rule_id: Optional[str] = None
    must_catch: bool = True


class IntakeContradictions(BaseModel, extra="allow"):
    minimum_count: int = 0
    required: List[str] = []
    likely_also: List[str] = []
    diagnostic_bonus: List[str] = []


class ResolutionConflict(BaseModel, extra="allow"):
    contradiction_id: str
    claim_control: Optional[str] = None
    trigger: Optional[str] = None


class ResolutionConflicts(BaseModel, extra="allow"):
    minimum_count: int = 0
    required: List[Any] = []
    preferred_also: List[Any] = []


class SprsTarget(BaseModel, extra="allow"):
    expected_range: List[int]
    reasoning: Optional[str] = None


class ExpectedOutputs(BaseModel, extra="allow"):
    sprs_target: Optional[SprsTarget] = None
    intake_contradictions_must_catch: Optional[IntakeContradictions] = None
    resolution_conflicts_must_catch: Optional[ResolutionConflicts] = None
    at_risk_top_10: Optional[Dict[str, Any]] = None
    claims_extraction: Optional[Dict[str, Any]] = None
    method_coverage: Optional[Dict[str, Any]] = None
    readiness_pct_target: Optional[Dict[str, Any]] = None
    assessor_findings_style: Optional[Dict[str, Any]] = None


class ForbiddenFacts(BaseModel, extra="allow"):
    employee_count_other_than: Optional[int] = None
    location_other_than: Optional[str] = None
    cage_code_other_than: Optional[str] = None
    company_name_other_than: Optional[str] = None


class DateConstraints(BaseModel, extra="allow"):
    earliest_allowed: Optional[str] = None
    latest_allowed: Optional[str] = None
    flag_future_dates: bool = True


class ForbiddenList(BaseModel, extra="allow"):
    forbidden_tools: List[str] = []
    forbidden_ip_ranges: Optional[Dict[str, Any]] = None
    allowed_hostnames: List[str] = []
    allowed_evidence_titles: List[str] = []
    forbidden_facts: Optional[ForbiddenFacts] = None
    date_constraints: Optional[DateConstraints] = None


class Fixture(BaseModel, extra="allow"):
    company_profile: CompanyProfile
    intake: List[IntakeAnswer]
    evidence_artifacts: List[EvidenceArtifact]
    contradictions: List[Contradiction]
    expected_outputs: ExpectedOutputs
    forbidden: ForbiddenList
    evidence_content: Dict[str, str] = {}
