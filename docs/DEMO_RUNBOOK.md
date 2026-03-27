# CMMC Platform — Demo Runbook
**Version:** 1.0 | **Date:** 2026-03-13 | **Demo org:** Apex Defense Solutions

This runbook walks through a complete demo from cold start to live dashboard.
Follow it in order — each step depends on the previous.

---

## Prerequisites

| Requirement | Check |
|---|---|
| Docker Desktop running | `docker ps` should show 4 containers |
| Python 3.11 venv activated | `.\venv\Scripts\Activate.ps1` |
| `ANTHROPIC_API_KEY` set | `echo $env:ANTHROPIC_API_KEY` |
| PostgreSQL accepting connections | `docker exec cmmc-postgres pg_isready` |
| Qdrant responding | `curl http://localhost:6333/collections` |

---

## Part 1 — Cold Start (first time only)

If the database is empty or you need a clean slate:

```powershell
# 1. Start all infrastructure
docker-compose up -d

# 2. Activate venv
.\venv\Scripts\Activate.ps1

# 3. Initialize database schema (creates all 10 tables)
python scripts/init_db.py

# 4. Seed NIST 800-171 controls (110 controls + 246 objectives)
python scripts/load_nist_to_postgres.py

# 5. Embed controls into Qdrant for RAG
python scripts/load_nist_to_qdrant.py

# 6. Load 26 Apex evidence artifacts
python scripts/load_apex_evidence.py

# 7. Run full SSP generation (ALL 110 controls — costs ~$2-4 API credits, takes ~15 min)
python scripts/generate_ssp.py --org-id 9de53b587b23450b87af

# 8. Generate SPRS score + POA&M items
python scripts/test_scoring.py   # validates everything is working
```

---

## Part 2 — Normal Demo Start (database already populated)

```powershell
# 1. Verify infrastructure is up
docker ps

# 2. Activate venv (if not already active)
.\venv\Scripts\Activate.ps1

# 3. Start FastAPI backend (Terminal 1)
uvicorn src.api.main:app --reload --port 8000

# 4. Start Streamlit dashboard (Terminal 2)
python -m streamlit run src/ui/dashboard.py --server.port 8501

# 5. (Optional) Start Temporal worker for durable SSP jobs (Terminal 3)
python -m src.workflows.worker
```

**URLs:**
- Dashboard: http://localhost:8501
- API docs: http://localhost:8000/docs
- Temporal UI: http://localhost:8080

---

## Part 3 — Demo Reset (between demos)

Resets Apex org to a known clean state without dropping the schema:

```powershell
python scripts/demo_reset.py
```

This script:
1. Deletes all `ssp_sections` for Apex org
2. Deletes all `poam_items` for Apex org
3. Deletes all `evidence_artifacts` + `evidence_control_map` for Apex org
4. Clears Apex audit log entries
5. Re-loads the 26 evidence files (DRAFT state)

After reset, run `scripts/run_demo.py` to re-populate:

```powershell
python scripts/run_demo.py
```

`run_demo.py` steps:
1. Reset Apex org
2. Upload 26 evidence artifacts (DRAFT)
3. Transition evidence through states (DRAFT → REVIEWED → APPROVED → PUBLISHED)
4. Generate SSP for a subset of controls (or full 110)
5. Calculate SPRS score
6. Generate POA&M items

---

## Part 4 — Pre-Demo Health Check

Run before any live demo:

```powershell
# Quick DB sanity check
python -c "
import sys; sys.path.insert(0, '.')
from src.db.session import get_session
from sqlalchemy import text
with get_session() as db:
    controls = db.execute(text('SELECT COUNT(*) FROM controls')).scalar()
    sections = db.execute(text('SELECT COUNT(*) FROM ssp_sections')).scalar()
    artifacts = db.execute(text('SELECT COUNT(*) FROM evidence_artifacts')).scalar()
    poam = db.execute(text('SELECT COUNT(*) FROM poam_items')).scalar()
    print(f'Controls: {controls} (expect 110)')
    print(f'SSP sections: {sections} (expect 110)')
    print(f'Evidence artifacts: {artifacts} (expect 26)')
    print(f'POA&M items: {poam} (expect 37)')
"

# Verify API is running
curl http://localhost:8000/health

# Verify Qdrant has embeddings
curl http://localhost:6333/collections
```

Expected output:
```
Controls: 110
SSP sections: 110
Evidence artifacts: 26
POA&M items: 37
```

---

## Part 5 — Dashboard Demo Sequence

### Page 1: Overview (landing page)

**What to show:**
- SPRS gauge chart — should show score ~68 (amber zone)
- Domain status bar chart — 14 NIST families, color-coded by status
- Stats row: 110 controls, 26 evidence artifacts, 37 POA&M items

**Key talking points:**
> "This is the SPRS score — the number DoD submits to the Supplier Performance Risk System.
> It starts at 110 and drops for gaps. Ours is 68, which means we have work to do.
> The POA&M eligibility threshold is 88 — you need to be above that to even submit a POA&M.
> The gap between 68 and 88 represents our roadmap."

---

### Page 2: Evidence Management

**Artifact List tab:**
- Shows all 26 uploaded artifacts with state badges (green PUBLISHED)
- Use the search bar to filter by filename (e.g., type "Entra")
- Use Domain filter to show only Access Control artifacts (5 files)
- Click any artifact expander to reveal:
  - Inline file viewer (Markdown renders, CSV shows as table, JSON prettified)
  - Linked controls (e.g., Apex_Access_Control_Policy links to AC.L2-3.1.1 through 3.1.12)
  - Download button
  - Audit history (shows DRAFT → REVIEWED → APPROVED → PUBLISHED transitions)

**Key talking points:**
> "Every artifact is hash-locked once published. The SHA-256 is recorded in an append-only
> audit chain — every entry contains the hash of the previous entry. This is the same
> integrity model used in blockchain. A C3PAO assessor can verify we didn't modify
> evidence after the assessment."

**Upload New Evidence tab:**
- Demonstrate file upload (use any PDF/CSV)
- Show it appears in DRAFT state in the Artifact List

**State Transitions tab:**
- Show the DRAFT → REVIEWED workflow
- Point out the state diagram: PUBLISHED is terminal and immutable

---

### Page 3: SSP & POA&M

**SSP tab:**
- Browse through control narratives — filter by family (AC, IA, AU, etc.)
- Open AC.L2-3.1.1 — point out:
  - "Implemented" status badge (green)
  - Specific tool references (Microsoft Entra ID, Conditional Access, Authenticator)
  - Evidence Artifacts table — shows real artifact IDs like `ee842ca1...`
  - Assessment objectives addressed

**Key talking points:**
> "Traditionally, writing one SSP narrative takes a compliance consultant 30-45 minutes.
> We generated all 110 in about 15 minutes. The LLM references actual tools from the
> org profile — it doesn't write generic boilerplate. And it only cites artifacts that
> are actually in the evidence repository, not invented IDs."

**POA&M tab:**
- Show the 37 open POA&M items
- Point out the 180-day remediation timeline
- Show a high-severity item (5-point control)

**Key talking points:**
> "The POA&M is auto-generated from the SSP gaps. Each item maps back to a specific
> control and has a recommended remediation action. This is what the org submits to
> their contracting officer alongside the SSP."

---

### Page 4: SPRS Scoring

- Show the domain breakdown table — 14 families, point values
- Highlight the gap between current score and POA&M eligibility threshold
- Show the remediation priority list — highest-impact controls first

**Key talking points:**
> "SPRS is the number that directly affects your ability to win DoD contracts.
> Below 88, you can't even submit a POA&M. Below 70, you're at serious risk of
> contract termination. Our AI immediately tells you the 5 controls that, if fixed,
> get you above the threshold fastest."

---

### Page 5: Demo Controls

**Audit Log tab:**
- Show the hash-chained audit trail
- Scroll through entries — evidence.created, evidence.transitioned events
- Point out the SHA-256 chain (each entry's hash feeds into the next)

**SSP Single Generate tab:**
- Live-generate a single control narrative
- Pick a control with evidence (e.g., IR.L2-3.6.1)
- Watch it stream in real-time (~10-15 seconds)
- Show that it cites the real Incident Response Plan artifact ID

---

## Part 6 — Troubleshooting

### "ModuleNotFoundError: No module named 'docx'"
The venv is not activated. Run:
```powershell
.\venv\Scripts\Activate.ps1
```

### "relation does not exist" DB errors
The database schema needs to be initialized:
```powershell
python scripts/init_db.py
```

### Dashboard shows empty SPRS gauge
No SSP sections in DB. Run:
```powershell
python scripts/generate_ssp.py --org-id 9de53b587b23450b87af
```
Or use the full demo script:
```powershell
python scripts/run_demo.py
```

### "Connection refused" on Qdrant/Postgres/Temporal
Docker containers not running:
```powershell
docker-compose up -d
docker ps  # verify all 4 containers show Up
```

### SSP generation returns empty narrative / parse error
Check `ANTHROPIC_API_KEY` is set:
```powershell
echo $env:ANTHROPIC_API_KEY
# Should print: sk-ant-...
```

If blank:
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-your-key-here"
```

### Streamlit "Port 8501 already in use"
Another Streamlit is running:
```powershell
# Find and kill existing process
netstat -ano | findstr :8501
taskkill /PID <pid> /F
```

### Audit chain integrity error
Run the repair script:
```powershell
python scripts/fix_audit_chain.py
```

### Evidence artifacts not showing in Artifact List
They may be for a different org. Verify:
```powershell
python -c "
import sys; sys.path.insert(0, '.')
from src.db.session import get_session
from sqlalchemy import text
with get_session() as db:
    rows = db.execute(text('SELECT org_id, COUNT(*) FROM evidence_artifacts GROUP BY org_id')).fetchall()
    for r in rows: print(r)
"
```
Correct org_id is `9de53b587b23450b87af`.

---

## Appendix — Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | (required) | Claude API access |
| `DATABASE_URL` | `postgresql://cmmc:localdev@localhost:5432/cmmc` | PostgreSQL connection |
| `QDRANT_HOST` | `localhost` | Qdrant vector store |
| `TEMPORAL_HOST` | `localhost:7233` | Temporal workflow engine |
| `LLM_PROVIDER` | `anthropic` | `anthropic` or `openai_compatible` (vLLM) |
| `LLM_MODEL` | `claude-sonnet-4-20250514` | Model ID |
| `EVIDENCE_DIR` | `data/evidence` | Evidence file storage root |
| `SSP_EXPORT_DIR` | `data/exports` | Word/ZIP export output |
| `FRONTEND_URL` | `*` | CORS allowed origin |
