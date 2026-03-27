# CMMC Platform — Build Context
<!-- Living document. Update after each significant session. -->
<!-- Last updated: 2026-03-11 -->

---

## What This Is

Sovereign AI-powered CMMC Level 2 compliance platform for small defense contractors
(10–200 employees). Solo founder project. Core value: automate SSP generation, evidence
management, SPRS scoring, gap assessment, and POA&M creation so subcontractors can
achieve certification without hiring a compliance consultant.

Demo org: **Apex Defense Solutions** — 45-person contractor, `org_id: 9de53b587b23450b87af`

---

## Current State: MVP Feature-Complete, Pre-Shippable

All compliance logic is built and tested. The gap is infrastructure and hardening,
not features.

### Built and Working

| Area | Files | Notes |
|---|---|---|
| **SPRS scoring** | `src/scoring/sprs.py` | Start 110, subtract per NOT MET/NOT ASSESSED, floor -203 |
| **Gap assessment** | `src/scoring/gap_assessment.py` | 5 gap types, 3 severities (CRITICAL/HIGH/MEDIUM) |
| **POA&M generation** | `src/scoring/poam.py` | 180-day deadlines, milestone templates, eligibility rules |
| **Evidence pipeline** | `src/evidence/state_machine.py`, `hasher.py`, `storage.py` | DRAFT→PUBLISHED state machine, SHA-256 hash-chained audit log |
| **SSP generation** | `src/agents/ssp_generator.py`, `llm_client.py` | RAG + LLM, three paths: sync / background / Temporal |
| **LLM abstraction** | `src/agents/llm_client.py` | Unified interface: Claude API (dev) or vLLM (prod) |
| **Temporal workflows** | `src/workflows/ssp_workflow.py`, `worker.py` | Durable per-control generation, retries, Word export activity |
| **Word export** | `src/ssp/docx_export.py` | Professional .docx, cover page, per-family sections, evidence tables |
| **All 22 API endpoints** | `src/api/ssp_routes.py`, `evidence_routes.py`, `scoring_routes.py` | FastAPI, full request/response models |
| **JWT auth** | `src/api/auth.py` | Register/login/me, bcrypt passwords, org isolation via token |
| **DB schema** | `src/db/models.py` | 8 tables, indexes, relationships — organizations, controls, evidence, ssp_sections, poam_items, audit_log |
| **RAG layer** | `src/rag/embedder.py`, `chunker.py` | sentence-transformers, Qdrant vector store, NIST control embeddings |
| **Dashboard** | `src/ui/dashboard.py` | Streamlit multi-page: SPRS gauge, gap summary, evidence upload, SSP generation |
| **Unit tests** | `tests/` | 64 tests: API, state machine, hashing, scoring — all pass without live services |

### Partially Done

| Area | File | Gap |
|---|---|---|
| **SSP output parser** | `ssp_generator.py:_parse_ssp_output()` | Regex-based; breaks on LLM formatting variations. Needs structured output or stricter prompting |
| **Job tracking** | `ssp_routes.py` | In-memory `_jobs` dict — lost on restart. `scripts/add_ssp_jobs_table.py` exists but not wired into routes |
| **Dashboard auth** | `src/ui/dashboard.py` | Hardcoded `org_id = "9de53b587b23450b87af"`. Needs JWT session so users see their own data |
| **Dashboard UX** | `src/ui/dashboard.py` | SSP generation progress shows "run this terminal command" instead of polling the API |

### Not Built Yet

| Area | Priority | Notes |
|---|---|---|
| **Dockerfiles** | BLOCKER | `docker/` directory is empty. Need API, dashboard, and Temporal worker containers |
| **Alembic migrations** | HIGH | Schema changes done via one-off `scripts/add_*.py` files. No migration history |
| **Rate limiting** | HIGH | No per-IP or per-user limits on any endpoints |
| **POA&M update workflow** | MEDIUM | Can generate POA&Ms but no UI/API to update status (IN_PROGRESS, CLOSED) |
| **OVERDUE automation** | MEDIUM | POA&M items past 180 days never auto-flip to OVERDUE |
| **Score history** | MEDIUM | SPRS score is always recalculated live; no historical trend data |
| **PIEE/eMASS export** | LOW | Manifest generation exists but no PIEE-formatted export |
| **Multi-tenancy** | POST-MVP | Schema is multi-tenant ready (`org_id` everywhere) but no org provisioning flow |
| **EvidenceReviewWorkflow** | POST-MVP | Temporal workflow for evidence review — designed but not implemented |
| **Assessor portal** | POST-MVP | Read-only view for third-party assessors |

---

## Tech Stack

| Layer | Technology | Version | Notes |
|---|---|---|---|
| API | FastAPI | 0.135.1 | Uvicorn 0.41.0 |
| Dashboard | Streamlit | 1.55.0 | Port 8501 |
| LLM (dev) | Claude API | anthropic 0.84.0 | claude-sonnet-4-20250514 |
| LLM (prod) | vLLM + OpenAI SDK | openai 2.26.0 | Air-gapped sovereign deployment |
| Database | PostgreSQL 16 | psycopg2-binary 2.9.11 | SQLAlchemy 2.0.48 |
| Vector store | Qdrant | qdrant-client 1.17.0 | NIST 800-171 control embeddings |
| Workflows | Temporal | temporalio 1.23.0 | Task queue: `cmmc-ssp` |
| Embeddings | sentence-transformers | 5.2.3 | BAAI/bge-small-en-v1.5 (dev), Snowflake Arctic (prod) |
| Auth | python-jose + passlib | 3.5.0 / 1.7.4 | HS256 JWT, bcrypt passwords |
| Export | python-docx | 1.2.0 | Word .docx SSP export |
| Config | python-dotenv | 1.1.0 | `.env` → `configs/settings.py` |

---

## Infrastructure (Local Dev)

```
docker-compose up -d   # starts all four services

cmmc-postgres    :5432   PostgreSQL 16
cmmc-qdrant      :6333   Qdrant vector store
cmmc-temporal    :7233   Temporal workflow engine
cmmc-temporal-ui :8080   Temporal monitoring UI
```

API:       http://localhost:8000
API docs:  http://localhost:8000/docs
Dashboard: http://localhost:8501

Start sequence:
```
docker-compose up -d
.\venv\Scripts\Activate.ps1
uvicorn src.api.main:app --reload --port 8000
python -m streamlit run src/ui/dashboard.py --server.port 8501
python -m src.workflows.worker   # separate terminal, needed for Temporal SSP jobs
```

One-time DB setup (already done for demo org):
```
python scripts/init_db.py
python scripts/load_nist_to_postgres.py
python scripts/load_nist_to_qdrant.py
```

---

## Key Files to Know

```
configs/settings.py          Central config — all env vars with dev defaults
src/api/auth.py              JWT auth — reads JWT_SECRET_KEY directly via os.getenv
src/api/main.py              FastAPI app entry, 4 routers, CORS
src/db/models.py             Full 8-table SQLAlchemy schema
src/agents/ssp_generator.py  Core SSP generation logic — RAG retrieval + LLM call + DB persist
src/evidence/state_machine.py Evidence transitions + hash-chained audit log
src/scoring/sprs.py          SPRS score calculation
docs/production_readiness.md Full status tracker with all known issues
```

---

## Environment / Secrets

`.env` is gitignored. Contains:
- `ANTHROPIC_API_KEY` — **replace placeholder before running SSP generation**
- `JWT_SECRET_KEY=dev-secret-change-in-production` — **replace before any real users**
- `DATABASE_URL=postgresql://cmmc:localdev@localhost:5432/cmmc`
- `QDRANT_URL=http://localhost:6333`
- Full list in `.env.example` (TODO: create this)

`configs/settings.py` calls `load_dotenv()` at import time — all other modules that use
`os.getenv()` will see `.env` values as long as `settings.py` is imported first (it always
is, via `src/db/session.py`).

---

## Known Issues

### Must Fix Before Any Real Users
1. **`JWT_SECRET_KEY`** — placeholder value in `.env`. Generate with `openssl rand -hex 32`
2. **`ANTHROPIC_API_KEY`** — placeholder in `.env`. Set real key before SSP generation
3. **No Dockerfiles** — can't containerize the app yet; `docker/` is empty
4. **In-memory job tracking** — `_jobs` dict in `ssp_routes.py` lost on API restart; wire up `ssp_jobs` DB table

### Important but Not Blocking
5. **SSP regex parser** — `_parse_ssp_output()` in `ssp_generator.py` fails on unexpected LLM formatting; switch to structured output
6. **Dashboard hardcoded org_id** — `dashboard.py` always shows Apex Defense data; needs JWT session
7. **No Alembic** — schema migrations are manual `scripts/add_*.py` files; set up Alembic before schema evolves further
8. **No rate limiting** — any endpoint can be hammered; add `slowapi` or similar
9. **Temporal worker manual start** — worker must be started separately; no supervisor or auto-restart

### Minor
10. `CA.L2-3.12.4` (SSP control) POA&M exclusion is hardcoded string match in `poam.py` — fine for now
11. Manifest generation in `hasher.py` hardcodes org name in some paths
12. No `.env.example` file for new developer onboarding

---

## SPRS Scoring Rules (Quick Reference)

- Start at **110** (all controls met)
- Subtract each control's weight (1, 3, or 5 pts) for NOT MET or NOT ASSESSED
- Partial + active POA&M → treated as MET (no deduction)
- Floor: **-203**
- POA&M eligibility threshold: score **≥ 88**
- `CA.L2-3.12.4` (System Security Plan) **cannot** be on a POA&M
- 5-point controls = CRITICAL severity gaps

---

## Evidence State Machine (Quick Reference)

```
DRAFT → REVIEWED → APPROVED → PUBLISHED  (terminal, immutable)
              ↑         |
              └─────────┘  (can revert APPROVED → REVIEWED, or REVIEWED → DRAFT)
```

PUBLISHED: SHA-256 hash locked. File immutable. Hash recorded in audit log.
Every transition writes a hash-chained entry to `audit_log` (SHA-256, GENESIS seed).
Never update `evidence_artifacts.state` directly — always use `transition_evidence()`.

---

## Next Priorities

### Session: Infrastructure (do next)
- [ ] Write `docker/Dockerfile.api` and `docker/Dockerfile.dashboard`
- [ ] Write `docker/Dockerfile.worker` for Temporal worker
- [ ] Add `.env.example` with all keys documented

### Session: Stability
- [ ] Wire `ssp_jobs` table into `ssp_routes.py` (replace `_jobs` dict)
- [ ] Harden SSP parser: use Claude structured output or XML tags instead of regex
- [ ] Add `slowapi` rate limiting to sensitive endpoints (auth, SSP generation)

### Session: Dashboard Polish
- [ ] Remove hardcoded `org_id` from `dashboard.py`, use JWT session cookie
- [ ] Add SSP generation progress polling (replace "run this command" message)
- [ ] Handle DB connection failure gracefully (currently silently crashes)

### Session: Migrations
- [ ] Initialize Alembic: `alembic init alembic`
- [ ] Generate baseline migration from current schema
- [ ] Replace `scripts/add_*.py` pattern going forward

### Post-MVP
- [ ] Multi-tenant org provisioning
- [ ] POA&M status update API + UI
- [ ] SPRS score history (store snapshot per calculation)
- [ ] Assessor portal (read-only, scoped to one org)
- [ ] Continuous monitoring hooks (re-score when evidence state changes)

---

## Running Tests

```bash
pytest tests/ -k "not integration"   # 64 unit tests, no live services
pytest tests/ -m integration         # live DB smoke tests (requires postgres)
```

All 64 unit tests mock live services (DB, Qdrant, LLM). Integration tests need
`docker-compose up -d` first.

---

## Coding Conventions (important)

- Raw SQL via `sqlalchemy.text()` for performance-critical DB paths — not ORM
- All DB sessions via `get_session()` context manager or `get_db()` FastAPI dependency
- IDs are short 20-char hex strings generated at insert time (`new_id()` in `models.py`)
- `EVD-` prefix on evidence artifact IDs, `poam-` prefix on POA&M IDs
- **Never** update `evidence_artifacts.state` directly — use `transition_evidence()`
- **Never** bypass `_compute_entry_hash()` in the audit log chain
- Audit log is append-only — never delete or update rows in `audit_log`
