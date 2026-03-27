# CMMC Platform — Architecture
**Version:** 1.0 | **Date:** 2026-03-13

---

## 1. System Overview

The CMMC Compliance Platform automates NIST 800-171 Rev 2 / CMMC Level 2 compliance work
for small defense contractors. It generates System Security Plans (SSPs) using AI,
manages tamper-evident evidence, calculates SPRS scores, and auto-generates POA&M items.

```
+-----------------------------------------------------------------------+
|                           Client Layer                                |
|  Browser  -> Streamlit Dashboard (port 8501)                          |
|  Dev/CI   -> FastAPI REST API    (port 8000)  /docs for OpenAPI       |
+------------------------------+-----------------------------------------+
                               |
+------------------------------v-----------------------------------------+
|                         Application Layer                              |
|                                                                        |
|   FastAPI (Uvicorn)                  Streamlit                        |
|   +-- /api/ssp/*    SSP gen          +-- Overview (SPRS gauge)        |
|   +-- /api/evidence/* state machine  +-- Evidence Management          |
|   +-- /api/scoring/* SPRS/gaps/poam  +-- SSP & POA&M browser         |
|   +-- /api/auth/*   JWT              +-- SPRS Scoring                 |
|                                      +-- Demo Controls                |
+------------------------------+-----------------------------------------+
                               |
+------------------------------v-----------------------------------------+
|                          Service Layer                                 |
|                                                                        |
|  SSPGenerator        SPRSCalculator       EvidenceStateMachine        |
|  (RAG + LLM)         (gap scoring)        (DRAFT -> PUBLISHED)        |
|                                                                        |
|  GapAssessmentEngine POAMGenerator        AuditChain                  |
|  (cross-reference)   (auto-items)         (SHA-256 chained)           |
+-------+-------------------------------+--------------------------------+
        |                               |
+-------v------+        +---------------v------+    +-------------------+
|  PostgreSQL  |        |       Qdrant         |    |     Temporal      |
|  (port 5432) |        |  (port 6333/6334)    |    |    (port 7233)    |
|  10 tables   |        |  NIST embeddings     |    |  Durable SSP      |
|  audit chain |        |  RAG retrieval       |    |  generation jobs  |
+--------------+        +----------------------+    +--------+----------+
                                                             |
+------------------------------------------------------------v----------+
|                            LLM Layer                                  |
|  Dev:  Claude API (claude-sonnet-4-20250514) via Anthropic SDK        |
|  Prod: vLLM OpenAI-compatible endpoint (sovereign, air-gapped)        |
|        Switch: LLM_PROVIDER=openai_compatible  LLM_BASE_URL=http://.. |
+------------------------------------------------------------------------+
```

---

## 2. Database Schema

10-table PostgreSQL schema. All IDs are short hex strings generated at insert time.

```
organizations
  +-- controls (110 NIST 800-171 Rev 2)
  |     id (e.g. AC.L2-3.1.1)
  |     family, family_abbrev, title, description, discussion
  |     points (SPRS weight), poam_eligible
  |     framework_id -> frameworks
  |
  |   +-- assessment_objectives (246)
  |         id, control_id (FK), description
  |         examine, interview, test (evidence methods)
  |
  +-- ssp_sections (AI-generated narratives, one per control per org)
  |     id, org_id, control_id
  |     implementation_status: Implemented | Partially Implemented
  |                            | Not Implemented | Planned
  |     narrative (text), evidence_refs (JSON array), gaps (JSON array)
  |     state, version, generated_by, created_at, updated_at
  |
  +-- evidence_artifacts (uploaded evidence files)
  |     id (EVD-xxxx), org_id
  |     filename, file_path, file_size_bytes, mime_type
  |     sha256_hash (set when state -> PUBLISHED)
  |     state: DRAFT | REVIEWED | APPROVED | PUBLISHED
  |     evidence_type, description, owner (uploaded_by)
  |     created_at, reviewed_at, approved_at, published_at
  |
  |   +-- evidence_control_map (M2M link)
  |         id (ECM-xxxx), evidence_id (FK), control_id (FK)
  |         objective_id (FK, optional)
  |
  +-- poam_items (auto-generated remediation items)
  |     id (poam-xxxx), org_id, control_id
  |     severity (1-5), status: OPEN | CLOSED
  |     description, remediation_plan
  |     due_date (180 days from creation), created_at
  |
  +-- audit_log (append-only SHA-256 hash chain)
  |     id (serial auto-increment)
  |     actor, actor_type (user | system)
  |     action  (evidence.created | evidence.transitioned |
  |              evidence.published | ssp.generated)
  |     target_type, target_id, details (JSON)
  |     entry_hash (SHA-256 of this entry + prev_hash)
  |     prev_hash  <-- CHAIN LINK to previous entry
  |     created_at
  |
  +-- users  (JWT auth, table exists, unseeded)
        id, email, hashed_password, org_id, role

Also: frameworks (1 row: NIST 800-171 Rev 2)
Note: ssp_jobs table not yet in schema -- stored in-memory in ssp_routes.py
```

---

## 3. SSP Generation Pipeline

```
Trigger: POST /api/ssp/generate  or  python scripts/generate_ssp.py
           |
           v
  SSPGenerator.generate_single_control(control_id, org_profile, db=session)
           |
    Step 1a: Fetch control + objectives from PostgreSQL
      SELECT * FROM controls WHERE id = :control_id
      SELECT * FROM assessment_objectives WHERE control_id = :control_id
           |
    Step 1b: Fetch real linked evidence from DB
      SELECT ea.id, ea.filename, ea.evidence_type, ea.sha256_hash
      FROM evidence_control_map ec
      JOIN evidence_artifacts ea ON ec.evidence_id = ea.id
      WHERE ec.control_id = :control_id
      Returns: (evidence_text_for_prompt, list[artifact_dict])
           |
    Step 2: RAG retrieval from Qdrant
      EmbeddingService.embed(control_id + org_description)
      QdrantClient.search(collection="nist_controls", vector, limit=5)
      Returns: relevant NIST discussion snippets for context
           |
    Step 3: Build LLM prompt
      system: SSP_SYSTEM_PROMPT
        - Role: CMMC Level 2 compliance expert
        - 8 rules including: use real artifact IDs, 150-300 words,
          specific tools, third person, cite assessment objectives
        - Exact output format with section headers
      user: SSP_USER_PROMPT_TEMPLATE filled with:
        - Organization context (name, tools, network, size)
        - Control details (id, title, family, SPRS weight, description)
        - Assessment objectives text
        - === EVIDENCE REPOSITORY ARTIFACTS === (real IDs + filenames)
           |
    Step 4: LLM inference
      ComplianceLLM.generate(system, user, max_tokens=1500)
      Returns structured plain text with section delimiters
           |
    Step 5: Parse -> SSPControlResult
      _parse_ssp_output() regex-extracts each section
      result.status            = implementation status string
      result.narrative         = narrative text (150-300 words)
      result.evidence_artifacts = LLM-parsed artifact strings
      result.db_artifact_refs  = real artifacts dict list (from Step 1b)
      result.gaps              = list of gap strings
           |
    Step 6: Persist to PostgreSQL
      UPSERT ssp_sections
        (org_id, control_id, implementation_status, narrative,
         evidence_refs=[real artifact IDs], gaps=[gap strings])
           |
    Step 7: Export (when generating full SSP)
      export_ssp_to_docx(results, org_profile, output_path)
        -> Word doc with cover page, TOC, per-family sections,
           4-column evidence tables (real artifact IDs + SHA-256),
           gap summary appendix, generation statistics
      binder_export_zip(results, org_profile, output_path)
        -> ZIP binder with SSP, evidence files, POA&M, manifest
```

---

## 4. Evidence Upload and State Machine

```
POST /api/evidence/upload
           |
  upload_evidence(db, org_id, filename, file_bytes, uploaded_by)
    1. artifact_id = "EVD-" + uuid4().hex[:12].upper()
    2. Write file: data/evidence/{org_id}/{artifact_id}_{filename}
    3. Detect MIME type
    4. INSERT INTO evidence_artifacts (state='DRAFT')
    5. Write audit entry: action="evidence.created"
    6. COMMIT

link_evidence_to_controls(artifact_id, control_ids=[...])
  For each control_id:
    INSERT INTO evidence_control_map (ECM-xxxx, evidence_id, control_id)
    ON CONFLICT DO NOTHING

State Machine:

  DRAFT -------> REVIEWED -------> APPROVED -------> PUBLISHED
    ^                 |                                    ^
    |                 v (can revert)                       |
    +-------------> DRAFT                              TERMINAL
                                                    (immutable)

  PUBLISHED transition special steps:
    1. sha256_hash = SHA256(file_bytes).hexdigest()
    2. UPDATE evidence_artifacts SET sha256_hash = hash, published_at = now
    3. File is now hash-locked -- any modification detectable
    4. Audit entry written: action="evidence.published", details={hash}

  Every transition writes audit_log entry:
    entry_hash = SHA256(actor + action + target_id + details + prev_hash)
    prev_hash  = last entry_hash in audit_log
    (First ever entry: prev_hash = "GENESIS")
```

---

## 5. SPRS Scoring Pipeline

```
SPRSCalculator.calculate()
  SELECT ssp_sections ss JOIN controls c ON ss.control_id = c.id
  WHERE ss.org_id = :org_id
  Score = 110
  For each control where implementation_status != 'Implemented':
    Score -= c.points
  Score floor = -203
  Returns: SPRSResult(score, deductions_by_family, total_deductions)

GapAssessmentEngine.assess(org_id)
  Load ssp_sections + controls for org
  For each non-Implemented control:
    severity = CRITICAL  if c.points >= 5
               HIGH      if c.points >= 3
               MEDIUM    if c.points >= 1
               LOW       otherwise
  Returns: list[Gap] sorted by severity desc, points desc

POAMGenerator.generate(org_id)
  Run GapAssessmentEngine.assess()
  For each gap where c.poam_eligible = True:
    UPSERT poam_items:
      id = "poam-" + uuid
      due_date = today + timedelta(days=180)
      status = "OPEN"
      severity = gap.severity
  Returns: list[POAMItem]

Special rule: CA.L2-3.12.4 (System Security Plan itself)
  poam_eligible = False -- CANNOT go on POA&M
  Must be Implemented for CMMC certification
```

---

## 6. Audit Chain

The `audit_log` table is an append-only, SHA-256 hash-chained ledger
(same integrity model as a blockchain without consensus):

```python
# Hash computation (src/evidence/state_machine.py)
def _compute_entry_hash(actor, actor_type, action,
                        target_type, target_id,
                        details, prev_hash):
    payload = (actor + actor_type + action +
               target_type + str(target_id) +
               json.dumps(details, sort_keys=True) +
               prev_hash)
    return hashlib.sha256(payload.encode()).hexdigest()

# Genesis entry
prev_hash = "GENESIS"

# Chain verification
def verify_audit_chain(entries):
    prev = "GENESIS"
    for entry in entries:
        expected = _compute_entry_hash(..., prev_hash=prev)
        if entry.entry_hash != expected:
            return False, entry.id  # tampered
        prev = entry.entry_hash
    return True, None
```

Properties:
- **Append-only:** no updates or deletes
- **Tamper-evident:** modifying any entry invalidates all subsequent hashes
- **Verifiable:** replay from GENESIS to current tip
- **Events logged:** evidence.created, evidence.transitioned,
  evidence.published, ssp.generated

---

## 7. LLM Architecture

`ComplianceLLM` (`src/agents/llm_client.py`) abstracts both providers:

```python
# Development (default)
LLM_PROVIDER = "anthropic"
  uses: anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
  model: claude-sonnet-4-20250514

# Production (sovereign / air-gapped)
LLM_PROVIDER = "openai_compatible"
LLM_BASE_URL = "http://vllm-server:8080/v1"
  uses: openai.OpenAI(base_url=LLM_BASE_URL, api_key="not-needed")
  model: Meta-Llama-3.1-70B-Instruct (or configured model)

# Interface (identical for both providers)
llm = ComplianceLLM()
response: str = llm.generate(
    system_prompt=SSP_SYSTEM_PROMPT,
    user_prompt=formatted_user_prompt,
    max_tokens=1500
)
```

---

## 8. Authentication

JWT authentication is fully implemented in `src/api/auth.py`
but **not yet wired to route `Depends()` calls** (production gap).

```
POST /api/auth/token
  Body: {username, password}
  Returns: {access_token, token_type: "bearer"}

GET /api/auth/me
  Header: Authorization: Bearer <token>
  Returns: {id, email, org_id, role}

JWT payload:
  sub: user_id (hex string)
  org_id: organization UUID
  role: "admin" | "user" | "readonly"
  exp: unix timestamp (default: 8 hours)

Wiring to any route:
  from src.api.auth import get_current_user
  @router.get("/protected")
  async def endpoint(user = Depends(get_current_user)):
      # user.org_id available for row-level security
      ...
```

---

## 9. Temporal Durable Workflow

Used for production-scale 110-control SSP generation with fault tolerance:

```
scripts/trigger_ssp.py
    |
    v
Temporal Server (port 7233, queue: "ssp-generation")
    |
    v
src/workflows/worker.py  (Temporal Worker process)
    |
    v
SSPGenerationWorkflow  (src/workflows/ssp_workflow.py)
    |
    +-- activity: generate_control_narrative(control_id)  [x110]
    |   Each activity is independently retryable with backoff.
    |   If worker crashes, Temporal replays from last checkpoint.
    |
    +-- activity: persist_ssp_section(result)
    |
    +-- activity: export_to_docx(all_results)
    |
    v
Workflow completion event (visible in Temporal UI at port 8080)
```

---

## 10. Deployment

### Current (Development)
```
Windows 10 Host
+-- Docker Desktop
|   +-- cmmc-postgres    PostgreSQL 16    port 5432
|   +-- cmmc-qdrant      Qdrant latest    port 6333/6334
|   +-- cmmc-temporal    Temporal server  port 7233
|   +-- cmmc-temporal-ui Temporal UI      port 8080
|
+-- Python 3.11 venv (processes, not containers)
    +-- uvicorn src.api.main:app --reload --port 8000
    +-- streamlit run src/ui/dashboard.py --port 8501
    +-- python -m src.workflows.worker (optional)
    LLM: Claude API (external, ANTHROPIC_API_KEY required)
```

### Target (Production / Sovereign Deployment)
```
Air-gapped Linux server or GovCloud (IL4/IL5)
+-- Docker Compose (all components containerized)
    +-- cmmc-api         FastAPI    [Dockerfile: TODO]
    +-- cmmc-dashboard   Streamlit  [Dockerfile: TODO]
    +-- cmmc-postgres    PostgreSQL 16
    +-- cmmc-qdrant      Qdrant
    +-- cmmc-temporal    Temporal server
    +-- cmmc-temporal-ui Temporal web UI
    +-- cmmc-vllm        vLLM serving local model (no external API)
    +-- cmmc-nginx       Reverse proxy + TLS termination
    Secrets: HashiCorp Vault or AWS Secrets Manager
    DB migrations: Alembic (not yet configured)
    LLM: sovereign model (Llama-3.1-70B or FIPS-approved equivalent)
```

### Production Gaps (see docs/production_readiness.md)
1. Dockerfiles for API and Dashboard
2. JWT auth wired to all API route dependencies
3. Secrets management (no hardcoded fallback keys)
4. Alembic migration framework replacing init_db.py
5. `ssp_jobs` database table (currently in-memory dict)
6. CORS locked to specific origins (currently allow_origins=["*"])
7. Rate limiting and request input validation
