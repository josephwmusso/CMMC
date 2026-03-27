# Feature: REST API
## FastAPI Application — All Endpoints

---

## Base URL

Dev: `http://localhost:8000`
Docs: `http://localhost:8000/docs` (Swagger UI)
ReDoc: `http://localhost:8000/redoc`

---

## Health

```
GET /health
Response: { "status": "ok", "version": "0.6.0", "week": 6 }
```

---

## SSP Generation (`/api/ssp/`)

| Method | Path | Description |
|---|---|---|
| POST | `/api/ssp/generate` | Generate SSP for a single control (sync, ~15s) |
| POST | `/api/ssp/generate-full` | Generate all 110 controls (async BackgroundTask) |
| POST | `/api/ssp/generate-full-temporal` | Generate all 110 controls (durable Temporal workflow) |
| GET | `/api/ssp/status` | Poll job status by job_id |
| GET | `/api/ssp/download/{filename}` | Download generated Word doc |

**`POST /api/ssp/generate` request:**
```json
{
  "control_id": "AC.L2-3.1.1",
  "org_profile": {
    "org_name": "Acme Defense",
    "system_name": "Acme Secure Enclave",
    "system_description": "...",
    "employee_count": 50,
    "facility_type": "Single office with server room",
    "tools_description": "- Active Directory\n- CrowdStrike Falcon\n...",
    "network_description": "VLAN-segmented network...",
    "org_id": "my-org-id",
    "use_demo_profile": false
  }
}
```

**`POST /api/ssp/generate-full` request:**
```json
{
  "org_profile": { ... },
  "control_ids": ["AC.L2-3.1.1", "AC.L2-3.1.2"],  // null = all 110
  "export_docx": true
}
```

---

## Evidence Management (`/api/evidence/`)

| Method | Path | Description |
|---|---|---|
| POST | `/api/evidence/upload` | Upload an evidence file (multipart/form-data) |
| GET | `/api/evidence/` | List artifacts for an org |
| GET | `/api/evidence/{artifact_id}` | Get single artifact metadata |
| POST | `/api/evidence/{artifact_id}/transition` | Change artifact state |
| POST | `/api/evidence/{artifact_id}/link-controls` | Link to controls/objectives |
| GET | `/api/evidence/{artifact_id}/verify` | Verify file hash integrity |
| POST | `/api/evidence/manifest/generate` | Generate eMASS hash manifest |
| GET | `/api/evidence/manifest/download` | Download manifest as file |
| GET | `/api/evidence/audit/verify` | Verify audit chain integrity |

**`POST /api/evidence/upload` (multipart):**
```
file: <binary file>
description: "Access control policy"
uploaded_by: "alice"
org_id: "9de53b587b23450b87af"
source_system: "manual"
```

**`POST /api/evidence/{id}/transition`:**
```
Query params:
  new_state: REVIEWED | APPROVED | PUBLISHED
  actor: "alice"
  comment: "Approved — matches implementation"
```

**`POST /api/evidence/{id}/link-controls`:**
```json
{
  "control_ids": ["AC.L2-3.1.1", "AC.L2-3.1.2"],
  "objective_ids": ["3.1.1[a]", "3.1.1[b]"]
}
```

---

## Scoring (`/api/scoring/`)

| Method | Path | Description |
|---|---|---|
| GET | `/api/scoring/sprs` | Full SPRS score with family breakdown |
| GET | `/api/scoring/gaps` | Full gap assessment |
| GET | `/api/scoring/gaps/critical` | Critical gaps only (5-point controls) |
| POST | `/api/scoring/poam/generate` | Auto-generate POA&M items |
| GET | `/api/scoring/poam` | Current POA&M status |
| GET | `/api/scoring/overview` | Combined SPRS + gaps + POA&M (for dashboard) |

All scoring endpoints accept `?org_id=...` query param.

---

## Request/Response Conventions

**Org ID:** All endpoints default to the demo org (`9de53b587b23450b87af`). Pass `org_id`
explicitly for real orgs.

**Error responses:**
```json
{ "detail": "Artifact EVD-ABC not found" }   // 404
{ "detail": "Cannot transition from PUBLISHED" }  // 400
{ "detail": "LLM generation failed: ..." }  // 500
```

**Datetime fields:** ISO 8601 strings in all responses.

---

## Auth (Not Yet Implemented)

Currently: **No authentication**. Every endpoint is public.

Planned: JWT Bearer tokens on all routes.

```
POST /api/auth/login  → { "access_token": "eyJ...", "expires_in": 3600 }

All other endpoints:
Authorization: Bearer eyJ...
```

---

## Rate Limiting (Not Yet Implemented)

`POST /api/ssp/generate` calls the Claude API at ~$0.01-0.05 per control.
Full 110-control run = ~$1-5 in API costs.

Planned: `slowapi` middleware — 10 SSP generation requests per minute per IP.

---

## CORS

Current: `allow_origins=["*"]` — wide open.

Production: Lock to frontend domain only.
```python
allow_origins=["https://app.yourcmmcplatform.com"]
```

---

## Known Gaps / TODO

- [ ] Authentication middleware (JWT)
- [ ] Rate limiting (slowapi)
- [ ] CORS locked to production domain
- [ ] API versioning (`/api/v1/...`)
- [ ] Pagination on list endpoints (currently just `limit` param)
- [ ] Webhook support (notify on SSP generation completion)
- [ ] OpenAPI schema cleanup (remove Pydantic deprecation warnings)
- [ ] Request ID / trace ID in response headers for debugging
