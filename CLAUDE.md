# CMMC Compliance Platform — Claude Code Context

## What This Is

A sovereign AI-powered CMMC Level 2 compliance platform for small defense contractors.
Solo founder project. Target customer: subcontractors (10–200 employees) who handle CUI
and need CMMC Level 2 certification to keep DoD contracts.

**Core value proposition:** Automates the hardest parts of CMMC compliance — generating
System Security Plans (SSPs) using AI, managing evidence artifacts with a tamper-evident
audit chain, calculating SPRS scores, and auto-generating POA&M items.

---

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI (Python 3.11), Uvicorn |
| Dashboard | Streamlit (`src/ui/dashboard.py`) |
| LLM | Claude API (dev) / vLLM OpenAI-compatible (prod) |
| Database | PostgreSQL 16 |
| Vector store | Qdrant (NIST 800-171 control embeddings) |
| Workflow engine | Temporal (durable SSP generation jobs) |
| Embeddings | BAAI/bge-small-en-v1.5 (dev), Snowflake Arctic (prod) |
| ORM | SQLAlchemy (raw SQL for performance-critical paths) |

---

## Project Layout

```
cmmc-platform/
├── configs/
│   └── settings.py          # All config — reads from env vars, has dev defaults
├── src/
│   ├── agents/
│   │   ├── llm_client.py    # Unified LLM interface (Claude API or vLLM)
│   │   ├── ssp_generator.py # RAG + LLM SSP narrative generator
│   │   └── ssp_prompts.py   # Prompt templates + DEMO_ORG_PROFILE
│   ├── api/
│   │   ├── main.py          # FastAPI app entry point
│   │   ├── ssp_routes.py    # POST /api/ssp/generate, /generate-full, /generate-full-temporal
│   │   ├── evidence_routes.py # Evidence upload, transitions, linking, manifests
│   │   └── scoring_routes.py  # SPRS score, gaps, POA&M, overview
│   ├── db/
│   │   ├── models.py        # 8-table SQLAlchemy schema
│   │   ├── models_ssp.py    # SSP section model (may be merged into models.py)
│   │   └── session.py       # SessionLocal, get_db, get_session context manager
│   ├── evidence/
│   │   ├── hasher.py        # SHA-256 hashing, manifest generation, verify_hash
│   │   ├── state_machine.py # DRAFT→REVIEWED→APPROVED→PUBLISHED + audit chain
│   │   └── storage.py       # File upload, artifact CRUD, control linking
│   ├── rag/
│   │   ├── embedder.py      # EmbeddingService wrapping sentence-transformers
│   │   └── chunker.py       # Chunks NIST controls/objectives for Qdrant ingestion
│   ├── scoring/
│   │   ├── sprs.py          # SPRSCalculator — computes SPRS score from DB
│   │   ├── gap_assessment.py # GapAssessmentEngine — cross-references SSP + evidence
│   │   └── poam.py          # POAMGenerator — auto-creates 180-day POA&M items
│   ├── ssp/
│   │   ├── docx_export.py   # Exports SSP results to Word (.docx)
│   │   └── binder_export.py # Full compliance binder export
│   ├── ui/
│   │   └── dashboard.py     # Streamlit multi-page dashboard
│   └── workflows/
│       ├── ssp_workflow.py  # Temporal workflow + activities for SSP generation
│       ├── worker.py        # Temporal worker process
│       └── trigger_ssp.py   # CLI to kick off SSP workflow
├── tests/
│   ├── test_hasher.py       # SHA-256 hashing pipeline tests
│   ├── test_state_machine.py # Evidence state machine + audit chain tests
│   ├── test_scoring.py      # SPRS, gap assessment, POA&M tests
│   └── test_api.py          # FastAPI endpoint tests (TestClient, mocked)
├── scripts/
│   ├── init_db.py           # One-time DB schema creation
│   ├── load_nist_to_postgres.py  # Seeds 110 controls + 246 objectives
│   ├── load_nist_to_qdrant.py    # Embeds controls/objectives into Qdrant
│   └── generate_ssp.py      # CLI script for SSP generation
├── docker-compose.yml       # Dev: postgres, qdrant, temporal, temporal-ui
└── docker/                  # Prod Dockerfiles go here (not yet created)
```

---

## Database Schema (8 tables)

| Table | Purpose |
|---|---|
| `organizations` | Single org for MVP. Multi-tenant later. |
| `controls` | 110 NIST 800-171 Rev 2 controls with SPRS weights |
| `assessment_objectives` | 246 objectives from NIST 800-171A |
| `evidence_artifacts` | Uploaded files with state machine (DRAFT→PUBLISHED) |
| `evidence_control_map` | M2M: evidence ↔ controls/objectives |
| `ssp_sections` | AI-generated SSP narratives per control per org |
| `poam_items` | Plan of Action & Milestones (180-day remediation) |
| `audit_log` | Append-only, SHA-256 hash-chained tamper-evident ledger |

---

## Services (Docker)

| Service | Port | Purpose |
|---|---|---|
| `cmmc-postgres` | 5432 | Primary database |
| `cmmc-qdrant` | 6333 | Vector store for NIST control embeddings |
| `cmmc-temporal` | 7233 | Durable workflow engine |
| `cmmc-temporal-ui` | 8080 | Temporal workflow monitoring UI |

Start all: `docker-compose up -d`

---

## Key Config (configs/settings.py)

All values read from environment variables with dev defaults:

```
ANTHROPIC_API_KEY      → LLM API key (never commit a real key)
DATABASE_URL           → postgresql://cmmc:localdev@localhost:5432/cmmc
QDRANT_HOST            → localhost
TEMPORAL_HOST          → localhost:7233
EVIDENCE_DIR           → data/evidence (relative, not absolute Windows path)
SSP_EXPORT_DIR         → data/exports
LLM_MODEL              → claude-sonnet-4-20250514
```

---

## Running Locally

```powershell
# 1. Start infrastructure
docker-compose up -d

# 2. Activate venv
.\venv\Scripts\Activate.ps1

# 3. Start FastAPI
uvicorn src.api.main:app --reload --port 8000

# 4. Start Streamlit dashboard
python -m streamlit run src/ui/dashboard.py --server.port 8501

# 5. Start Temporal worker (in a separate terminal)
python -m src.workflows.worker
```

API docs: http://localhost:8000/docs
Dashboard: http://localhost:8501
Temporal UI: http://localhost:8080

---

## Tests

```powershell
pytest tests/ -k "not integration"   # 64 unit tests, no live services needed
pytest tests/ -m integration         # live DB smoke tests (requires postgres)
```

---

## Demo Org

The built-in demo organization is **Apex Defense Solutions** (org_id: `9de53b587b23450b87af`).
It's a realistic 45-person defense contractor with a fully-described tool stack used as the
default context for SSP generation. All dev scripts and API defaults use this org.

---

## LLM Architecture

`ComplianceLLM` in `src/agents/llm_client.py` abstracts both providers:
- **Dev:** `provider="anthropic"` → Claude API directly
- **Prod:** `provider="openai_compatible"` → vLLM endpoint (sovereign, air-gapped deployment)

Switch by setting env vars: `LLM_PROVIDER=openai_compatible`, `LLM_BASE_URL=http://...`

---

## Evidence State Machine

```
DRAFT → REVIEWED → APPROVED → PUBLISHED (terminal, immutable)
                ↓
            DRAFT (can go back)
```

PUBLISHED artifacts: SHA-256 hash locked, file is immutable, hash recorded in audit log.
Every transition writes a hash-chained entry to `audit_log` (SHA-256 chain, GENESIS seed).

---

## SPRS Scoring

- Start at 110 (all controls met)
- Subtract control's point weight for each NOT MET or NOT ASSESSED control
- Floor: -203
- POA&M eligibility threshold: score ≥ 88
- 5-point controls = CRITICAL severity gaps
- `CA.L2-3.12.4` (System Security Plan) CANNOT be placed on POA&M

---

## Production Gaps (not yet built)

See `docs/production_readiness.md` for full tracker.

Critical items:
1. No authentication (JWT needed on all endpoints)
2. No `.env` / secrets management
3. Hardcoded Windows paths in source (`D:/cmmc-platform/...`)
4. No Dockerfile for the API or dashboard
5. CORS is `allow_origins=["*"]`
6. No Alembic migrations
7. `_jobs` dict in `ssp_routes.py` is in-memory (lost on restart)

---

## Coding Conventions

- Raw SQL via `sqlalchemy.text()` for DB queries (not ORM where performance matters)
- All DB sessions via `get_session()` context manager or `get_db()` FastAPI dependency
- IDs are short hex strings generated at insert time (not UUID4 objects)
- Evidence artifact IDs prefixed `EVD-`, POA&M IDs prefixed `poam-`
- Audit log entries computed with `_compute_entry_hash()` — don't bypass this
- All state transitions go through `transition_evidence()` in `state_machine.py` — never update `evidence_artifacts.state` directly
