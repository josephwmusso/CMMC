"""
CMMC Compliance Platform — Core Database Models
=================================================
Postgres 16 schema for evidence lifecycle, NIST 800-171 controls,
SSP sections, and a hash-chained audit ledger.

Path: D:\\cmmc-platform\\src\\db\\models.py

Tables:
  - frameworks           Compliance framework registry (NIST 800-171, CMMC, etc.)
  - organizations        Tenant (single-tenant for MVP, multi-tenant later)
  - controls             110 NIST 800-171 Rev 2 controls (FK → frameworks)
  - assessment_objectives  320 objectives from NIST 800-171A
  - evidence_artifacts   Uploaded evidence files with state machine
  - evidence_control_map M2M link: evidence <-> controls/objectives
  - ssp_sections         Generated SSP narratives per control
  - poam_items           Plan of Action & Milestones entries
  - audit_log            Append-only, hash-chained ledger
"""

import enum
import uuid
import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, JSON, Boolean,
    ForeignKey, Index, CheckConstraint, UniqueConstraint,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


# ---------------------------------------------------------------------------
# Helper: generate short UUIDs for primary keys
# ---------------------------------------------------------------------------
def new_id() -> str:
    return uuid.uuid4().hex[:20]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class EvidenceState(enum.Enum):
    """
    Evidence lifecycle:  DRAFT -> REVIEWED -> APPROVED -> PUBLISHED
    PUBLISHED is terminal — artifact becomes immutable (WORM semantics).
    """
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    PUBLISHED = "published"


class ControlStatus(enum.Enum):
    """Per-control assessment outcome (maps to CMMC scoring)."""
    NOT_ASSESSED = "not_assessed"
    NOT_MET = "not_met"
    PARTIALLY_MET = "partially_met"
    MET = "met"
    NOT_APPLICABLE = "not_applicable"


class POAMStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    OVERDUE = "overdue"


# Stable ID for the canonical NIST 800-171 Rev 2 / CMMC Level 2 framework.
# Matches the seed value in scripts/add_frameworks_table.py.
NIST_171_R2_FRAMEWORK_ID = "nist80171r2_fw000001"


# ---------------------------------------------------------------------------
# Compliance Framework registry
# ---------------------------------------------------------------------------
class Framework(Base):
    """
    One row per compliance framework the platform understands.
    Currently only NIST 800-171 Rev 2 / CMMC Level 2 is seeded.
    Adding CMMC Level 3 (NIST 800-172) or FedRAMP later means inserting
    a new row here and a new set of controls — nothing else changes.
    """
    __tablename__ = "frameworks"

    id            = Column(String(20),  primary_key=True, default=new_id)
    name          = Column(String(255), nullable=False)   # "CMMC Level 2"
    version       = Column(String(100), nullable=False)   # "NIST 800-171 Rev 2"
    control_count = Column(Integer,     nullable=False, default=0)  # 110
    description   = Column(Text)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    # relationships
    controls = relationship("Control", back_populates="framework")


# ---------------------------------------------------------------------------
# Organization (tenant)
# ---------------------------------------------------------------------------
class Organization(Base):
    """
    Single-tenant for MVP.  Keeps the schema multi-tenant-ready so you
    don't have to refactor when you add your second customer.
    """
    __tablename__ = "organizations"

    id = Column(String(20), primary_key=True, default=new_id)
    name = Column(String(255), nullable=False)
    cage_code = Column(String(10))          # DoD CAGE code
    duns_number = Column(String(13))        # DUNS / UEI
    system_name = Column(String(255))       # e.g., "Apex CUI Environment"
    system_boundary = Column(Text)          # free-text boundary description
    employee_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # relationships
    evidence = relationship("EvidenceArtifact", back_populates="organization")
    ssp_sections = relationship("SSPSection", back_populates="organization")
    poam_items = relationship("POAMItem", back_populates="organization")


# ---------------------------------------------------------------------------
# NIST 800-171 Rev 2 Controls (110 rows)
# ---------------------------------------------------------------------------
class Control(Base):
    """
    One row per NIST 800-171 Rev 2 security requirement.
    ID format: "AC.L2-3.1.1"  (family.level-section.requirement)
    """
    __tablename__ = "controls"

    id = Column(String(30), primary_key=True)         # e.g., "AC.L2-3.1.1"
    framework_id = Column(
        String(20), ForeignKey("frameworks.id", ondelete="SET NULL"), nullable=True,
        default=NIST_171_R2_FRAMEWORK_ID,
    )
    family = Column(String(80), nullable=False)        # "Access Control"
    family_abbrev = Column(String(4), nullable=False)  # "AC"
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    discussion = Column(Text)
    nist_section = Column(String(20))                  # "3.1.1"
    points = Column(Integer, default=1)                # SPRS weight (1, 3, or 5)
    poam_eligible = Column(Boolean, default=True)      # some controls can't be POA&M'd
    status = Column(
        SAEnum(ControlStatus, name="control_status"),
        default=ControlStatus.NOT_ASSESSED,
    )

    # relationships
    framework    = relationship("Framework", back_populates="controls")
    objectives   = relationship("AssessmentObjective", back_populates="control")
    evidence_links = relationship("EvidenceControlMap", back_populates="control")
    ssp_sections = relationship("SSPSection", back_populates="control")
    poam_items   = relationship("POAMItem", back_populates="control")

    __table_args__ = (
        Index("ix_controls_family",    "family_abbrev"),
        Index("ix_controls_status",    "status"),
        Index("ix_controls_framework", "framework_id"),
    )


# ---------------------------------------------------------------------------
# NIST 800-171A Assessment Objectives (320 rows)
# ---------------------------------------------------------------------------
class AssessmentObjective(Base):
    """
    Each control has 1-N assessment objectives (the [a], [b], [c] sub-items).
    Assessors evaluate EACH objective — partial credit matters.
    """
    __tablename__ = "assessment_objectives"

    id = Column(String(30), primary_key=True)          # "3.1.1[a]"
    control_id = Column(
        String(30), ForeignKey("controls.id", ondelete="CASCADE"), nullable=False
    )
    description = Column(Text, nullable=False)
    examine = Column(Text)      # artifacts to examine
    interview = Column(Text)    # roles to interview
    test = Column(Text)         # procedures to test
    status = Column(
        SAEnum(ControlStatus, name="control_status"),
        default=ControlStatus.NOT_ASSESSED,
    )

    # relationships
    control = relationship("Control", back_populates="objectives")
    evidence_links = relationship("EvidenceControlMap", back_populates="objective")

    __table_args__ = (
        Index("ix_objectives_control", "control_id"),
    )


# ---------------------------------------------------------------------------
# Evidence Artifacts — the heart of the platform
# ---------------------------------------------------------------------------
class EvidenceArtifact(Base):
    """
    One row per uploaded evidence file.  State machine enforces lifecycle:
      DRAFT -> REVIEWED -> APPROVED -> PUBLISHED (immutable)
    SHA-256 hash is computed at PUBLISHED and becomes permanent.
    """
    __tablename__ = "evidence_artifacts"

    id = Column(String(20), primary_key=True, default=new_id)
    org_id = Column(
        String(20), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size_bytes = Column(Integer)
    mime_type = Column(String(100))

    # integrity
    sha256_hash = Column(String(64))               # populated at PUBLISHED
    hash_algorithm = Column(String(20), default="sha256")

    # lifecycle
    state = Column(
        SAEnum(EvidenceState, name="evidence_state"),
        default=EvidenceState.DRAFT,
        nullable=False,
    )

    # classification
    evidence_type = Column(String(50))   # policy, log, config, screenshot, test_output
    source_system = Column(String(100))  # entra_id, m365, manual, siem, edr
    description = Column(Text)
    owner = Column(String(255))

    # timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    reviewed_at = Column(DateTime(timezone=True))
    reviewed_by = Column(String(255))
    approved_at = Column(DateTime(timezone=True))
    approved_by = Column(String(255))
    published_at = Column(DateTime(timezone=True))

    # extensible metadata (connector-specific fields, tags, etc.)
    metadata_json = Column(JSON, default=dict)

    # relationships
    organization = relationship("Organization", back_populates="evidence")
    control_links = relationship(
        "EvidenceControlMap", back_populates="evidence", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_evidence_org", "org_id"),
        Index("ix_evidence_state", "state"),
        Index("ix_evidence_type", "evidence_type"),
        Index("ix_evidence_control_type", "org_id", "evidence_type"),
    )


# ---------------------------------------------------------------------------
# Evidence <-> Control / Objective many-to-many
# ---------------------------------------------------------------------------
class EvidenceControlMap(Base):
    """
    Links an evidence artifact to one or more controls AND their specific
    assessment objectives.  This is the graph that powers:
      "Show me all evidence for AC.L2-3.1.1, objective [a]"
    """
    __tablename__ = "evidence_control_map"

    id = Column(String(20), primary_key=True, default=new_id)
    evidence_id = Column(
        String(20), ForeignKey("evidence_artifacts.id", ondelete="CASCADE"),
        nullable=False,
    )
    control_id = Column(
        String(30), ForeignKey("controls.id", ondelete="CASCADE"),
        nullable=False,
    )
    objective_id = Column(
        String(30), ForeignKey("assessment_objectives.id", ondelete="SET NULL"),
        nullable=True,  # can map to control without specific objective
    )
    relevance_score = Column(Float)  # RAG-assigned confidence 0-1
    mapped_by = Column(String(50))   # "agent", "manual", "connector"

    # relationships
    evidence = relationship("EvidenceArtifact", back_populates="control_links")
    control = relationship("Control", back_populates="evidence_links")
    objective = relationship("AssessmentObjective", back_populates="evidence_links")

    __table_args__ = (
        UniqueConstraint("evidence_id", "control_id", "objective_id",
                         name="uq_evidence_control_objective"),
        Index("ix_ecm_control", "control_id"),
        Index("ix_ecm_evidence", "evidence_id"),
    )


# ---------------------------------------------------------------------------
# SSP Sections — one per control
# ---------------------------------------------------------------------------
class SSPSection(Base):
    """
    AI-generated (or manually written) implementation narrative for each
    control.  Versioned — every regeneration bumps the version.
    """
    __tablename__ = "ssp_sections"

    id = Column(String(20), primary_key=True, default=new_id)
    org_id = Column(
        String(20), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    control_id = Column(
        String(30), ForeignKey("controls.id", ondelete="CASCADE"), nullable=False
    )
    implementation_status = Column(String(30), default="not_provided")
    # ^ "implemented", "partially_implemented", "planned", "not_provided"
    narrative = Column(Text)            # the actual SSP prose
    citations = Column(JSON, default=list)  # list of evidence_artifact IDs cited
    state = Column(
        SAEnum(EvidenceState, name="evidence_state"),
        default=EvidenceState.DRAFT,
    )
    version = Column(Integer, default=1)
    generated_by = Column(String(50))   # "agent:ssp_writer_v1", "manual"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # relationships
    organization = relationship("Organization", back_populates="ssp_sections")
    control = relationship("Control", back_populates="ssp_sections")

    __table_args__ = (
        UniqueConstraint("org_id", "control_id", "version",
                         name="uq_ssp_org_control_version"),
        Index("ix_ssp_org_control", "org_id", "control_id"),
    )


# ---------------------------------------------------------------------------
# POA&M Items
# ---------------------------------------------------------------------------
class POAMItem(Base):
    """
    Plan of Action & Milestones — required for any control scored NOT MET.
    CMMC allows conditional certification if SPRS >= 88 (80% threshold)
    and all POA&M items have 180-day close-out plans.
    """
    __tablename__ = "poam_items"

    id = Column(String(20), primary_key=True, default=new_id)
    org_id = Column(
        String(20), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    control_id = Column(
        String(30), ForeignKey("controls.id", ondelete="CASCADE"), nullable=False
    )
    weakness_description = Column(Text, nullable=False)
    remediation_plan = Column(Text)
    milestone_changes = Column(JSON, default=list)  # [{date, description}]
    resources_required = Column(Text)
    scheduled_completion = Column(DateTime(timezone=True))
    actual_completion = Column(DateTime(timezone=True))
    status = Column(
        SAEnum(POAMStatus, name="poam_status"),
        default=POAMStatus.OPEN,
    )
    risk_level = Column(String(20))  # low, moderate, high, very_high
    # 3.1C — origin of this POA&M row. 'ASSESSMENT' for the classic
    # gap-report generator, 'SCAN' for Nessus-driven items,
    # 'CONTRADICTION' reserved for future use.
    source_type = Column(String(20), default="ASSESSMENT")
    source_id = Column(String(20))  # scan_imports.id when source_type=SCAN
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # relationships
    organization = relationship("Organization", back_populates="poam_items")
    control = relationship("Control", back_populates="poam_items")

    __table_args__ = (
        Index("ix_poam_org", "org_id"),
        Index("ix_poam_status", "status"),
        Index("ix_poam_control", "control_id"),
    )


# ---------------------------------------------------------------------------
# Intake Contradiction — cross-module consistency findings (2.9A)
# ---------------------------------------------------------------------------
class IntakeContradiction(Base):
    """A contradiction the rules engine detected in an org's intake data.

    Queries in routes + contradiction_engine use raw SQL for consistency
    with the rest of the API layer — this model exists for ORM
    introspection / test setup.
    """

    __tablename__ = "intake_contradictions"

    id = Column(String(20), primary_key=True)
    org_id = Column(String(20), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(30), ForeignKey("intake_sessions.id", ondelete="SET NULL"))

    rule_id = Column(String(50), nullable=False)
    family = Column(String(10), nullable=False)
    severity = Column(String(20), nullable=False)   # CRITICAL / HIGH / MEDIUM / LOW
    status = Column(String(20), nullable=False, default="OPEN")  # OPEN / RESOLVED / DISMISSED / OVERRIDDEN

    description = Column(Text, nullable=False)
    source_question_id = Column(String(100), nullable=False)
    source_answer = Column(Text)
    conflicting_question_id = Column(String(100))
    conflicting_answer = Column(Text)
    affected_control_ids = Column(JSON, nullable=False, default=list)

    resolution_notes = Column(Text)
    resolved_by = Column(String, ForeignKey("users.id"))
    resolved_at = Column(DateTime(timezone=True))

    detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("org_id", "rule_id", name="uq_intake_contradictions_org_rule"),
        Index("ix_intake_contradictions_org_status", "org_id", "status"),
    )


# ---------------------------------------------------------------------------
# Scan Imports & Findings (Phase 3.1A — Nessus parser MVP)
# ---------------------------------------------------------------------------
class ScanImport(Base):
    """Metadata for one uploaded .nessus file. Each import optionally spawns
    a DRAFT evidence artifact linked via ``evidence_artifact_id``.

    Routes use raw SQL for inserts/reads — this model is here for
    introspection / future ORM-style queries."""

    __tablename__ = "scan_imports"

    id = Column(String(20), primary_key=True)
    org_id = Column(String(20), ForeignKey("organizations.id"), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    scan_type = Column(String(20), nullable=False, default="NESSUS")
    scanner_version = Column(String(100))
    scan_date = Column(DateTime(timezone=True))
    imported_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    imported_by = Column(String, ForeignKey("users.id"))

    host_count = Column(Integer, nullable=False, default=0)
    finding_count = Column(Integer, nullable=False, default=0)
    critical_count = Column(Integer, nullable=False, default=0)
    high_count = Column(Integer, nullable=False, default=0)
    medium_count = Column(Integer, nullable=False, default=0)
    low_count = Column(Integer, nullable=False, default=0)
    info_count = Column(Integer, nullable=False, default=0)

    status = Column(String(20), nullable=False, default="PROCESSING")
    error_message = Column(Text)
    evidence_artifact_id = Column(String(20), ForeignKey("evidence_artifacts.id"))
    summary_text = Column(Text)


class ScanFinding(Base):
    """One Nessus finding row. Multiple per host × plugin × port."""

    __tablename__ = "scan_findings"

    id = Column(String(20), primary_key=True)
    scan_import_id = Column(
        String(20),
        ForeignKey("scan_imports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    org_id = Column(String(20), ForeignKey("organizations.id"), nullable=False, index=True)

    host_ip = Column(String(45), nullable=False)
    hostname = Column(String(255))
    port = Column(Integer, nullable=False, default=0)
    protocol = Column(String(10))

    plugin_id = Column(String(20), nullable=False)
    plugin_name = Column(String(500), nullable=False)
    plugin_family = Column(String(200))

    severity = Column(Integer, nullable=False, default=0)
    severity_label = Column(String(20), nullable=False, default="INFO")
    cvss_base_score = Column(Float)
    cvss3_base_score = Column(Float)
    cve_ids = Column(JSON, default=list)

    synopsis = Column(Text)
    description = Column(Text)
    solution = Column(Text)
    risk_factor = Column(String(20))
    mapped_control_ids = Column(JSON, default=list)

    status = Column(String(20), nullable=False, default="OPEN")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("ix_scan_findings_severity_desc", severity.desc()),
    )


# ---------------------------------------------------------------------------
# Baseline engine — CIS/STIG catalog + per-org adoption + deviation records
# ---------------------------------------------------------------------------
class Baseline(Base):
    """Seeded catalog entry for a security baseline (CIS, STIG, custom)."""
    __tablename__ = "baselines"

    id          = Column(String(20), primary_key=True)
    name        = Column(String(200), nullable=False)
    version     = Column(String(50), nullable=False)
    source      = Column(String(100), nullable=False)    # CIS | DISA_STIG | CUSTOM
    platform    = Column(String(100), nullable=False)
    description = Column(Text)
    item_count  = Column(Integer, nullable=False, default=0)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())


class BaselineItem(Base):
    """One checkable item within a baseline, with keyword hints for matching."""
    __tablename__ = "baseline_items"

    id                    = Column(String(20), primary_key=True)
    baseline_id           = Column(String(20), ForeignKey("baselines.id", ondelete="CASCADE"), nullable=False)
    cis_id                = Column(String(50))
    section               = Column(String(200))
    title                 = Column(String(500), nullable=False)
    description           = Column(Text)
    expected_value        = Column(Text)
    rationale             = Column(Text)
    severity              = Column(String(20), nullable=False, default="MEDIUM")
    control_ids           = Column(ARRAY(Text), nullable=False)
    match_keywords        = Column(ARRAY(Text))
    match_plugin_families = Column(ARRAY(Text))
    created_at            = Column(DateTime(timezone=True), server_default=func.now())


class OrgBaseline(Base):
    """An org's adoption of a baseline. Archiving preserves deviation history."""
    __tablename__ = "org_baselines"

    id          = Column(String(20), primary_key=True)
    org_id      = Column(String(20), ForeignKey("organizations.id"), nullable=False)
    baseline_id = Column(String(20), ForeignKey("baselines.id"), nullable=False)
    adopted_at  = Column(DateTime(timezone=True), server_default=func.now())
    status      = Column(String(20), nullable=False, default="ACTIVE")  # ACTIVE | ARCHIVED

    __table_args__ = (UniqueConstraint("org_id", "baseline_id"),)


class BaselineDeviation(Base):
    """A scan finding (or manual entry) that violates a baseline item."""
    __tablename__ = "baseline_deviations"

    id               = Column(String(20), primary_key=True)
    org_id           = Column(String(20), ForeignKey("organizations.id"), nullable=False)
    org_baseline_id  = Column(String(20), ForeignKey("org_baselines.id", ondelete="CASCADE"), nullable=False)
    baseline_item_id = Column(String(20), ForeignKey("baseline_items.id"), nullable=False)
    scan_finding_id  = Column(String(20), ForeignKey("scan_findings.id", ondelete="SET NULL"))
    actual_value     = Column(Text)
    status           = Column(String(20), nullable=False, default="OPEN")  # OPEN | REMEDIATED | ACCEPTED | FALSE_POSITIVE
    notes            = Column(Text)
    detected_at      = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at      = Column(DateTime(timezone=True))
    resolved_by      = Column(String(20), ForeignKey("users.id"))


# ---------------------------------------------------------------------------
# Audit Log — append-only, hash-chained
# ---------------------------------------------------------------------------
class AuditLog(Base):
    """
    Every state change, agent action, and user operation is recorded here.
    Hash-chaining: each entry stores the hash of the previous entry,
    making the log tamper-evident.  Assessors can verify chain integrity.

    This table should NEVER be UPDATEd or DELETEd — append only.
    """
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actor = Column(String(255), nullable=False)     # user email or agent ID
    actor_type = Column(String(50), nullable=False)  # "user", "agent", "system"
    action = Column(String(100), nullable=False)     # "evidence.state_change"
    target_type = Column(String(50))                 # "evidence_artifact"
    target_id = Column(String(30))
    details = Column(JSON)                           # action-specific payload
    prev_hash = Column(String(64))                   # SHA-256 of previous entry
    entry_hash = Column(String(64))                  # SHA-256 of this entry

    __table_args__ = (
        Index("ix_audit_timestamp", "timestamp"),
        Index("ix_audit_target", "target_type", "target_id"),
        Index("ix_audit_actor", "actor"),
    )


# ---------------------------------------------------------------------------
# Evidence state machine + audit helpers
# ---------------------------------------------------------------------------

VALID_TRANSITIONS: dict[str, list[str]] = {
    "draft":     ["reviewed"],
    "reviewed":  ["approved", "draft"],       # can be sent back
    "approved":  ["published", "reviewed"],   # can be sent back
    "published": [],                          # terminal — immutable
}


def compute_hash(data: str) -> str:
    """SHA-256 hex digest of a string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def compute_file_hash(file_path: str) -> str:
    """SHA-256 hex digest of a file, read in 64 KB chunks."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def build_audit_entry_hash(entry_id: int, timestamp: str, actor: str,
                           action: str, target_id: str, details: dict,
                           prev_hash: str) -> str:
    """Deterministic hash of an audit log entry for chain verification."""
    payload = json.dumps({
        "id": entry_id,
        "timestamp": timestamp,
        "actor": actor,
        "action": action,
        "target_id": target_id,
        "details": details,
        "prev_hash": prev_hash or "",
    }, sort_keys=True, default=str)
    return compute_hash(payload)


def create_audit_entry(db_session, *, actor: str, actor_type: str,
                       action: str, target_type: str = None,
                       target_id: str = None, details: dict = None) -> AuditLog:
    """
    Create a new hash-chained audit log entry.
    Call this inside the same transaction as the action it records.
    """
    # Get the most recent entry's hash for chaining
    last_entry = (
        db_session.query(AuditLog)
        .order_by(AuditLog.id.desc())
        .first()
    )
    prev_hash = last_entry.entry_hash if last_entry else None

    now = datetime.now(timezone.utc)

    entry = AuditLog(
        timestamp=now,
        actor=actor,
        actor_type=actor_type,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details or {},
        prev_hash=prev_hash,
    )

    # We need a flush to get the auto-incremented ID before computing the hash
    db_session.add(entry)
    db_session.flush()

    entry.entry_hash = build_audit_entry_hash(
        entry_id=entry.id,
        timestamp=now.isoformat(),
        actor=actor,
        action=action,
        target_id=target_id,
        details=details or {},
        prev_hash=prev_hash,
    )

    return entry


def transition_evidence_state(db_session, *, artifact_id: str,
                              new_state: str, actor: str) -> EvidenceArtifact:
    """
    Transition an evidence artifact through its state machine.
    Raises ValueError for invalid transitions.
    Computes file hash on publish.  Records everything in audit log.
    """
    artifact = db_session.query(EvidenceArtifact).get(artifact_id)
    if artifact is None:
        raise ValueError(f"Evidence artifact {artifact_id} not found")

    current = artifact.state.value
    if new_state not in VALID_TRANSITIONS[current]:
        allowed = VALID_TRANSITIONS[current]
        raise ValueError(
            f"Cannot transition from '{current}' to '{new_state}'. "
            f"Allowed: {allowed}"
        )

    now = datetime.now(timezone.utc)

    # State-specific side effects
    if new_state == "reviewed":
        artifact.reviewed_at = now
        artifact.reviewed_by = actor
    elif new_state == "approved":
        artifact.approved_at = now
        artifact.approved_by = actor
    elif new_state == "published":
        artifact.published_at = now
        artifact.sha256_hash = compute_file_hash(artifact.file_path)

    old_state = artifact.state.value
    artifact.state = EvidenceState(new_state)
    artifact.updated_at = now

    # Audit trail
    create_audit_entry(
        db_session,
        actor=actor,
        actor_type="user",
        action="evidence.state_change",
        target_type="evidence_artifact",
        target_id=artifact_id,
        details={"from": old_state, "to": new_state},
    )

    return artifact
