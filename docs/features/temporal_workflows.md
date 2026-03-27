# Feature: Temporal Workflows
## Durable SSP Generation via Temporal

---

## Why Temporal?

Generating SSPs for all 110 NIST 800-171 controls requires ~110 LLM API calls.
At 15–30 seconds each, that's 30–55 minutes total.

**Problem with simple async/BackgroundTasks:**
- If the API process crashes at control 57/110, all progress is lost
- No visibility into which controls succeeded vs failed
- No automatic retry of failed LLM calls
- Can't resume from where it stopped

**Temporal solves this:**
- Checkpoints after each activity (each control generation)
- If worker crashes at control 57, Temporal replays history and resumes at 58
- Automatic retry with exponential backoff on transient failures
- Full workflow visibility in Temporal UI
- Activities can be distributed across multiple workers

---

## Workflow Definition

**File:** `src/workflows/ssp_workflow.py`

### Workflow: `SSPGenerationWorkflow`

```python
@workflow.defn(name="SSPGenerationWorkflow")
class SSPGenerationWorkflow:
    async def run(self, inp: SSPWorkflowInput) -> SSPWorkflowResult:
        # 1. Get control list
        control_ids = await workflow.execute_activity(get_all_control_ids_activity, ...)

        # 2. Generate each control (sequential — respects API rate limits)
        results = []
        for control_id in control_ids:
            result = await workflow.execute_activity(
                generate_ssp_control_activity,
                SSPControlActivityInput(control_id=control_id, org_profile=org_profile),
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3, ...)
            )
            results.append(result)

        # 3. Export Word doc
        docx_path = await workflow.execute_activity(export_ssp_docx_activity, ...)

        return SSPWorkflowResult(...)
```

### Activities

| Activity | What it does | Timeout | Retries |
|---|---|---|---|
| `get_all_control_ids` | Fetch 110 control IDs from Postgres | 30s | 3 |
| `generate_ssp_control` | LLM generation + DB persist for one control | 5min | 3 |
| `export_ssp_docx` | Export completed results to Word doc | 2min | 1 |

### Input/Output Types

```python
@dataclass
class SSPWorkflowInput:
    org_id: str
    org_name: str
    system_name: str
    # ... full org profile
    control_ids: Optional[list] = None   # None = all 110
    export_docx: bool = True

@dataclass
class SSPWorkflowResult:
    org_id: str
    controls_total: int
    controls_succeeded: int
    controls_failed: int
    docx_path: Optional[str]
    statuses: dict   # {"Implemented": 60, "Partially Implemented": 30, ...}
```

---

## Worker Process

**File:** `src/workflows/worker.py`

```python
worker = Worker(
    client,
    task_queue="cmmc-ssp",
    workflows=[SSPGenerationWorkflow],
    activities=[
        generate_ssp_control_activity,
        get_all_control_ids_activity,
        export_ssp_docx_activity,
    ],
)
```

**Start:** `python -m src.workflows.worker`

Must run alongside FastAPI. In production: separate container or process supervisor (supervisord, systemd).

---

## Triggering Workflows

### Via API
```
POST /api/ssp/generate-full-temporal
Body: { "org_profile": {...}, "export_docx": true }
Response: { "job_id": "ssp-org-20260306123456", "status": "running" }
```

### Via CLI
```powershell
python -m src.workflows.trigger_ssp
python -m src.workflows.trigger_ssp --org-id my-org --controls AC.L2-3.1.1 AC.L2-3.1.2
python -m src.workflows.trigger_ssp --no-docx
```

### Monitoring
Temporal UI: http://localhost:8080
- View running workflows
- See which activities completed vs failed
- Inspect retry history
- Manually terminate stuck workflows

---

## Infrastructure

| Service | Purpose |
|---|---|
| `cmmc-temporal` (port 7233) | Temporal server (workflow engine + history storage) |
| `cmmc-temporal-ui` (port 8080) | Web UI for monitoring workflows |
| `cmmc-postgres` | Temporal uses Postgres as its persistence backend |

**docker-compose.yml fix applied:** `DB=postgres12` (was `DB=postgresql`, caused crash).

Temporal connects to the same Postgres instance as the app, using the `cmmc` database.
In production, Temporal should have its own dedicated Postgres instance.

---

## Task Queue: `cmmc-ssp`

All SSP generation work runs on the `cmmc-ssp` task queue. This allows:
- Scaling workers horizontally (run multiple `worker.py` processes)
- Isolating SSP generation from other future workflows (e.g., evidence review workflows)

Future task queues to add:
- `cmmc-evidence` — evidence review approval workflows
- `cmmc-monitoring` — continuous compliance monitoring workflows

---

## Known Gaps / TODO

- [ ] Worker process not automatically started — requires manual `python -m src.workflows.worker`
- [ ] No Dockerfile for the worker process
- [ ] Sequential activity execution — safe for rate limits but slow. Could batch non-dependent controls
- [ ] No progress reporting back to the API — client can't see 45/110 progress via REST
- [ ] Workflow ID collision check — if two jobs start for same org simultaneously, they get different IDs but race on ssp_sections upsert
- [ ] `EvidenceReviewWorkflow` — planned but not implemented (human approval steps in evidence state machine)
- [ ] Temporal should use separate Postgres DB in production (not shared with app)
- [ ] Workflow cancellation endpoint — no way to cancel a running SSP generation from the API
