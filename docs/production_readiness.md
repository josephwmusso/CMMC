# Production Readiness Tracker
## CMMC Compliance Platform

**Status:** MVP — Pre-production
**Last updated:** 2026-03-06

---

## Summary

**Updated after 4-agent critical review (2026-03-06)**

| Category | Blockers | High | Medium |
|---|---|---|---|
| Security | 6 | 3 | 2 |
| Infrastructure | 3 | 2 | 2 |
| Data Integrity | 3 | 4 | 2 |
| SSP Generation | 1 | 3 | 2 |
| API Quality | 0 | 3 | 3 |
| Dashboard UX | 1 | 2 | 3 |
| Observability | 0 | 2 | 2 |

---

---

## NEW FINDINGS FROM CRITICAL REVIEW (subagent audit)

### SEC-NEW-1: org_id Injection — No Server-Side Ownership Verification (CRITICAL)
Users can pass any `org_id` in form/query params. Server never validates the caller owns that org.

**Attack:**
```bash
# Read any org's evidence
curl http://localhost:8000/api/evidence/?org_id=competitor-org-id
# Upload evidence to any org
curl -X POST .../api/evidence/upload -F "org_id=victim-org-id" -F "file=@anything.pdf"
```

**Files:** `evidence_routes.py:41`, `scoring_routes.py:25`, `ssp_routes.py:52`
**Fix:** Extract org_id from JWT token, not from request params. Verify ownership on every query.

---

### SEC-NEW-2: SQL Injection in State Machine (HIGH)
`state_machine.py` builds a dynamic `SET` clause via string join:
```python
set_sql = ", ".join(set_clauses)
db.execute(text(f"UPDATE evidence_artifacts SET {set_sql} WHERE id = :id"), update_fields)
```
`set_clauses` is built from internal logic only (not user input), so current risk is low — but the pattern is dangerous if `new_state` or `actor` are ever interpolated directly.
**Fix:** Parameterize all values. Never f-string into SQL.

---

### SEC-NEW-3: Path Traversal in Evidence Download (HIGH)
`GET /api/ssp/download/{filename}` takes a filename directly from the URL and joins it to `EXPORT_DIR`:
```python
filepath = os.path.join(EXPORT_DIR, filename)
```
If `filename = "../../configs/settings.py"`, the file path escapes the export directory.
**Fix:**
```python
filepath = os.path.join(EXPORT_DIR, os.path.basename(filename))
if not os.path.abspath(filepath).startswith(os.path.abspath(EXPORT_DIR)):
    raise HTTPException(400, "Invalid filename")
```

---

### DATA-NEW-1: File Upload — No Size Limit (HIGH)
`upload_artifact()` does `file_bytes = await file.read()` — entire file loaded into memory.
A 500MB file will OOM the server. No limit anywhere in the codebase.
**Fix:** Add `MAX_EVIDENCE_SIZE_MB = 100` to settings. Reject with HTTP 413 if exceeded.

---

### DATA-NEW-2: MIME Type Spoofing (CRITICAL)
MIME type guessed from filename only (`mimetypes.guess_type("malware.exe.pdf")` → `application/pdf`).
An attacker can upload a disguised executable.
**Fix:** Validate file magic bytes (first 4–8 bytes). Whitelist allowed types. Reject unknown types.

---

### DATA-NEW-3: Race Condition on State Transitions (HIGH)
Two concurrent `APPROVED → PUBLISHED` requests both read `state=APPROVED`, both pass validation,
both update to `PUBLISHED`. No row-level lock.
**Fix:** Use `SELECT ... FOR UPDATE` before reading state. Wrap in serializable transaction.

---

### DATA-NEW-4: Audit Chain Full Table Scan (MEDIUM)
`_get_prev_hash()` runs `SELECT entry_hash FROM audit_log ORDER BY id DESC LIMIT 1` on every
transition. With 10,000 audit entries and no index on `id`, this becomes a full table scan.
**Fix:** Add `CREATE INDEX idx_audit_log_id ON audit_log(id DESC)`.

---

### SSP-NEW-1: No Partial Generation Recovery (CRITICAL)
If SSP generation crashes at control 57/110, there is no way to resume from 57.
The Temporal workflow helps — activities are checkpointed — but the `generate_full_ssp()`
method in `ssp_generator.py` (used by the BackgroundTask path) has no checkpoint logic.
**Fix:** Persist job state to DB. On resume, skip controls that already have SSP sections.

---

### SSP-NEW-2: Regex Parser Fragility (HIGH)
`_parse_ssp_output()` uses regex patterns that fail on:
- Double newlines before section headers
- Extra spaces in header names
- Missing sections (Claude sometimes omits EVIDENCE ARTIFACTS)
- Section greedy-captures to EOF when next section is missing

**Fix:** Validate all required sections are present. Return error (not empty fields) on parse failure.
Log the raw LLM output when parsing fails for debugging.

---

### SSP-NEW-3: No API Cost Estimation or Guard (HIGH)
110 controls × ~$0.02/call = ~$2.20 per full SSP run. No warning shown to users.
No per-org budget limit. A bug or malicious user could trigger hundreds of runs.
**Fix:** Show estimated cost before triggering. Add per-org monthly LLM spend limit in settings.

---

### UX-NEW-1: Dashboard Has No Error Handling (BLOCKING)
If Postgres is down, the dashboard silently crashes or hangs on load.
`load_sprs_data()` is called in the sidebar with no fallback — entire app goes blank.
**Fix:** Wrap all DB calls in `try/except` with `st.error("Database unavailable...")` fallback.

---

### UX-NEW-2: SSP Generation Progress — User Told to Run Terminal Command (HIGH)
The "Generate Full SSP" button shows: *"Run in your terminal: cd D:\cmmc-platform..."*
This is not acceptable for a commercial product. The dashboard never polls the job status endpoint.
**Fix:** Dashboard should call `POST /api/ssp/generate-full`, then poll `GET /api/ssp/status`
every 5s with `st.rerun()`. Show a progress bar and per-control status.

---

## 🔴 BLOCKERS — Cannot ship without these

### SEC-1: No Authentication
**Impact:** Anyone with the URL can generate SSPs, access evidence, view SPRS scores.
This is a platform for defense contractors handling CUI. Zero auth is a showstopper.

**Fix:**
1. Add `python-jose` + `passlib` to venv
2. Create `src/api/auth.py` with:
   - `POST /api/auth/login` → returns JWT
   - `get_current_user` FastAPI dependency
3. Add `Depends(get_current_user)` to all sensitive routes
4. Add `users` table to DB schema

**Files to change:** `src/api/main.py`, all route files, `src/db/models.py`

---

### SEC-2: No Authorization (Org Isolation)
**Impact:** Once auth exists, user from Org A could pass `org_id=org-b-id` and access Org B's data.
Every DB query that accepts `org_id` from the request must verify the caller owns that org.

**Fix:** After auth is in place, add org_id verification:
```python
def verify_org_access(org_id: str, current_user: User):
    if current_user.org_id != org_id and not current_user.is_admin:
        raise HTTPException(403, "Access denied")
```

**Files to change:** All route files, scoring engines (org_id parameter)

---

### SEC-3: No Secrets Management
**Impact:** `ANTHROPIC_API_KEY = "your-key-here"` in source. DB password `localdev` in docker-compose.
If repo is ever pushed to GitHub, secrets are exposed.

**Fix:**
1. Create `.env` file (gitignored) with real values
2. Create `.env.example` with placeholder values (committed)
3. Add `.env` and `venv/` and `data/` to `.gitignore`
4. Replace docker-compose.yml hardcoded passwords with `${VAR}` references

```bash
# .env.example
ANTHROPIC_API_KEY=your-anthropic-api-key-here
POSTGRES_PASSWORD=change-me-in-production
DATABASE_URL=postgresql://cmmc:${POSTGRES_PASSWORD}@localhost:5432/cmmc
EVIDENCE_DIR=./data/evidence
SSP_EXPORT_DIR=./data/exports
```

---

### INFRA-1: No Dockerfile
**Impact:** Platform cannot be containerized or deployed anywhere.
`docker/` directory is completely empty.

**Fix:** Create:
- `docker/Dockerfile.api` — FastAPI app
- `docker/Dockerfile.dashboard` — Streamlit dashboard
- `docker/Dockerfile.worker` — Temporal worker
- `docker-compose.prod.yml` — production compose with all services

```dockerfile
# docker/Dockerfile.api
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### INFRA-2: No requirements.txt
**Impact:** Cannot reproduce the Python environment. No one can onboard or deploy without the venv.

**Fix:**
```powershell
pip freeze > requirements.txt
```

Then trim to direct dependencies only (not all transitive deps) for maintainability.

---

### DATA-1: Hardcoded Windows Paths
**Impact:** `D:/cmmc-platform/data/evidence` appears directly in `storage.py` and `evidence_routes.py`.
Breaks in any Docker container, Linux server, or another developer's machine.

**Files with hardcoded paths:**
- `src/evidence/storage.py:26` — `evidence_dir` default
- `src/api/evidence_routes.py:200` — `output_dir` in manifest generation
- `configs/settings.py:46,57` — `EVIDENCE_DIR`, `SSP_EXPORT_DIR` defaults

**Fix:** Change all defaults to relative paths:
```python
EVIDENCE_DIR = os.getenv("EVIDENCE_DIR", "data/evidence")
SSP_EXPORT_DIR = os.getenv("SSP_EXPORT_DIR", "data/exports")
```

---

## 🟡 HIGH PRIORITY — Needed before paying customers

### SEC-4: CORS Wide Open
`allow_origins=["*"]` in `src/api/main.py`.

**Fix:**
```python
allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:8501")]
```

---

### SEC-5: No Rate Limiting on LLM Endpoints
`POST /api/ssp/generate` costs money per call. No protection against abuse.

**Fix:** Add `slowapi`:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@router.post("/generate")
@limiter.limit("10/minute")
def generate_single_control(request: Request, ...):
```

---

### DATA-2: In-Memory Job State
`_jobs` dict in `ssp_routes.py` is lost on every API restart.

**Fix:** Create `ssp_jobs` table in Postgres:
```sql
CREATE TABLE ssp_jobs (
    id VARCHAR PRIMARY KEY,
    org_id VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    progress VARCHAR,
    controls_done INTEGER DEFAULT 0,
    controls_total INTEGER DEFAULT 0,
    docx_path VARCHAR,
    error TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

---

### DATA-3: No Database Migrations (Alembic)
Schema is created via raw `scripts/init_db.py`. Any schema change requires manual SQL.
In production, schema changes must be versioned and reversible.

**Fix:**
```powershell
pip install alembic
alembic init alembic
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

---

### DATA-4: No File Size Limit on Evidence Upload
A user could upload a 10GB file. No limit anywhere in the upload endpoint.

**Fix:**
```python
MAX_EVIDENCE_SIZE_MB = 50
if len(file_bytes) > MAX_EVIDENCE_SIZE_MB * 1024 * 1024:
    raise HTTPException(413, f"File exceeds {MAX_EVIDENCE_SIZE_MB}MB limit")
```

---

### DATA-5: Manifest Hardcodes Org Name
`generate_hash_manifest()` in `evidence_routes.py` hardcodes `"Apex Defense Solutions"`.
Every customer will get a manifest with the wrong org name.

**Fix:** Pass `org_name` from the `organizations` table lookup.

---

### INFRA-3: Temporal Worker Manual Start
The worker must be manually started. If it crashes, SSP generation silently fails.

**Fix options:**
- `docker-compose.yml`: add `worker` service that runs `python -m src.workflows.worker`
- Production: supervisord or systemd unit file

---

## 🟢 MEDIUM PRIORITY — Polish before growth

### API-1: No API Versioning
All routes are `/api/*`. When breaking changes are needed, all clients break simultaneously.
**Fix:** Add `/api/v1/` prefix to all routes.

### API-2: No Webhook / Push Notifications
Client must poll `GET /api/ssp/status` to know when generation completes.
**Fix:** Webhook endpoint — POST to caller-provided URL on completion.

### API-3: No POA&M Update Endpoints
POA&M items can be created and read, but not updated or closed via API.
**Fix:** Add `PATCH /api/scoring/poam/{id}` endpoint.

### OBS-1: No Structured Logging
`logging.basicConfig` sends to stdout only. No log aggregation in production.
**Fix:** Add `structlog` or ship logs to Datadog/CloudWatch.

### OBS-2: No Error Tracking
Unhandled exceptions are logged but not tracked. No alerting on LLM failures.
**Fix:** Add Sentry SDK with `sentry_sdk.init()` in `main.py`.

### UX-1: No Empty State Handling
Dashboard shows zeros/errors if org has no data. Needs helpful "Get started" flows.

### UX-2: OVERDUE POA&M Not Auto-Flagged
POA&M items past their deadline don't automatically flip to OVERDUE.
**Fix:** Cron job or Temporal scheduled workflow to check deadlines daily.

---

## Completed ✅

- [x] Temporal container crash fixed (`DB=postgres12`)
- [x] Temporal workflows built (`src/workflows/`)
- [x] 64 unit tests written and passing
- [x] Pydantic deprecation warning fixed (`json_schema_extra`)
- [x] Evidence state machine with hash-chained audit log
- [x] SPRS calculator with full methodology
- [x] Gap assessment engine
- [x] POA&M auto-generator
- [x] SSP generation with RAG + LLM
- [x] Word doc export
- [x] FastAPI with all core routes
- [x] Streamlit dashboard
