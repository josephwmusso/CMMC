"""
Database Migration Script — Initialize all CMMC platform tables.

Path: D:\\cmmc-platform\\scripts\\init_db.py

Run from project root (with venv activated):
    cd D:\\cmmc-platform
    python scripts\\init_db.py

What it does:
  1. Creates all tables (safe to re-run — skips existing tables)
  2. Seeds the 14 NIST 800-171 control families with representative controls
  3. Seeds assessment objectives for seeded controls
  4. Creates a default organization for local development
  5. Verifies everything with a quick read-back

Prerequisites:
  - Postgres running: docker-compose up -d
  - configs/settings.py has correct DATABASE_URL
"""

import sys
import os

# Ensure project root is on path so imports work
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import inspect, text
from src.db.models import (
    Base, Control, AssessmentObjective, Organization,
    AuditLog, EvidenceArtifact, EvidenceControlMap,
    SSPSection, POAMItem, ControlStatus,
    create_audit_entry,
)
from src.db.session import engine, get_session


# ── Step 1: Create all tables ────────────────────────────────────────────

def create_tables():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    expected = [
        "organizations", "controls", "assessment_objectives",
        "evidence_artifacts", "evidence_control_map",
        "ssp_sections", "poam_items", "audit_log",
    ]
    for t in expected:
        status = "OK" if t in tables else "MISSING"
        print(f"  {t:30s} [{status}]")

    missing = [t for t in expected if t not in tables]
    if missing:
        print(f"\nERROR: Missing tables: {missing}")
        sys.exit(1)

    # intake_responses is created by scripts/init_questionnaire_db.py in the
    # usual local-dev flow, but keep this self-contained so running just
    # init_db.py on a fresh DB still gives us a valid intake table with the
    # question_tier column. Both the CREATE and the ALTER are idempotent.
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS intake_responses (
                id              VARCHAR(30) PRIMARY KEY,
                session_id      VARCHAR(30) NOT NULL,
                org_id          VARCHAR(30) NOT NULL,
                module_id       INTEGER NOT NULL,
                question_id     VARCHAR(50) NOT NULL,
                control_ids     JSON NOT NULL DEFAULT '[]',
                answer_type     VARCHAR(20) NOT NULL DEFAULT 'text',
                answer_value    TEXT,
                answer_details  JSON,
                creates_gap     BOOLEAN NOT NULL DEFAULT FALSE,
                gap_severity    VARCHAR(20),
                evidence_action VARCHAR(30),
                question_tier   VARCHAR(30) DEFAULT 'SCREENING',
                answered_at     TIMESTAMP NOT NULL DEFAULT NOW(),
                UNIQUE(session_id, question_id)
            )
        """))
        conn.execute(text("""
            ALTER TABLE intake_responses
            ADD COLUMN IF NOT EXISTS question_tier VARCHAR(30) DEFAULT 'SCREENING'
        """))
        conn.commit()
    print(f"  {'intake_responses':30s} [OK — question_tier ensured]")

    print("All tables created.\n")


# ── Step 2: Seed NIST 800-171 Rev 2 controls ─────────────────────────────
# This is a REPRESENTATIVE subset.  In Week 2 Step 2 you'll load the full
# 110 controls from the actual NIST PDF/data.  This seed gives you enough
# to build and test against right now.

CONTROL_FAMILIES = [
    ("AC", "Access Control"),
    ("AT", "Awareness and Training"),
    ("AU", "Audit and Accountability"),
    ("CM", "Configuration Management"),
    ("IA", "Identification and Authentication"),
    ("IR", "Incident Response"),
    ("MA", "Maintenance"),
    ("MP", "Media Protection"),
    ("PE", "Physical Protection"),
    ("PS", "Personnel Security"),
    ("RA", "Risk Assessment"),
    ("CA", "Security Assessment"),
    ("SC", "System and Communications Protection"),
    ("SI", "System and Information Integrity"),
]

# Representative controls (one per family + key high-weight ones)
# Format: (id, family_abbrev, family, title, description, nist_section, points, poam_eligible)
SEED_CONTROLS = [
    # Access Control — 3 controls (includes a 5-pointer)
    ("AC.L2-3.1.1", "AC", "Access Control",
     "Authorized Access Control",
     "Limit information system access to authorized users, processes acting on "
     "behalf of authorized users, or devices (including other information systems).",
     "3.1.1", 5, True),

    ("AC.L2-3.1.2", "AC", "Access Control",
     "Transaction & Function Control",
     "Limit information system access to the types of transactions and functions "
     "that authorized users are permitted to execute.",
     "3.1.2", 1, True),

    ("AC.L2-3.1.3", "AC", "Access Control",
     "CUI Flow Enforcement",
     "Control the flow of CUI in accordance with approved authorizations.",
     "3.1.3", 1, True),

    # Awareness & Training
    ("AT.L2-3.2.1", "AT", "Awareness and Training",
     "Role-Based Risk Awareness",
     "Ensure that managers, systems administrators, and users of organizational "
     "information systems are made aware of the security risks associated with "
     "their activities and of the applicable policies, standards, and procedures "
     "related to the security of organizational information systems.",
     "3.2.1", 1, True),

    ("AT.L2-3.2.2", "AT", "Awareness and Training",
     "Role-Based Training",
     "Ensure that organizational personnel are adequately trained to carry out "
     "their assigned information security-related duties and responsibilities.",
     "3.2.2", 1, True),

    # Audit & Accountability
    ("AU.L2-3.3.1", "AU", "Audit and Accountability",
     "System Auditing",
     "Create, protect, and retain information system audit records to the extent "
     "needed to enable the monitoring, analysis, investigation, and reporting of "
     "unlawful, unauthorized, or inappropriate information system activity.",
     "3.3.1", 3, True),

    ("AU.L2-3.3.2", "AU", "Audit and Accountability",
     "User Accountability",
     "Ensure that the actions of individual information system users can be "
     "uniquely traced to those users so they can be held accountable for "
     "their actions.",
     "3.3.2", 3, True),

    # Configuration Management
    ("CM.L2-3.4.1", "CM", "Configuration Management",
     "System Baselining",
     "Establish and maintain baseline configurations and inventories of "
     "organizational information systems (including hardware, software, firmware, "
     "and documentation) throughout the respective system development life cycles.",
     "3.4.1", 3, True),

    # Identification & Authentication
    ("IA.L2-3.5.1", "IA", "Identification and Authentication",
     "Identification",
     "Identify information system users, processes acting on behalf of users, "
     "or devices.",
     "3.5.1", 1, True),

    ("IA.L2-3.5.2", "IA", "Identification and Authentication",
     "Authentication",
     "Authenticate (or verify) the identities of those users, processes, or "
     "devices, as a prerequisite to allowing access to organizational "
     "information systems.",
     "3.5.2", 3, True),

    # Incident Response
    ("IR.L2-3.6.1", "IR", "Incident Response",
     "Incident Handling",
     "Establish an operational incident-handling capability for organizational "
     "information systems that includes adequate preparation, detection, analysis, "
     "containment, recovery, and user response activities.",
     "3.6.1", 3, True),

    # Maintenance
    ("MA.L2-3.7.1", "MA", "Maintenance",
     "System Maintenance",
     "Perform maintenance on organizational information systems.",
     "3.7.1", 1, True),

    # Media Protection
    ("MP.L2-3.8.1", "MP", "Media Protection",
     "Media Protection",
     "Protect (i.e., physically control and securely store) information system "
     "media containing CUI, both paper and digital.",
     "3.8.1", 1, True),

    # Physical Protection
    ("PE.L2-3.10.1", "PE", "Physical Protection",
     "Limit Physical Access",
     "Limit physical access to organizational information systems, equipment, "
     "and the respective operating environments to authorized individuals.",
     "3.10.1", 1, True),

    # Personnel Security
    ("PS.L2-3.9.1", "PS", "Personnel Security",
     "Screen Individuals",
     "Screen individuals prior to authorizing access to information systems "
     "containing CUI.",
     "3.9.1", 1, True),

    # Risk Assessment
    ("RA.L2-3.11.1", "RA", "Risk Assessment",
     "Risk Assessments",
     "Periodically assess the risk to organizational operations (including "
     "mission, functions, image, or reputation), organizational assets, and "
     "individuals, resulting from the operation of organizational information "
     "systems and the associated processing, storage, or transmission of CUI.",
     "3.11.1", 3, True),

    # Security Assessment
    ("CA.L2-3.12.1", "CA", "Security Assessment",
     "Security Control Assessment",
     "Periodically assess the security controls in organizational information "
     "systems to determine if the controls are effective in their application.",
     "3.12.1", 3, True),

    # System & Communications Protection — includes the critical 5-pointer
    ("SC.L2-3.13.1", "SC", "System and Communications Protection",
     "Boundary Protection",
     "Monitor, control, and protect organizational communications (i.e., "
     "information transmitted or received by organizational information systems) "
     "at the external boundaries and key internal boundaries of the information "
     "systems.",
     "3.13.1", 1, True),

    ("SC.L2-3.13.11", "SC", "System and Communications Protection",
     "CUI Encryption",
     "Employ FIPS-validated cryptography when used to protect the "
     "confidentiality of CUI.",
     "3.13.11", 5, False),  # NOT POA&M eligible — must be met for cert

    # System & Information Integrity
    ("SI.L2-3.14.1", "SI", "System and Information Integrity",
     "Flaw Remediation",
     "Identify, report, and correct information and information system flaws "
     "in a timely manner.",
     "3.14.1", 3, True),
]


# Assessment objectives for the seeded controls (representative subset)
# Format: (id, control_id, description, examine, interview, test)
SEED_OBJECTIVES = [
    # AC.L2-3.1.1 — 4 objectives
    ("3.1.1[a]", "AC.L2-3.1.1",
     "Authorized users are identified.",
     "Access control policy; system security plan; list of authorized users",
     "System administrators; information security officer",
     "Review user account listings and compare against authorized user list"),

    ("3.1.1[b]", "AC.L2-3.1.1",
     "Processes acting on behalf of authorized users are identified.",
     "Access control policy; system design documentation; service account list",
     "System administrators; system developers",
     "Verify service accounts map to authorized processes"),

    ("3.1.1[c]", "AC.L2-3.1.1",
     "Devices (including other systems) authorized to connect are identified.",
     "Device inventory; network diagrams; system security plan",
     "Network administrators; information security officer",
     "Scan network for connected devices and compare against authorized list"),

    ("3.1.1[d]", "AC.L2-3.1.1",
     "Information system access is limited to authorized users, processes, "
     "and devices.",
     "Access control mechanisms; authentication logs; system configuration",
     "System administrators",
     "Attempt unauthorized access and verify it is denied"),

    # SC.L2-3.13.11 — 1 objective
    ("3.13.11[a]", "SC.L2-3.13.11",
     "FIPS-validated cryptography is employed to protect the confidentiality "
     "of CUI.",
     "Cryptographic module documentation; FIPS 140 certificates; system config",
     "System administrators; information security officer",
     "Verify encryption modules hold valid FIPS 140-2/140-3 certificates"),

    # AU.L2-3.3.1 — 2 objectives
    ("3.3.1[a]", "AU.L2-3.3.1",
     "Audit records needed to monitor, analyze, investigate, and report "
     "unlawful or unauthorized system activity are specified.",
     "Audit and accountability policy; audit log configurations; SSP",
     "Information security officer; system administrators",
     "Review audit configuration for completeness of auditable events"),

    ("3.3.1[b]", "AU.L2-3.3.1",
     "The content of audit records needed is defined.",
     "Audit policy; system security plan; audit log samples",
     "System administrators",
     "Examine sample audit records for required content fields"),

    # IR.L2-3.6.1 — 2 objectives
    ("3.6.1[a]", "IR.L2-3.6.1",
     "An operational incident-handling capability is established.",
     "Incident response plan; incident response policy; procedures",
     "Incident response team; information security officer",
     "Review incident response plan for required elements"),

    ("3.6.1[b]", "IR.L2-3.6.1",
     "The incident-handling capability includes preparation.",
     "Incident response plan; training records; communication procedures",
     "Incident response team members",
     "Verify team training and readiness procedures"),

    # RA.L2-3.11.1 — 1 objective
    ("3.11.1[a]", "RA.L2-3.11.1",
     "Risk to organizational operations, assets, and individuals is "
     "periodically assessed.",
     "Risk assessment policy; risk assessment reports; vulnerability scans",
     "Risk executive; information security officer",
     "Review risk assessment schedule and most recent report"),
]


def seed_controls(session):
    """Insert seed controls if they don't already exist."""
    existing = {c.id for c in session.query(Control.id).all()}
    added = 0
    for (cid, abbrev, family, title, desc, section, pts, poam) in SEED_CONTROLS:
        if cid not in existing:
            session.add(Control(
                id=cid,
                family_abbrev=abbrev,
                family=family,
                title=title,
                description=desc,
                nist_section=section,
                points=pts,
                poam_eligible=poam,
                status=ControlStatus.NOT_ASSESSED,
            ))
            added += 1
    session.flush()
    print(f"  Controls: {added} added, {len(existing)} already existed.")
    return added


def seed_objectives(session):
    """Insert seed assessment objectives."""
    existing = {o.id for o in session.query(AssessmentObjective.id).all()}
    added = 0
    for (oid, cid, desc, examine, interview, test) in SEED_OBJECTIVES:
        if oid not in existing:
            session.add(AssessmentObjective(
                id=oid,
                control_id=cid,
                description=desc,
                examine=examine,
                interview=interview,
                test=test,
                status=ControlStatus.NOT_ASSESSED,
            ))
            added += 1
    session.flush()
    print(f"  Objectives: {added} added, {len(existing)} already existed.")
    return added


def seed_default_org(session):
    """Create a default dev organization."""
    existing = session.query(Organization).first()
    if existing:
        print(f"  Organization already exists: {existing.name}")
        return

    org = Organization(
        name="Dev Organization (Local)",
        system_name="CMMC Platform Dev Instance",
        employee_count=1,
    )
    session.add(org)
    session.flush()
    print(f"  Created default org: {org.name} (id={org.id})")


# ── Step 3: Verify ────────────────────────────────────────────────────────

def verify(session):
    print("\n--- Verification ---")
    control_count = session.query(Control).count()
    obj_count = session.query(AssessmentObjective).count()
    org_count = session.query(Organization).count()

    total_pts = sum(
        c.points for c in session.query(Control).all()
    )

    print(f"  Controls:    {control_count}  (SPRS points seeded: {total_pts})")
    print(f"  Objectives:  {obj_count}")
    print(f"  Orgs:        {org_count}")

    # Quick relationship check
    ac_control = session.get(Control, "AC.L2-3.1.1")
    if ac_control:
        obj_for_ac = len(ac_control.objectives)
        print(f"  AC.L2-3.1.1 objectives: {obj_for_ac}  (expected: 4)")
    else:
        print("  WARNING: AC.L2-3.1.1 not found — seed may have failed")

    # Check audit log table is accessible
    audit_count = session.query(AuditLog).count()
    print(f"  Audit log entries: {audit_count}")

    print("\nDatabase initialized successfully!")
    print(f"SPRS max from seeded controls: {total_pts}  (full dataset will be 110)")


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("CMMC Platform — Database Initialization")
    print("=" * 60)

    # Test connection first
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            pg_version = result.scalar()
            print(f"Connected to: {pg_version}\n")
    except Exception as e:
        print(f"\nERROR: Cannot connect to Postgres!")
        print(f"  {e}")
        print(f"\nMake sure Docker is running:")
        print(f"  docker-compose up -d")
        sys.exit(1)

    create_tables()

    print("Seeding data...")
    with get_session() as session:
        seed_controls(session)
        seed_objectives(session)
        seed_default_org(session)

    # Verify with a fresh session
    with get_session() as session:
        verify(session)

    print("\n--- Next Steps ---")
    print("1. Load full 110 controls from NIST PDF (Week 2, Step 2)")
    print("2. Load controls into Qdrant for RAG (Week 2, Step 2)")
    print("3. Build SSP generation agent (Week 3-4)")


if __name__ == "__main__":
    main()
