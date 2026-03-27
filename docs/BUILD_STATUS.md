# CMMC Platform — Build Status
**Date:** 2026-03-13 | **Author:** Claude Code | **Sprint:** Week 8

---

## 1. Database Metrics

| Table | Row Count | Notes |
|---|---|---|
| `organizations` | 1 | Apex Defense Solutions demo org |
| `controls` | 110 | NIST 800-171 Rev 2, all 14 families |
| `assessment_objectives` | 246 | NIST 800-171A objectives |
| `ssp_sections` | 110 | All controls generated, Apex org |
| `evidence_artifacts` | 26 | All PUBLISHED state |
| `evidence_control_map` | 69 | Links across 41 controls |
| `poam_items` | 37 | All OPEN status |
| `audit_log` | 141 | Hash-chained, genesis=GENESIS |
| `frameworks` | 1 | NIST 800-171 Rev 2 |
| `users` | 0 | Auth table exists, not seeded |
| `ssp_jobs` | — | Table not yet in schema (in-memory dict) |

### SSP Section Breakdown (Apex org)
| Status | Count |
|---|---|
| Implemented | 78 |
| Partially Implemented | 32 |
| Not Implemented | 0 |
| Planned | 0 |

### SPRS Score
| Metric | Value |
|---|---|
| Starting score | 110 |
| Partial Implemented deductions | 42 pts |
| **Estimated SPRS score** | **68** |
| POA&M eligible threshold | ≥ 88 |
| POA&M eligibility | Not currently eligible (score < 88) |

> Note: SPRS deductions calculated as sum of `controls.points` where `implementation_status = 'Partially Implemented'`. Full `Not Implemented` would deduct more. Score will improve when Partial controls are fully evidenced and re-assessed.

### Evidence Artifact States
All 26 artifacts: **PUBLISHED** (SHA-256 hashed, immutable)

### Audit Chain
- **141 entries**, genesis `prev_hash = GENESIS`
- Chain integrity: verified (genesis seed confirmed correct)

---

## 2. File Inventory

### Source — `src/` (Python LOC)

| File | Lines | Purpose |
|---|---|---|
| `src/ui/dashboard.py` | 1,779 | Streamlit multi-page dashboard |
| `src/agents/ssp_generator.py` | 585 | RAG + LLM SSP narrative engine |
| `src/db/models.py` | 557 | SQLAlchemy 8-table schema |
| `src/scoring/gap_assessment.py` | 320 | Gap cross-reference engine |
| `src/api/ssp_routes.py` | 290 | SSP generation API endpoints |
| `src/workflows/ssp_workflow.py` | 289 | Temporal durable workflow |
| `src/api/evidence_routes.py` | 307 | Evidence CRUD + state machine API |
| `src/evidence/state_machine.py` | 273 | DRAFT→REVIEWED→APPROVED→PUBLISHED |
| `src/scoring/sprs.py` | 251 | SPRS score calculator |
| `src/scoring/poam.py` | 258 | POA&M auto-generator |
| `src/evidence/storage.py` | 205 | File upload + artifact CRUD |
| `src/api/auth.py` | 198 | JWT auth (built, not wired to routes yet) |
| `src/agents/ssp_prompts.py` | 170 | LLM prompt templates + DEMO_ORG_PROFILE |
| `src/rag/chunker.py` | 160 | NIST control chunker for Qdrant |
| `src/agents/llm_client.py` | 130 | Claude API / vLLM unified client |
| `src/api/main.py` | 43 | FastAPI app entry point |
| `src/db/session.py` | 67 | SessionLocal, get_db, get_session |
| `src/db/models_ssp.py` | 45 | SSPSection model (duplicate — to be merged) |
| `src/ssp/docx_export.py` | 397 | Word document export |
| `src/ssp/binder_export.py` | 300 | Full compliance binder ZIP export |
| `src/rag/embedder.py` | 90 | Sentence-transformer embedding service |
| `src/api/scoring_routes.py` | 77 | SPRS / gap / POA&M API endpoints |
| `src/evidence/hasher.py` | 85 | SHA-256 hashing + manifest generation |
| `src/workflows/trigger_ssp.py` | 79 | Temporal workflow CLI trigger |
| `src/workflows/worker.py` | 62 | Temporal worker process |
| **TOTAL src/** | **~7,200** | |

### Config & Data
| File | Lines | Purpose |
|---|---|---|
| `configs/settings.py` | 62 | All config from env vars with dev defaults |
| `data/nist/controls_full.py` | 1,343 | 110 NIST controls seed data |
| `data/nist/objectives_full.py` | 1,189 | 246 assessment objectives seed data |

### Scripts — `scripts/`
| File | Lines | Purpose |
|---|---|---|
| `scripts/run_demo.py` | 721 | Full end-to-end demo orchestrator |
| `scripts/init_db.py` | 439 | One-time DB schema creation |
| `scripts/test_week8.py` | 390 | Week 8 integration test suite |
| `scripts/generate_ssp.py` | 213 | CLI for SSP generation |
| `scripts/load_apex_evidence.py` | 237 | Bulk-load 26 Apex evidence files |
| `scripts/fix_audit_chain.py` | 233 | Audit chain repair utility |
| `scripts/demo_evidence_flow.py` | 204 | Demo evidence workflow script |
| `scripts/load_nist_to_postgres.py` | 215 | Seeds 110 controls + 246 objectives |
| `scripts/load_nist_to_qdrant.py` | 209 | Embeds controls/objectives into Qdrant |
| `scripts/demo_reset.py` | 147 | Resets demo org to clean state |
| `scripts/test_evidence.py` | 165 | Evidence pipeline smoke tests |

### Tests — `tests/`
| File | Lines | Coverage |
|---|---|---|
| `tests/test_api.py` | 157 | FastAPI endpoints (10 tests) |
| `tests/test_scoring.py` | 225 | SPRS + gap + POA&M (22 tests) |
| `tests/test_state_machine.py` | 196 | Evidence state machine (22 tests) |
| `tests/test_hasher.py` | 115 | SHA-256 hashing pipeline (12 tests) |
| `tests/conftest.py` | 41 | Shared fixtures (mock DB, mock LLM) |

### Evidence Samples — `data/evidence/apex_samples/` (26 files)
```
Access Control (5):   Apex_Access_Control_Policy_v4.2.md
                      Entra_ID_Conditional_Access_Export_20260301.json
                      CyberArk_Privileged_Account_Inventory.csv
                      VPN_GlobalProtect_Config.txt
                      Quarterly_Access_Review_Q1_2026.csv

Audit (3):            Splunk_SIEM_Configuration_Summary.md
                      Audit_Log_Retention_Policy_v2.1.md
                      Windows_Event_Log_GPO_Export.xml

Config Mgmt (3):      Intune_Compliance_Policy_Export.json
                      CIS_Benchmark_Scan_Results_20260301.csv
                      Change_Management_Procedure_v3.0.md

Identity & Auth (2):  Entra_MFA_Enforcement_Report_20260301.csv
                      Password_Policy_GPO_Settings.txt

Incident Response (2): Incident_Response_Plan_v3.1.md
                       Tabletop_Exercise_Report_20260215.md

Media Protection (1): BitLocker_Compliance_Report_All_Endpoints.csv

Physical (2):         Facility_Access_Log_February_2026.csv
                      Physical_Security_Assessment_20260101.md

Risk Assessment (2):  Annual_Risk_Assessment_2026.md
                      Nessus_Vulnerability_Scan_Summary_20260301.csv

Sys/Comms (3):        Network_Diagram_Apex_CUI_Enclave.md
                      Palo_Alto_Firewall_Rules_Export.csv
                      TLS_Certificate_Inventory.csv

Security Assessment(1): POA_M_Tracking_Spreadsheet_Q1_2026.csv

Training (2):         KnowBe4_Security_Training_Completion_20260301.csv
                      CUI_Handling_Training_Roster_2026.csv
```

---

## 3. Test Results

### pytest (unit tests) — `tests/`
```
Command:  ./venv/Scripts/python.exe -m pytest tests/ -v --tb=short
Result:   66/66 PASSED  (2 warnings: unknown pytest.mark.integration)
Time:     10.96s
```

> **Important:** Must run with `./venv/Scripts/python.exe` (not system `python`).
> System Python lacks `python-docx`, causing 10 collection errors. All 66 tests pass in venv.

| Suite | Tests | Result |
|---|---|---|
| `test_api.py` | 10 | PASS |
| `test_scoring.py` | 22 | PASS |
| `test_state_machine.py` | 22 | PASS |
| `test_hasher.py` | 12 | PASS |
| **Total** | **66** | **66/66** |

### test_week8.py (integration) — `scripts/`
```
Command:  python scripts/test_week8.py
Result:   35/35 PASSED, 0 failed
```

| Group | Tests | Result |
|---|---|---|
| SPRS Score Calculation | 3 | PASS |
| Gap Assessment | 4 | PASS |
| POA&M Generation | 4 | PASS |
| Evidence Upload | 3 | PASS |
| Evidence State Machine | 4 | PASS |
| Audit Chain | 4 | PASS |
| SSP Generate (single) | 3 | PASS |
| SSP Persist | 3 | PASS |
| Evidence Manifest | 3 | PASS |
| Evidence Binder Export | 4 | PASS |
| **Total** | **35** | **35/35** |

---

## 4. Known Issues

### Critical (blocks production)
| # | Issue | Location | Fix |
|---|---|---|---|
| 1 | No JWT auth on API routes | `src/api/main.py` | Auth built (`auth.py`), not wired to route dependencies |
| 2 | `ssp_jobs` table doesn't exist | DB schema | Jobs stored in-memory dict in `ssp_routes.py` — lost on restart |
| 3 | No `.env` / secrets management | `configs/settings.py` | API key hardcoded fallback; use `python-dotenv` |
| 4 | No Dockerfile for API or dashboard | `docker/` | Docker dir exists but no Dockerfiles yet |
| 5 | No Alembic migrations | root | Schema changes require `init_db.py` re-run |

### Non-Critical (tech debt)
| # | Issue | Location | Details |
|---|---|---|---|
| 6 | `models_ssp.py` duplicate | `src/db/models_ssp.py` | SSPSection defined here AND in `models.py` — use `extend_existing=True` workaround |
| 7 | CORS wildcard (mitigated) | `src/api/main.py:29` | `allow_origins=[FRONTEND_URL]` — defaults to `*` via env var |
| 8 | Hardcoded Windows path | `scripts/demo_evidence_flow.py:168` | `D:/cmmc-platform/data/exports` |
| 9 | Hardcoded `cd D:/cmmc-platform` | `src/workflows/trigger_ssp.py`, `worker.py` | Docstring only, not functional |
| 10 | `users` table empty | DB | Auth table created but no seed/registration flow |
| 11 | `pytest.ini` missing `integration` mark | `pytest.ini` / `conftest.py` | `PytestUnknownMarkWarning` for `@pytest.mark.integration` |

---

## 5. Docker State

```
NAMES              STATUS        PORTS
cmmc-temporal      Up 17 hours   0.0.0.0:7233->7233/tcp
cmmc-postgres      Up 17 hours   0.0.0.0:5432->5432/tcp
cmmc-temporal-ui   Up 17 hours   0.0.0.0:8080->8080/tcp
cmmc-qdrant        Up 17 hours   0.0.0.0:6333-6334->6333-6334/tcp
```

All 4 infrastructure services running. API and Dashboard run as processes (not containerized yet).

---

## 6. Recent Changes — March 13, 2026

### Evidence & Data
- **`data/evidence/apex_samples/`** — 26 realistic evidence files created across 11 CMMC domains
- **`scripts/load_apex_evidence.py`** — Bulk loader script; loads and links all 26 files, leaves as DRAFT
- **`scripts/run_demo.py`** — Step 2 rewritten to load 26 real apex_samples files from disk
- **`scripts/fix_audit_chain.py`** — Audit chain repair utility (fixed genesis hash = "GENESIS")
- **`scripts/add_frameworks_table.py`** — Ran successfully; `frameworks` table created with 1 row

### SSP Generation
- **`src/agents/ssp_generator.py`** — Real evidence injection: `_fetch_evidence_for_control()` queries `evidence_control_map` and passes real artifact IDs/filenames to the LLM prompt; `db_artifact_refs` field on `SSPControlResult`
- **`src/agents/ssp_prompts.py`** — Rule 6 updated to instruct LLM to use only real artifact IDs, not invent `EV-XXX` style IDs; Unicode corruption fixed (curly `"""` → ASCII `"""`)
- **`src/ssp/docx_export.py`** — Evidence tables in Word export now use 4-column layout with real `db_artifact_refs` (Artifact ID, Filename, Type, SHA-256 first 16 chars)

### Dashboard & UI
- **`src/ui/dashboard.py`** — Full CSS overhaul (professional dark-navy theme); Evidence Artifact List tab with inline file viewers, state badges, linked controls, audit history, download buttons, search/filter; Plotly SPRS gauge fixed (removed unsupported `tickcolor`/`gridcolor` properties)
- **`.streamlit/config.toml`** — Professional dark theme configuration

### Testing
- **`tests/conftest.py`** — Created; shared fixtures for mock DB session and mock LLM client
- **`tests/test_api.py`** — Fixed import issues; all 10 API tests passing (66/66 total)
- **`scripts/test_week8.py`** — Genesis hash fix (was `GENESIS_SEED`, now `GENESIS`); 35/35 passing

---

## 7. Project Completion Estimate

| Area | Status | Notes |
|---|---|---|
| DB Schema | 95% | Missing `ssp_jobs` table, `users` unseeded |
| SSP Generation | 90% | Works end-to-end; Temporal workflow needs vLLM test |
| Evidence Management | 95% | State machine + audit chain fully functional |
| SPRS / Scoring | 85% | Calculator works; needs live re-assessment flow |
| Dashboard UI | 85% | Fully functional; polish items remain |
| API | 70% | Routes work; JWT auth not wired |
| Testing | 90% | 101/101 tests pass; needs integration mark |
| Production Readiness | 30% | See `docs/production_readiness.md` |
