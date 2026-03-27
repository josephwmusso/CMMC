# Feature: SSP Generation
## AI-Powered System Security Plan Narratives

---

## What It Does

Generates C3PAO-acceptable System Security Plan implementation narratives for all 110
NIST 800-171 Rev 2 controls using Claude AI + RAG over the NIST control library.

This is the core killer feature of the platform. A human compliance consultant takes
3–6 months and $50K+ to write an SSP. This generates one in < 45 minutes.

---

## Architecture

```
Org Profile + Control ID
        │
        ▼
SSPGenerator._retrieve_control_context()
  → QdrantClient.scroll() with exact filter {control_id, type: "control"}
  → Returns: control text, title, family, SPRS weight, POA&M eligibility
  → Also fetches objective chunks {control_id, type: "objective"}
  → Fallback: Postgres query if Qdrant returns nothing
        │
        ▼
SSP_USER_PROMPT_TEMPLATE.format(...)
  → Injects org profile + control text + objectives
        │
        ▼
ComplianceLLM.generate()
  → Claude API (dev) or vLLM (prod)
  → max_tokens=2048, temperature=0.3
  → 3 retries with exponential backoff
        │
        ▼
_parse_ssp_output()
  → Regex parsing of structured output sections:
    - IMPLEMENTATION STATUS
    - IMPLEMENTATION NARRATIVE
    - EVIDENCE ARTIFACTS
    - ASSESSMENT OBJECTIVES ADDRESSED
    - GAPS AND RECOMMENDATIONS
        │
        ▼
_persist_ssp_section()
  → Upsert to ssp_sections table (update if exists, insert if new)
  → Returns SSPControlResult dataclass
```

---

## API Endpoints

### Single Control (Synchronous)
```
POST /api/ssp/generate
Body: {
  "control_id": "AC.L2-3.1.1",
  "org_profile": {
    "org_name": "Acme Defense",
    "system_name": "Acme Secure System",
    "use_demo_profile": false
  }
}
Response: {
  "control_id": "AC.L2-3.1.1",
  "status": "Implemented",
  "narrative": "...",
  "evidence_artifacts": ["AD Policy.pdf"],
  "gaps": [],
  "generation_time_sec": 12.4
}
```

### Full SSP — FastAPI BackgroundTasks (simple)
```
POST /api/ssp/generate-full
Body: { "export_docx": true }
Response: { "job_id": "a1b2c3d4", "status": "pending" }

GET /api/ssp/status?job_id=a1b2c3d4
Response: { "status": "running", "progress": "45/110 — SC.L2-3.13.5" }
```

**Limitation:** Job state is in-memory. Lost if API restarts.

### Full SSP — Temporal (durable)
```
POST /api/ssp/generate-full-temporal
Body: { "export_docx": true }
Response: { "job_id": "ssp-org-20260306123456", "status": "running" }
```

Track at Temporal UI: http://localhost:8080

### Download Word Doc
```
GET /api/ssp/download/{filename}
Response: SSP_Apex_Defense_20260306_123456.docx
```

---

## Org Profile

The org profile provides context for the LLM to write specific narratives:

| Field | Purpose |
|---|---|
| `org_name` | Used in narratives ("Apex Defense configures...") |
| `system_name` | The CUI-handling system name |
| `system_description` | CUI boundary description |
| `employee_count` | Contextualizes control implementation scale |
| `facility_type` | Physical security context |
| `tools_description` | Specific tools (AD, CrowdStrike, Sentinel, etc.) |
| `network_description` | Network topology (VLANs, firewall, VPN) |

**Demo profile:** `DEMO_ORG_PROFILE` in `ssp_prompts.py` — Apex Defense Solutions,
45 employees, full realistic tool stack. Used when `use_demo_profile=true`.

---

## Output Format

The LLM is prompted to return a strictly structured response:

```
---
IMPLEMENTATION STATUS: [Implemented | Partially Implemented | Not Implemented | Planned]

IMPLEMENTATION NARRATIVE:
[150-300 word narrative in third person, naming specific tools and configs]

EVIDENCE ARTIFACTS:
- [EV-XXX] Description of evidence artifact

ASSESSMENT OBJECTIVES ADDRESSED:
- [3.1.1[a]]: Brief statement of how it's met

GAPS AND RECOMMENDATIONS:
- [Gap description or "None identified"]
---
```

---

## Database Persistence

Table: `ssp_sections`

| Column | Type | Notes |
|---|---|---|
| `id` | varchar | Short hex hash |
| `control_id` | varchar | FK to controls |
| `org_id` | varchar | FK to organizations |
| `narrative` | text | Generated narrative |
| `implementation_status` | varchar | Implemented / Partial / Not / Planned |
| `evidence_refs` | json | List of evidence artifact references |
| `gaps` | json | List of gap strings |
| `generated_by` | varchar | "ssp_agent" |
| `version` | int | Increments on regeneration |
| `created_at` | timestamp | |
| `updated_at` | timestamp | |

---

## Word Doc Export

`src/ssp/docx_export.py` — uses `python-docx`.

Structure:
1. Cover page (org name, system name, classification banner)
2. Table of contents placeholder
3. Per-family sections (AC, AT, AU, CM, IA, IR, MA, MP, PE, PS, RA, CA, SC, SI)
4. Per-control narrative with status badge
5. Evidence reference tables
6. Gap summary appendix

Output: `data/exports/SSP_{org_name}_{timestamp}.docx`

---

## Temporal Workflow

For durable generation of all 110 controls:

```python
SSPGenerationWorkflow
  activities:
    - get_all_control_ids_activity    # fetch from Postgres
    - generate_ssp_control_activity   # one per control (LLM + persist)
    - export_ssp_docx_activity        # Word doc export

Task queue: "cmmc-ssp"
Retry policy: max 3 attempts, 5s initial, 2x backoff
Timeout per control: 5 minutes
```

Start worker: `python -m src.workflows.worker`
Trigger: `python -m src.workflows.trigger_ssp`
Or via API: `POST /api/ssp/generate-full-temporal`

---

## Known Gaps / TODO

- [ ] Cost estimation before triggering full generation (warn user: ~$X in API costs)
- [ ] Parallel generation for independent controls (currently sequential for rate limit safety)
- [ ] Resume from partial completion (if org already has 60/110 controls, skip them)
- [ ] Quality scoring: confidence score per narrative
- [ ] Regeneration of single control without overwriting others
- [ ] Control family filtering (generate only AC family, etc.)
- [ ] Version history: view previous versions of a narrative
