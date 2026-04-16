"""
Render startup script — creates all tables matching the actual ORM and migration
scripts exactly, seeds data, and starts uvicorn.

Sources of truth for schema:
  - src/db/models.py (core 9 tables)
  - src/db/models_ssp.py (overrides ssp_sections with evidence_refs/gaps JSONB)
  - scripts/init_questionnaire_db.py (intake tables)
  - scripts/init_document_engine_db.py (document engine tables)
  - src/api/auth.py (users table column names: hashed_password, full_name, is_admin)
"""
import os
import sys
import hashlib
import json
import logging
import time
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# 1. DATABASE CONNECTION
# ---------------------------------------------------------------------------

def get_db_url():
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def get_connection():
    import psycopg2
    url = get_db_url()
    if not url:
        logger.error("FATAL: DATABASE_URL not set")
        sys.exit(1)
    return psycopg2.connect(url)


def wait_for_db(max_attempts=30):
    import psycopg2
    url = get_db_url()
    logger.info(f"DATABASE_URL set: {bool(url)}")
    if not url:
        logger.error("FATAL: DATABASE_URL not set")
        sys.exit(1)
    for i in range(max_attempts):
        try:
            conn = psycopg2.connect(url)
            conn.close()
            logger.info("Database ready")
            return
        except Exception as e:
            logger.info(f"  Attempt {i+1}/{max_attempts}: {e}")
            time.sleep(2)
    logger.error("FATAL: Could not connect to database")
    sys.exit(1)


# ---------------------------------------------------------------------------
# 2. TABLE CREATION — matches actual ORM + migration scripts exactly
# ---------------------------------------------------------------------------

TABLES_DDL = [
    # ── Core tables from models.py ──

    ("frameworks", """
        CREATE TABLE IF NOT EXISTS frameworks (
            id            VARCHAR(20) PRIMARY KEY,
            name          VARCHAR(255) NOT NULL,
            version       VARCHAR(100) NOT NULL DEFAULT '',
            control_count INTEGER NOT NULL DEFAULT 0,
            description   TEXT,
            created_at    TIMESTAMPTZ DEFAULT NOW()
        )
    """),

    ("organizations", """
        CREATE TABLE IF NOT EXISTS organizations (
            id              VARCHAR(20) PRIMARY KEY,
            name            VARCHAR(255) NOT NULL,
            cage_code       VARCHAR(10),
            duns_number     VARCHAR(13),
            system_name     VARCHAR(255),
            system_boundary TEXT,
            employee_count  INTEGER,
            created_at      TIMESTAMPTZ DEFAULT NOW(),
            updated_at      TIMESTAMPTZ
        )
    """),

    ("controls", """
        CREATE TABLE IF NOT EXISTS controls (
            id              VARCHAR(30) PRIMARY KEY,
            framework_id    VARCHAR(20) REFERENCES frameworks(id) ON DELETE SET NULL,
            family          VARCHAR(80) NOT NULL,
            family_abbrev   VARCHAR(4) NOT NULL,
            title           VARCHAR(500) NOT NULL,
            description     TEXT NOT NULL DEFAULT '',
            discussion      TEXT,
            nist_section    VARCHAR(20),
            points          INTEGER DEFAULT 1,
            poam_eligible   BOOLEAN DEFAULT TRUE,
            status          VARCHAR(20) DEFAULT 'not_assessed'
        )
    """),

    ("assessment_objectives", """
        CREATE TABLE IF NOT EXISTS assessment_objectives (
            id          VARCHAR(30) PRIMARY KEY,
            control_id  VARCHAR(30) NOT NULL REFERENCES controls(id) ON DELETE CASCADE,
            description TEXT NOT NULL DEFAULT '',
            examine     TEXT,
            interview   TEXT,
            test        TEXT,
            status      VARCHAR(20) DEFAULT 'not_assessed'
        )
    """),

    ("evidence_artifacts", """
        CREATE TABLE IF NOT EXISTS evidence_artifacts (
            id              VARCHAR(20) PRIMARY KEY,
            org_id          VARCHAR(20) NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            filename        VARCHAR(500) NOT NULL,
            file_path       VARCHAR(1000) NOT NULL DEFAULT '',
            file_size_bytes INTEGER,
            mime_type       VARCHAR(100),
            sha256_hash     VARCHAR(64),
            hash_algorithm  VARCHAR(20) DEFAULT 'sha256',
            state           VARCHAR(20) NOT NULL DEFAULT 'draft',
            evidence_type   VARCHAR(50),
            source_system   VARCHAR(100),
            description     TEXT,
            owner           VARCHAR(255),
            created_at      TIMESTAMPTZ DEFAULT NOW(),
            updated_at      TIMESTAMPTZ,
            reviewed_at     TIMESTAMPTZ,
            reviewed_by     VARCHAR(255),
            approved_at     TIMESTAMPTZ,
            approved_by     VARCHAR(255),
            published_at    TIMESTAMPTZ,
            metadata_json   JSON DEFAULT '{}'
        )
    """),

    # NO created_at column — matches models.py EvidenceControlMap
    ("evidence_control_map", """
        CREATE TABLE IF NOT EXISTS evidence_control_map (
            id              VARCHAR(20) PRIMARY KEY,
            evidence_id     VARCHAR(20) NOT NULL REFERENCES evidence_artifacts(id) ON DELETE CASCADE,
            control_id      VARCHAR(30) NOT NULL REFERENCES controls(id) ON DELETE CASCADE,
            objective_id    VARCHAR(30) REFERENCES assessment_objectives(id) ON DELETE SET NULL,
            relevance_score FLOAT,
            mapped_by       VARCHAR(50),
            UNIQUE(evidence_id, control_id, objective_id)
        )
    """),

    # Nessus scan imports (Phase 3.1A). Parent row per uploaded .nessus file.
    # Each import optionally links to an auto-created DRAFT evidence artifact.
    ("scan_imports", """
        CREATE TABLE IF NOT EXISTS scan_imports (
            id                   VARCHAR(20) PRIMARY KEY,
            org_id               VARCHAR(20) NOT NULL REFERENCES organizations(id),
            filename             VARCHAR(500) NOT NULL,
            scan_type            VARCHAR(20) NOT NULL DEFAULT 'NESSUS',
            scanner_version      VARCHAR(100),
            scan_date            TIMESTAMPTZ,
            imported_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            imported_by          VARCHAR REFERENCES users(id),
            host_count           INTEGER NOT NULL DEFAULT 0,
            finding_count        INTEGER NOT NULL DEFAULT 0,
            critical_count       INTEGER NOT NULL DEFAULT 0,
            high_count           INTEGER NOT NULL DEFAULT 0,
            medium_count         INTEGER NOT NULL DEFAULT 0,
            low_count            INTEGER NOT NULL DEFAULT 0,
            info_count           INTEGER NOT NULL DEFAULT 0,
            status               VARCHAR(20) NOT NULL DEFAULT 'PROCESSING',
            error_message        TEXT,
            evidence_artifact_id VARCHAR(20) REFERENCES evidence_artifacts(id),
            summary_text         TEXT
        )
    """),

    # Individual findings within a scan. CASCADE delete when parent goes.
    ("scan_findings", """
        CREATE TABLE IF NOT EXISTS scan_findings (
            id                   VARCHAR(20) PRIMARY KEY,
            scan_import_id       VARCHAR(20) NOT NULL REFERENCES scan_imports(id) ON DELETE CASCADE,
            org_id               VARCHAR(20) NOT NULL REFERENCES organizations(id),
            host_ip              VARCHAR(45) NOT NULL,
            hostname             VARCHAR(255),
            port                 INTEGER NOT NULL DEFAULT 0,
            protocol             VARCHAR(10),
            plugin_id            VARCHAR(20) NOT NULL,
            plugin_name          VARCHAR(500) NOT NULL,
            plugin_family        VARCHAR(200),
            severity             INTEGER NOT NULL DEFAULT 0,
            severity_label       VARCHAR(20) NOT NULL DEFAULT 'INFO',
            cvss_base_score      FLOAT,
            cvss3_base_score     FLOAT,
            cve_ids              JSON DEFAULT '[]',
            synopsis             TEXT,
            description          TEXT,
            solution             TEXT,
            risk_factor          VARCHAR(20),
            mapped_control_ids   JSON DEFAULT '[]',
            status               VARCHAR(20) NOT NULL DEFAULT 'OPEN',
            notes                TEXT,
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """),

    # Helper indexes — scan_findings grows fast and is queried by
    # org + severity + scan_import_id.
    ("scan_findings_idx_import", """
        CREATE INDEX IF NOT EXISTS idx_scan_findings_import ON scan_findings(scan_import_id)
    """),
    ("scan_findings_idx_org", """
        CREATE INDEX IF NOT EXISTS idx_scan_findings_org ON scan_findings(org_id)
    """),
    ("scan_findings_idx_sev", """
        CREATE INDEX IF NOT EXISTS idx_scan_findings_severity ON scan_findings(severity DESC)
    """),

    # ── Baseline engine (Phase 3.3) ──
    # Seeded catalog of security baselines (CIS, STIG) shared across orgs.
    ("baselines", """
        CREATE TABLE IF NOT EXISTS baselines (
            id           VARCHAR(20) PRIMARY KEY,
            name         VARCHAR(200) NOT NULL,
            version      VARCHAR(50) NOT NULL,
            source       VARCHAR(100) NOT NULL,
            platform     VARCHAR(100) NOT NULL,
            description  TEXT,
            item_count   INTEGER NOT NULL DEFAULT 0,
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """),
    ("baseline_items", """
        CREATE TABLE IF NOT EXISTS baseline_items (
            id                    VARCHAR(20) PRIMARY KEY,
            baseline_id           VARCHAR(20) NOT NULL REFERENCES baselines(id) ON DELETE CASCADE,
            cis_id                VARCHAR(50),
            section               VARCHAR(200),
            title                 VARCHAR(500) NOT NULL,
            description           TEXT,
            expected_value        TEXT,
            rationale             TEXT,
            severity              VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
            control_ids           TEXT[] NOT NULL,
            match_keywords        TEXT[],
            match_plugin_families TEXT[],
            created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """),
    ("org_baselines", """
        CREATE TABLE IF NOT EXISTS org_baselines (
            id          VARCHAR(20) PRIMARY KEY,
            org_id      VARCHAR(20) NOT NULL REFERENCES organizations(id),
            baseline_id VARCHAR(20) NOT NULL REFERENCES baselines(id),
            adopted_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            status      VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
            UNIQUE (org_id, baseline_id)
        )
    """),
    ("baseline_deviations", """
        CREATE TABLE IF NOT EXISTS baseline_deviations (
            id               VARCHAR(20) PRIMARY KEY,
            org_id           VARCHAR(20) NOT NULL REFERENCES organizations(id),
            org_baseline_id  VARCHAR(20) NOT NULL REFERENCES org_baselines(id) ON DELETE CASCADE,
            baseline_item_id VARCHAR(20) NOT NULL REFERENCES baseline_items(id),
            scan_finding_id  VARCHAR(20) REFERENCES scan_findings(id) ON DELETE SET NULL,
            actual_value     TEXT,
            status           VARCHAR(20) NOT NULL DEFAULT 'OPEN',
            notes            TEXT,
            detected_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            resolved_at      TIMESTAMPTZ,
            resolved_by      VARCHAR(20) REFERENCES users(id)
        )
    """),
    ("baseline_items_idx", """
        CREATE INDEX IF NOT EXISTS idx_baseline_items_baseline ON baseline_items(baseline_id)
    """),
    ("org_baselines_idx", """
        CREATE INDEX IF NOT EXISTS idx_org_baselines_org ON org_baselines(org_id)
    """),
    ("baseline_deviations_org_idx", """
        CREATE INDEX IF NOT EXISTS idx_baseline_deviations_org ON baseline_deviations(org_id)
    """),
    ("baseline_deviations_status_idx", """
        CREATE INDEX IF NOT EXISTS idx_baseline_deviations_status ON baseline_deviations(org_id, status)
    """),

    # models_ssp.py OVERRIDES models.py — uses evidence_refs (JSONB) and gaps (JSONB)
    ("ssp_sections", """
        CREATE TABLE IF NOT EXISTS ssp_sections (
            id                    VARCHAR(20) PRIMARY KEY,
            control_id            VARCHAR(30) NOT NULL REFERENCES controls(id),
            org_id                VARCHAR(100) NOT NULL DEFAULT 'default-org',
            narrative             TEXT NOT NULL DEFAULT '',
            implementation_status VARCHAR(30) NOT NULL DEFAULT 'Not Implemented',
            evidence_refs         JSONB DEFAULT '[]',
            gaps                  JSONB DEFAULT '[]',
            generated_by          VARCHAR(50) DEFAULT 'ssp_agent',
            version               INTEGER DEFAULT 1,
            created_at            TIMESTAMPTZ DEFAULT NOW(),
            updated_at            TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(org_id, control_id, version)
        )
    """),

    # Phase 4.1 — atomic claims extracted from SSP narratives. Each claim
    # is a verifiable factual statement that a C3PAO assessor would check.
    # ssp_section_id is intentionally unconstrained (no FK) because
    # sections version by (org, control, version) and claims should
    # survive section regeneration with a best-effort id carry-forward.
    ("claims", """
        CREATE TABLE IF NOT EXISTS claims (
            id                  VARCHAR(20) PRIMARY KEY,
            org_id              VARCHAR(20) NOT NULL REFERENCES organizations(id),
            control_id          VARCHAR(30) NOT NULL REFERENCES controls(id),
            ssp_section_id      VARCHAR(20),
            claim_text          TEXT NOT NULL,
            claim_type          VARCHAR(20) NOT NULL DEFAULT 'TECHNICAL',
            verification_status VARCHAR(20) NOT NULL DEFAULT 'UNVERIFIED',
            source_sentence     TEXT,
            source_span_start   INTEGER,
            source_span_end     INTEGER,
            confidence          REAL,
            evidence_refs       TEXT[],
            extracted_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            extraction_model    VARCHAR(50),
            verified_at         TIMESTAMPTZ,
            verified_by         VARCHAR(20) REFERENCES users(id),
            notes               TEXT
        )
    """),
    ("claims_idx_org", """
        CREATE INDEX IF NOT EXISTS idx_claims_org ON claims(org_id)
    """),
    ("claims_idx_control", """
        CREATE INDEX IF NOT EXISTS idx_claims_control ON claims(control_id)
    """),
    ("claims_idx_section", """
        CREATE INDEX IF NOT EXISTS idx_claims_section ON claims(ssp_section_id)
    """),
    ("claims_idx_status", """
        CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(verification_status)
    """),

    # Phase 4.2 — deterministic factual statements built from evidence
    # sources (scan findings, baseline deviations, intake, evidence,
    # contradictions). No LLM involved; IDs are stable hashes of
    # (source_type, source_id) so rebuilds are idempotent.
    ("observations", """
        CREATE TABLE IF NOT EXISTS observations (
            id                  VARCHAR(20) PRIMARY KEY,
            org_id              VARCHAR(20) NOT NULL REFERENCES organizations(id),
            observation_text    TEXT NOT NULL,
            source_type         VARCHAR(30) NOT NULL,
            source_id           VARCHAR(20),
            control_ids         TEXT[],
            observation_type    VARCHAR(20) NOT NULL DEFAULT 'TECHNICAL',
            confidence          REAL DEFAULT 1.0,
            observed_at         TIMESTAMPTZ,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            notes               TEXT
        )
    """),
    ("observations_idx_org", """
        CREATE INDEX IF NOT EXISTS idx_observations_org ON observations(org_id)
    """),
    ("observations_idx_source", """
        CREATE INDEX IF NOT EXISTS idx_observations_source ON observations(source_type)
    """),
    ("observations_idx_control", """
        CREATE INDEX IF NOT EXISTS idx_observations_control ON observations USING GIN(control_ids)
    """),

    # Phase 4.3 — LLM-determined relationship between one claim and one
    # observation (SUPPORTS / CONTRADICTS / UNRELATED). UNIQUE(claim_id,
    # observation_id) makes resolution idempotent at the row level;
    # resolve_control() deletes-then-inserts for semantic idempotency
    # when claims or observations have changed.
    ("resolutions", """
        CREATE TABLE IF NOT EXISTS resolutions (
            id             VARCHAR(20) PRIMARY KEY,
            org_id         VARCHAR(20) NOT NULL REFERENCES organizations(id),
            claim_id       VARCHAR(20) NOT NULL REFERENCES claims(id)       ON DELETE CASCADE,
            observation_id VARCHAR(20) NOT NULL REFERENCES observations(id) ON DELETE CASCADE,
            relationship   VARCHAR(20) NOT NULL,
            confidence     REAL NOT NULL DEFAULT 0.0,
            reasoning      TEXT,
            resolved_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            resolved_by    VARCHAR(20) REFERENCES users(id),
            model_used     VARCHAR(50),
            UNIQUE (claim_id, observation_id)
        )
    """),
    ("resolutions_idx_org", """
        CREATE INDEX IF NOT EXISTS idx_resolutions_org ON resolutions(org_id)
    """),
    ("resolutions_idx_claim", """
        CREATE INDEX IF NOT EXISTS idx_resolutions_claim ON resolutions(claim_id)
    """),
    ("resolutions_idx_rel", """
        CREATE INDEX IF NOT EXISTS idx_resolutions_relationship ON resolutions(relationship)
    """),

    # Phase 4.4 — per-org freshness threshold overrides. When empty the
    # module constants in src/truth/freshness.py apply. Composite PK
    # (org_id, evidence_type) so each org can tune each type once.
    # Phase 4.5 — stored simulation snapshots. Captures the truth-model
    # state, SPRS delta, method coverage, and LLM-generated assessor
    # findings at a single point in time for trend tracking.
    ("assessment_snapshots", """
        CREATE TABLE IF NOT EXISTS assessment_snapshots (
            id                      VARCHAR(20) PRIMARY KEY,
            org_id                  VARCHAR(20) NOT NULL REFERENCES organizations(id),
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by              VARCHAR(20) REFERENCES users(id),
            readiness_pct           REAL,
            sprs_actual             INTEGER,
            sprs_truth_adjusted     INTEGER,
            sprs_delta              INTEGER,
            total_claims            INTEGER,
            verified_claims         INTEGER,
            conflict_claims         INTEGER,
            unverified_claims       INTEGER,
            stale_claims            INTEGER,
            controls_at_risk        INTEGER,
            method_coverage_pct     REAL,
            findings_json           JSONB,
            details_json            JSONB
        )
    """),
    ("assessment_snapshots_idx_org", """
        CREATE INDEX IF NOT EXISTS idx_assessment_snapshots_org ON assessment_snapshots(org_id)
    """),
    ("assessment_snapshots_idx_created", """
        CREATE INDEX IF NOT EXISTS idx_assessment_snapshots_created ON assessment_snapshots(created_at DESC)
    """),

    # Phase 6.1 — export audit trail. Tracks what was exported, when,
    # and the package hash so orgs can verify old exports.
    ("export_records", """
        CREATE TABLE IF NOT EXISTS export_records (
            id              VARCHAR(20) PRIMARY KEY,
            org_id          VARCHAR(20) NOT NULL REFERENCES organizations(id),
            export_type     VARCHAR(50) NOT NULL,
            filename        VARCHAR(255),
            file_size_bytes BIGINT,
            package_hash    VARCHAR(128),
            artifact_count  INTEGER,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by      VARCHAR(20)
        )
    """),
    ("export_records_idx_org", """
        CREATE INDEX IF NOT EXISTS idx_export_records_org ON export_records(org_id)
    """),
    ("export_records_idx_type", """
        CREATE INDEX IF NOT EXISTS idx_export_records_type ON export_records(export_type)
    """),

    ("freshness_thresholds", """
        CREATE TABLE IF NOT EXISTS freshness_thresholds (
            org_id        VARCHAR(20) NOT NULL REFERENCES organizations(id),
            evidence_type VARCHAR(50) NOT NULL,
            fresh_days    INTEGER NOT NULL,
            aging_days    INTEGER NOT NULL,
            stale_days    INTEGER NOT NULL,
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (org_id, evidence_type)
        )
    """),

    ("poam_items", """
        CREATE TABLE IF NOT EXISTS poam_items (
            id                      VARCHAR(20) PRIMARY KEY,
            org_id                  VARCHAR(20) NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            control_id              VARCHAR(30) NOT NULL REFERENCES controls(id) ON DELETE CASCADE,
            weakness_description    TEXT NOT NULL DEFAULT '',
            remediation_plan        TEXT,
            milestone_changes       JSON DEFAULT '[]',
            resources_required      TEXT,
            scheduled_completion    TIMESTAMPTZ,
            actual_completion       TIMESTAMPTZ,
            status                  VARCHAR(20) DEFAULT 'OPEN',
            risk_level              VARCHAR(20),
            points                  INTEGER DEFAULT 1,
            source_type             VARCHAR(20) DEFAULT 'ASSESSMENT',
            source_id               VARCHAR(20),
            created_at              TIMESTAMPTZ DEFAULT NOW(),
            updated_at              TIMESTAMPTZ
        )
    """),

    # audit_log: id is SERIAL INTEGER, NO org_id column, actor_type NOT NULL
    ("audit_log", """
        CREATE TABLE IF NOT EXISTS audit_log (
            id          SERIAL PRIMARY KEY,
            timestamp   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            actor       VARCHAR(255) NOT NULL,
            actor_type  VARCHAR(50) NOT NULL,
            action      VARCHAR(100) NOT NULL,
            target_type VARCHAR(50),
            target_id   VARCHAR(30),
            details     JSON,
            prev_hash   VARCHAR(64),
            entry_hash  VARCHAR(64)
        )
    """),

    # ── Auth table — matches src/api/auth.py queries exactly ──
    # Column names: hashed_password (not password), full_name (not name).
    # is_admin kept for backward compat; role is the authoritative field
    # (SUPERADMIN / ADMIN / MEMBER / VIEWER). The role enum is created
    # idempotently in the migration block below (CREATE TABLE can't
    # reference an enum that doesn't yet exist when this block runs).
    ("users", """
        CREATE TABLE IF NOT EXISTS users (
            id                  VARCHAR PRIMARY KEY,
            email               VARCHAR UNIQUE NOT NULL,
            org_id              VARCHAR NOT NULL REFERENCES organizations(id),
            full_name           VARCHAR NOT NULL DEFAULT '',
            hashed_password     VARCHAR NOT NULL,
            is_admin            BOOLEAN NOT NULL DEFAULT FALSE,
            onboarding_complete BOOLEAN NOT NULL DEFAULT FALSE,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_login_at       TIMESTAMPTZ
        )
    """),

    # ── Intake tables from init_questionnaire_db.py ──

    ("intake_sessions", """
        CREATE TABLE IF NOT EXISTS intake_sessions (
            id                  VARCHAR(30) PRIMARY KEY,
            org_id              VARCHAR(30) NOT NULL REFERENCES organizations(id),
            started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            completed_at        TIMESTAMPTZ,
            current_module      INTEGER NOT NULL DEFAULT 0,
            status              VARCHAR(20) NOT NULL DEFAULT 'in_progress',
            modules_completed   INTEGER NOT NULL DEFAULT 0,
            total_questions     INTEGER NOT NULL DEFAULT 0,
            answered_questions  INTEGER NOT NULL DEFAULT 0,
            gap_count           INTEGER NOT NULL DEFAULT 0,
            estimated_sprs      INTEGER NOT NULL DEFAULT 0
        )
    """),

    ("intake_responses", """
        CREATE TABLE IF NOT EXISTS intake_responses (
            id              VARCHAR(30) PRIMARY KEY,
            session_id      VARCHAR(30) NOT NULL REFERENCES intake_sessions(id) ON DELETE CASCADE,
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
            answered_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(session_id, question_id)
        )
    """),

    ("intake_documents", """
        CREATE TABLE IF NOT EXISTS intake_documents (
            id              VARCHAR(30) PRIMARY KEY,
            session_id      VARCHAR(30) NOT NULL REFERENCES intake_sessions(id) ON DELETE CASCADE,
            org_id          VARCHAR(30) NOT NULL,
            doc_type        VARCHAR(50) NOT NULL DEFAULT '',
            title           VARCHAR(200) NOT NULL DEFAULT '',
            file_path       VARCHAR(500),
            generated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            status          VARCHAR(20) NOT NULL DEFAULT 'draft',
            control_ids     JSON NOT NULL DEFAULT '[]',
            word_count      INTEGER,
            sha256_hash     VARCHAR(64)
        )
    """),

    ("company_profiles", """
        CREATE TABLE IF NOT EXISTS company_profiles (
            id                  VARCHAR(30) PRIMARY KEY,
            org_id              VARCHAR(30) NOT NULL UNIQUE REFERENCES organizations(id),
            session_id          VARCHAR(30) REFERENCES intake_sessions(id),
            company_name        VARCHAR(200),
            cage_code           VARCHAR(10),
            duns_number         VARCHAR(15),
            employee_count      INTEGER,
            facility_count      INTEGER,
            primary_location    VARCHAR(200),
            cui_types           JSON DEFAULT '[]',
            cui_flow            VARCHAR(50),
            has_remote_workers  BOOLEAN DEFAULT FALSE,
            has_wireless        BOOLEAN DEFAULT FALSE,
            identity_provider   VARCHAR(100),
            email_platform      VARCHAR(100),
            email_tier          VARCHAR(50),
            edr_product         VARCHAR(100),
            firewall_product    VARCHAR(100),
            siem_product        VARCHAR(100),
            backup_solution     VARCHAR(100),
            existing_ssp        BOOLEAN DEFAULT FALSE,
            existing_poam       BOOLEAN DEFAULT FALSE,
            prior_assessment    BOOLEAN DEFAULT FALSE,
            dfars_7012_clause   BOOLEAN DEFAULT FALSE,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """),

    # ── Document engine tables from init_document_engine_db.py ──

    ("document_templates", """
        CREATE TABLE IF NOT EXISTS document_templates (
            id                  VARCHAR(30) PRIMARY KEY,
            doc_type            VARCHAR(50) NOT NULL UNIQUE,
            title               VARCHAR(200) NOT NULL,
            description         TEXT,
            sections            JSON NOT NULL,
            control_ids         JSON NOT NULL DEFAULT '[]',
            generation_rules    JSON NOT NULL DEFAULT '{}',
            conditional_on      VARCHAR(100),
            conditional_values  JSON DEFAULT '[]',
            min_modules_required JSON DEFAULT '[]',
            estimated_pages     INTEGER,
            created_at          TIMESTAMPTZ DEFAULT NOW()
        )
    """),

    ("generated_documents", """
        CREATE TABLE IF NOT EXISTS generated_documents (
            id                   VARCHAR(30) PRIMARY KEY,
            org_id               VARCHAR(30) NOT NULL REFERENCES organizations(id),
            template_id          VARCHAR(30) NOT NULL REFERENCES document_templates(id),
            doc_type             VARCHAR(50) NOT NULL,
            title                VARCHAR(200) NOT NULL,
            version              INTEGER NOT NULL DEFAULT 1,
            status               VARCHAR(20) NOT NULL DEFAULT 'draft',
            sections_data        JSON NOT NULL DEFAULT '[]',
            file_path            VARCHAR(500),
            file_content         BYTEA,
            word_count           INTEGER,
            generated_by         VARCHAR(50) DEFAULT 'document_engine',
            evidence_artifact_id VARCHAR(30),
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(org_id, doc_type, version)
        )
    """),

    # ── Other tables ──

    ("contact_requests", """
        CREATE TABLE IF NOT EXISTS contact_requests (
            id              VARCHAR PRIMARY KEY,
            name            VARCHAR NOT NULL,
            email           VARCHAR NOT NULL,
            company         VARCHAR,
            employee_count  VARCHAR,
            message         TEXT,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            status          VARCHAR NOT NULL DEFAULT 'new'
        )
    """),

    ("ssp_jobs", """
        CREATE TABLE IF NOT EXISTS ssp_jobs (
            job_id          VARCHAR(20) PRIMARY KEY,
            org_id          VARCHAR REFERENCES organizations(id),
            status          VARCHAR(20) NOT NULL DEFAULT 'pending',
            progress        TEXT NOT NULL DEFAULT 'Starting...',
            controls_done   INTEGER NOT NULL DEFAULT 0,
            controls_total  INTEGER NOT NULL DEFAULT 0,
            docx_path       TEXT,
            started_at      TIMESTAMPTZ,
            completed_at    TIMESTAMPTZ,
            error           TEXT
        )
    """),

    # Contradiction detection: cross-module consistency findings (2.9A).
    # One row per fired rule for an org. Status flow:
    #   OPEN → RESOLVED (rule no longer fires)
    #         → DISMISSED (user chose to ignore)
    #         → OVERRIDDEN (admin confirmed the claim is correct anyway)
    ("intake_contradictions", """
        CREATE TABLE IF NOT EXISTS intake_contradictions (
            id                       VARCHAR(20) PRIMARY KEY,
            org_id                   VARCHAR(20) NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            session_id               VARCHAR(30) REFERENCES intake_sessions(id) ON DELETE SET NULL,
            rule_id                  VARCHAR(50) NOT NULL,
            family                   VARCHAR(10) NOT NULL,
            severity                 VARCHAR(20) NOT NULL,
            status                   VARCHAR(20) NOT NULL DEFAULT 'OPEN',
            description              TEXT NOT NULL,
            source_question_id       VARCHAR(100) NOT NULL,
            source_answer            TEXT,
            conflicting_question_id  VARCHAR(100),
            conflicting_answer       TEXT,
            affected_control_ids     JSON NOT NULL DEFAULT '[]',
            resolution_notes         TEXT,
            resolved_by              VARCHAR REFERENCES users(id),
            resolved_at              TIMESTAMPTZ,
            detected_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (org_id, rule_id)
        )
    """),

    # Invites: time-limited registration codes issued by admins (1.6B).
    # user_role enum is created in the migration block below this CREATE
    # loop — so invites is listed AFTER users in DDL order but its role
    # column still resolves at create time because the enum migration is
    # idempotent and runs on every startup before any SELECT/INSERT hits
    # this table.
    ("invites", """
        CREATE TABLE IF NOT EXISTS invites (
            id         VARCHAR(64) PRIMARY KEY,
            org_id     VARCHAR NOT NULL REFERENCES organizations(id),
            code       VARCHAR UNIQUE NOT NULL,
            email      VARCHAR,
            role       VARCHAR(30) NOT NULL DEFAULT 'MEMBER',
            created_by VARCHAR NOT NULL REFERENCES users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ NOT NULL,
            used_at    TIMESTAMPTZ,
            used_by    VARCHAR
        )
    """),
]


# ---------------------------------------------------------------------------
# 3. SEED DATA
# ---------------------------------------------------------------------------

DEMO_ORG_ID = "9de53b587b23450b87af"


def seed_framework(cur):
    cur.execute("""
        INSERT INTO frameworks (id, name, version, control_count, description)
        VALUES ('nist80171r2_fw000001', 'CMMC Level 2', 'NIST 800-171 Rev 2', 110,
                'Cybersecurity Maturity Model Certification Level 2')
        ON CONFLICT (id) DO NOTHING
    """)
    logger.info("Framework seeded")


def seed_organization(cur):
    cur.execute("SELECT id FROM organizations WHERE id = %s", (DEMO_ORG_ID,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO organizations (id, name, system_name, employee_count) "
            "VALUES (%s, 'Apex Defense Solutions', 'Apex Secure Enclave', 45)",
            (DEMO_ORG_ID,),
        )
        logger.info("Created org: Apex Defense Solutions")
    else:
        logger.info("Org exists")


def seed_admin_user(cur):
    import bcrypt
    email = os.environ.get("ADMIN_EMAIL", "admin@intranest.ai")
    password = os.environ.get("ADMIN_PASSWORD", "Intranest2026!")
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # Seed / upsert the admin. role column always set to SUPERADMIN so this
    # user can access everything regardless of is_admin toggling elsewhere.
    cur.execute("""
        INSERT INTO users (id, email, org_id, full_name, hashed_password, is_admin, role)
        VALUES ('USR-ADMIN000001', %s, %s, 'Admin', %s, TRUE, 'SUPERADMIN'::user_role)
        ON CONFLICT (id) DO UPDATE SET
            email = EXCLUDED.email,
            hashed_password = EXCLUDED.hashed_password,
            is_admin = TRUE,
            role = 'SUPERADMIN'::user_role
    """, (email, DEMO_ORG_ID, hashed))
    logger.info(f"Admin user ready: {email} (SUPERADMIN)")


def seed_controls(cur):
    cur.execute("SELECT COUNT(*) FROM controls")
    count = cur.fetchone()[0]
    if count >= 110:
        logger.info(f"Controls already loaded: {count}")
        return

    logger.info(f"Controls: {count}/110 — loading full NIST dataset...")
    from data.nist.controls_full import NIST_800_171_CONTROLS
    for c in NIST_800_171_CONTROLS:
        cur.execute("""
            INSERT INTO controls (id, family, family_abbrev, title, description, discussion, nist_section, points, poam_eligible)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (c["id"], c["family"], c["family_id"], c["title"], c["description"],
              c.get("discussion", ""), c.get("nist_section", ""), c["points"], c["poam_eligible"]))
    logger.info(f"Loaded {len(NIST_800_171_CONTROLS)} controls")


def seed_objectives(cur):
    cur.execute("SELECT COUNT(*) FROM assessment_objectives")
    count = cur.fetchone()[0]
    if count >= 200:
        logger.info(f"Objectives already loaded: {count}")
        return

    logger.info(f"Objectives: {count} — loading...")
    from data.nist.objectives_full import ASSESSMENT_OBJECTIVES
    for o in ASSESSMENT_OBJECTIVES:
        cur.execute("""
            INSERT INTO assessment_objectives (id, control_id, description, examine, interview, test)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (o["id"], o["control_id"], o["description"], o.get("examine", ""),
              o.get("interview", ""), o.get("test", "")))
    logger.info(f"Loaded {len(ASSESSMENT_OBJECTIVES)} objectives")


def _compute_entry_hash(actor, actor_type, action, target_type, target_id,
                        details, prev_hash, timestamp):
    """
    MUST match src/evidence/state_machine.py::_compute_entry_hash exactly.
    The verifier uses this exact payload shape + sort_keys=True.
    """
    payload = json.dumps(
        {
            "actor": actor,
            "actor_type": actor_type,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "details": details,
            "prev_hash": prev_hash,
            "timestamp": timestamp,
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def seed_audit_genesis(cur):
    from datetime import datetime, timezone
    cur.execute("SELECT COUNT(*) FROM audit_log")
    count = cur.fetchone()[0]
    if count > 0:
        logger.info(f"Audit log already has {count} entries — skipping genesis seed")
        return

    now = datetime.now(timezone.utc)
    timestamp_iso = now.isoformat()
    details = {"message": "Audit chain genesis"}

    # Use the same hash algorithm the verifier uses — otherwise the
    # chain fails verification at entry #1 (the genesis row itself).
    entry_hash = _compute_entry_hash(
        actor="SYSTEM",
        actor_type="system",
        action="GENESIS",
        target_type="system",
        target_id="system",
        details=details,
        prev_hash="GENESIS",
        timestamp=timestamp_iso,
    )

    cur.execute("""
        INSERT INTO audit_log (timestamp, actor, actor_type, action, target_type, target_id, details, prev_hash, entry_hash)
        VALUES (%s, 'SYSTEM', 'system', 'GENESIS', 'system', 'system', CAST(%s AS json), 'GENESIS', %s)
    """, (now, json.dumps(details), entry_hash))
    logger.info("Created genesis audit log entry (hash-aligned with verifier)")


def heal_audit_chain(cur):
    """
    Idempotent self-heal for the audit chain.
    Walks every audit_log row in id ASC order and recomputes the correct
    prev_hash + entry_hash. Only writes updates for rows that are wrong.
    No-op when the chain is already intact.

    Necessary because early seeders used a broken hash algorithm
    (sha256("GENESIS") instead of sha256(json_payload)). This function
    repairs any stale data and is safe to run on every deploy.
    """
    cur.execute("""
        SELECT id, actor, actor_type, action, target_type, target_id,
               details, prev_hash, entry_hash, timestamp
        FROM audit_log ORDER BY id ASC
    """)
    rows = cur.fetchall()
    if not rows:
        return

    expected_prev = "GENESIS"
    fixed = 0
    for row in rows:
        (rid, actor, actor_type, action, ttype, tid,
         details, old_prev, old_hash, ts) = row

        # Normalize details to dict (matches verifier behavior)
        if isinstance(details, str):
            try:
                details_dict = json.loads(details)
            except Exception:
                details_dict = {}
        elif details is None:
            details_dict = {}
        else:
            details_dict = details

        ts_iso = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)

        new_hash = _compute_entry_hash(
            actor=actor, actor_type=actor_type, action=action,
            target_type=ttype, target_id=tid,
            details=details_dict, prev_hash=expected_prev, timestamp=ts_iso,
        )

        if old_prev != expected_prev or old_hash != new_hash:
            cur.execute(
                "UPDATE audit_log SET prev_hash = %s, entry_hash = %s WHERE id = %s",
                (expected_prev, new_hash, rid),
            )
            fixed += 1

        expected_prev = new_hash

    if fixed:
        logger.info(f"Audit chain: healed {fixed}/{len(rows)} entries")
    else:
        logger.info(f"Audit chain: intact ({len(rows)} entries, no repair needed)")


def seed_document_templates(cur):
    """Delegate to the existing init_document_engine_db.py seeder."""
    cur.execute("SELECT COUNT(*) FROM document_templates")
    if cur.fetchone()[0] >= 7:
        logger.info("Document templates already seeded")
        return
    logger.info("Seeding document templates via init_document_engine_db.py...")


# ---------------------------------------------------------------------------
# 4. MAIN
# ---------------------------------------------------------------------------

def main():
    logger.info("=" * 60)
    logger.info("INTRANEST PLATFORM — RENDER STARTUP")
    logger.info(f"DATABASE_URL present: {bool(os.environ.get('DATABASE_URL'))}")
    logger.info("=" * 60)

    wait_for_db()

    # Drop and recreate if RESET_SCHEMA is set (one-time fix for schema mismatches)
    if os.environ.get("RESET_SCHEMA", "false").lower() == "true":
        logger.info("RESET_SCHEMA=true — dropping all tables for clean recreation...")
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            DROP TABLE IF EXISTS
                ssp_jobs, contact_requests, generated_documents, document_templates,
                intake_documents, intake_responses, company_profiles, intake_sessions,
                evidence_control_map, ssp_sections, poam_items, audit_log,
                evidence_artifacts, assessment_objectives, controls, users,
                frameworks, organizations
            CASCADE
        """)
        conn.commit()
        conn.close()
        logger.info("All tables dropped")

    # Create all tables
    logger.info("Creating database tables...")
    conn = get_connection()
    cur = conn.cursor()
    for name, ddl in TABLES_DDL:
        try:
            cur.execute(ddl)
            conn.commit()
            logger.info(f"  {name}: OK")
        except Exception as e:
            conn.rollback()
            logger.error(f"  {name}: FAILED — {e}")
            logger.error(f"FATAL: Could not create table {name}")
            conn.close()
            sys.exit(1)

    # Idempotent migrations for constraints that CREATE TABLE IF NOT EXISTS
    # won't add to pre-existing tables.
    try:
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'ssp_sections_org_id_control_id_version_key'
                ) THEN
                    ALTER TABLE ssp_sections
                    ADD CONSTRAINT ssp_sections_org_id_control_id_version_key
                    UNIQUE (org_id, control_id, version);
                END IF;
            END$$;
        """)
        conn.commit()
        logger.info("  ssp_sections UNIQUE(org_id, control_id, version): OK")
    except Exception as e:
        conn.rollback()
        logger.warning(f"  ssp_sections unique constraint migration skipped: {e}")

    # users.role — SUPERADMIN/ADMIN/MEMBER/VIEWER. Enum + column + backfill, all idempotent.
    try:
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
                    CREATE TYPE user_role AS ENUM ('SUPERADMIN', 'ADMIN', 'MEMBER', 'VIEWER');
                END IF;
            END$$;
        """)
        cur.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS role user_role DEFAULT 'MEMBER'
        """)
        cur.execute("""
            UPDATE users
            SET role = 'ADMIN'::user_role
            WHERE is_admin = TRUE AND role = 'MEMBER'::user_role
        """)
        conn.commit()
        logger.info("  users.role user_role enum + column: OK")
    except Exception as e:
        conn.rollback()
        logger.warning(f"  users.role migration skipped: {e}")

    # poam_items.source_type / .source_id — 3.1C: distinguish scan-driven
    # POA&M items from assessment-driven ones. Idempotent.
    try:
        cur.execute("""
            ALTER TABLE poam_items
            ADD COLUMN IF NOT EXISTS source_type VARCHAR(20) DEFAULT 'ASSESSMENT'
        """)
        cur.execute("""
            ALTER TABLE poam_items
            ADD COLUMN IF NOT EXISTS source_id   VARCHAR(20)
        """)
        conn.commit()
        logger.info("  poam_items.source_type + .source_id: OK")
    except Exception as e:
        conn.rollback()
        logger.warning(f"  poam_items source_* migration skipped: {e}")

    # ssp_jobs.org_id — tenant isolation for /api/ssp/status, /cancel, /exports.
    # Existing rows predate multi-tenancy, so backfill them with the demo org.
    try:
        cur.execute("""
            ALTER TABLE ssp_jobs
            ADD COLUMN IF NOT EXISTS org_id VARCHAR REFERENCES organizations(id)
        """)
        cur.execute(
            "UPDATE ssp_jobs SET org_id = %s WHERE org_id IS NULL",
            (DEMO_ORG_ID,),
        )
        conn.commit()
        logger.info("  ssp_jobs.org_id: OK (backfilled NULLs with demo org)")
    except Exception as e:
        conn.rollback()
        logger.warning(f"  ssp_jobs.org_id migration skipped: {e}")

    # users.onboarding_complete — per-user flag for 1.6F wizard gating.
    # Admin (and any legacy user) is marked complete so the wizard doesn't
    # trigger for the seeded demo org.
    try:
        cur.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS onboarding_complete BOOLEAN NOT NULL DEFAULT FALSE
        """)
        cur.execute(
            "UPDATE users SET onboarding_complete = TRUE WHERE email = %s",
            (os.environ.get("ADMIN_EMAIL", "admin@intranest.ai"),),
        )
        conn.commit()
        logger.info("  users.onboarding_complete BOOLEAN: OK (admin backfilled TRUE)")
    except Exception as e:
        conn.rollback()
        logger.warning(f"  users.onboarding_complete migration skipped: {e}")

    # company_profiles.training_solution — schema gap from 1.6C so onboarding
    # can persist the training tool (there's no Module 0 question for it).
    try:
        cur.execute("""
            ALTER TABLE company_profiles
            ADD COLUMN IF NOT EXISTS training_solution VARCHAR(100)
        """)
        conn.commit()
        logger.info("  company_profiles.training_solution VARCHAR(100): OK")
    except Exception as e:
        conn.rollback()
        logger.warning(f"  company_profiles.training_solution migration skipped: {e}")

    # company_profiles SPRS submission fields — Phase 6.3.
    for col_ddl in [
        "ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS uei VARCHAR(20)",
        "ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS ssp_version VARCHAR(50)",
        "ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS ssp_date DATE",
        "ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS cui_scope_description TEXT",
        "ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS assessing_entity VARCHAR(100) DEFAULT 'Self'",
    ]:
        try:
            cur.execute(col_ddl)
            conn.commit()
        except Exception:
            conn.rollback()
    logger.info("  company_profiles SPRS columns: OK")

    # baseline_items.match_plugin_ids — Phase 3.3C: exact Nessus plugin ID
    # matching for precision. Without this, keyword substring matching
    # produces way too many false-positive deviations.
    try:
        cur.execute("""
            ALTER TABLE baseline_items
            ADD COLUMN IF NOT EXISTS match_plugin_ids TEXT[]
        """)
        conn.commit()
        logger.info("  baseline_items.match_plugin_ids TEXT[]: OK")
    except Exception as e:
        conn.rollback()
        logger.warning(f"  baseline_items.match_plugin_ids migration skipped: {e}")

    # users.deactivated_at — soft-delete column for 1.6B admin user management.
    try:
        cur.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS deactivated_at TIMESTAMPTZ
        """)
        conn.commit()
        logger.info("  users.deactivated_at TIMESTAMPTZ: OK")
    except Exception as e:
        conn.rollback()
        logger.warning(f"  users.deactivated_at migration skipped: {e}")

    # organizations.city / .state — used by the onboarding wizard (1.6B/1.6F).
    try:
        cur.execute("""
            ALTER TABLE organizations ADD COLUMN IF NOT EXISTS city  VARCHAR(100);
            ALTER TABLE organizations ADD COLUMN IF NOT EXISTS state VARCHAR(50);
        """)
        conn.commit()
        logger.info("  organizations.city + .state: OK")
    except Exception as e:
        conn.rollback()
        logger.warning(f"  organizations.city/state migration skipped: {e}")

    # intake_responses.question_tier — new column for tiered intake. Idempotent.
    try:
        cur.execute("""
            ALTER TABLE intake_responses
            ADD COLUMN IF NOT EXISTS question_tier VARCHAR(30) DEFAULT 'SCREENING'
        """)
        conn.commit()
        logger.info("  intake_responses.question_tier VARCHAR(30): OK")
    except Exception as e:
        conn.rollback()
        logger.warning(f"  question_tier migration skipped: {e}")

    # generated_documents.file_content — store DOCX bytes so downloads
    # survive Render's ephemeral filesystem. Idempotent for existing DBs.
    try:
        cur.execute("""
            ALTER TABLE generated_documents
            ADD COLUMN IF NOT EXISTS file_content BYTEA
        """)
        conn.commit()
        logger.info("  generated_documents.file_content BYTEA: OK")
    except Exception as e:
        conn.rollback()
        logger.warning(f"  file_content migration skipped: {e}")

    # Backfill file_content from filesystem for any rows that still
    # have a readable file_path but no stored bytes (local dev mostly).
    try:
        import psycopg2 as _pg
        cur.execute("""
            SELECT id, file_path FROM generated_documents
            WHERE file_content IS NULL AND file_path IS NOT NULL
        """)
        backfilled = 0
        for rid, fp in cur.fetchall():
            if fp and os.path.exists(fp):
                try:
                    with open(fp, "rb") as f:
                        blob = f.read()
                    cur.execute(
                        "UPDATE generated_documents SET file_content = %s WHERE id = %s",
                        (_pg.Binary(blob), rid),
                    )
                    backfilled += 1
                except Exception as read_err:
                    logger.warning(f"  backfill read failed for {rid}: {read_err}")
        conn.commit()
        if backfilled:
            logger.info(f"  generated_documents: backfilled {backfilled} file_content blobs")
    except Exception as e:
        conn.rollback()
        logger.warning(f"  file_content backfill skipped: {e}")

    # Verify tables exist
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
    existing = [row[0] for row in cur.fetchall()]
    logger.info(f"Tables in database: {existing}")
    required = ["organizations", "controls", "users", "ssp_sections", "evidence_artifacts",
                 "poam_items", "audit_log", "frameworks", "ssp_jobs"]
    missing = [t for t in required if t not in existing]
    if missing:
        logger.error(f"FATAL: Required tables MISSING: {missing}")
        conn.close()
        sys.exit(1)
    conn.close()
    logger.info("All tables verified")

    # Seed data
    logger.info("Seeding data...")
    conn = get_connection()
    cur = conn.cursor()
    try:
        seed_framework(cur)
        seed_organization(cur)
        seed_admin_user(cur)
        seed_controls(cur)
        seed_objectives(cur)
        seed_audit_genesis(cur)
        heal_audit_chain(cur)
        seed_document_templates(cur)
        try:
            from src.baselines.seeds import seed_baselines
            seed_baselines(cur)
        except Exception as e:
            logger.warning(f"Baseline seeding skipped: {e}")
        conn.commit()
        logger.info("All seed data committed")
    except Exception as e:
        conn.rollback()
        logger.error(f"FATAL: Seeding failed — {e}")
        conn.close()
        sys.exit(1)
    conn.close()

    # Run document template seeder (uses SQLAlchemy session)
    try:
        import subprocess
        subprocess.run([sys.executable, "scripts/init_document_engine_db.py"], check=False)
    except Exception:
        logger.warning("Document template seeding skipped")

    # Verify row counts
    logger.info("--- Data verification ---")
    conn = get_connection()
    cur = conn.cursor()
    for table in ["organizations", "controls", "assessment_objectives", "users",
                   "audit_log", "document_templates", "ssp_jobs"]:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            logger.info(f"  {table}: {cur.fetchone()[0]} rows")
        except Exception as e:
            logger.warning(f"  {table}: ERROR — {e}")
    conn.close()

    # Ensure runtime directories
    for d in ["data/evidence", "data/exports"]:
        os.makedirs(d, exist_ok=True)

    # Start uvicorn
    port = os.environ.get("PORT", "8001")
    logger.info(f"Starting uvicorn on port {port}...")
    os.execvp(
        sys.executable,
        [sys.executable, "-m", "uvicorn", "src.api.main:app",
         "--host", "0.0.0.0", "--port", port],
    )


if __name__ == "__main__":
    main()
