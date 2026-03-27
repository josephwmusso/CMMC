# Feature: Evidence Management
## Tamper-Evident Evidence Lifecycle with Hash-Chained Audit Log

---

## What It Does

Manages the complete lifecycle of evidence artifacts that prove CMMC control implementation.
Evidence is uploaded, reviewed, approved, and published — at which point it's SHA-256 hashed
and becomes cryptographically immutable. Every state transition is recorded in a tamper-evident
hash-chained audit log that satisfies DoD audit requirements.

---

## State Machine

```
DRAFT ──────────────────► REVIEWED
  ▲                          │
  │◄─────────────────────────┤
                             ▼
                         APPROVED ──► PUBLISHED (terminal, immutable)
                             ▲
                             │◄──────────────────────────────────
```

| Transition | Action | Who |
|---|---|---|
| DRAFT → REVIEWED | Marks for review | Uploader |
| REVIEWED → DRAFT | Send back with comments | Reviewer |
| REVIEWED → APPROVED | Approves evidence | Approver |
| APPROVED → REVIEWED | Reverts approval | Approver |
| APPROVED → PUBLISHED | Locks with SHA-256 hash | Admin |
| PUBLISHED → * | **Blocked** — immutable | Nobody |

---

## SHA-256 Hashing

At PUBLISHED transition:
1. `hash_file(file_path)` reads file in 8192-byte chunks
2. SHA-256 digest stored in `evidence_artifacts.sha256_hash`
3. Hash recorded in audit log entry details
4. File on disk is not deleted or moved (path stays valid for verification)

Verification: `GET /api/evidence/{id}/verify`
- Re-reads file, recomputes hash, compares to stored value
- Returns `{"valid": true, "status": "INTACT"}` or `{"valid": false, "status": "TAMPERED"}`

---

## Audit Chain

Every transition writes to `audit_log`:

```python
entry = {
    "actor": "alice@apexdefense.com",
    "actor_type": "user",
    "action": "evidence.PUBLISHED",
    "target_type": "evidence_artifact",
    "target_id": "EVD-ABC123456789",
    "details": {"from_state": "APPROVED", "to_state": "PUBLISHED", "sha256_hash": "..."},
    "prev_hash": "<hash of previous entry>",
    "entry_hash": SHA256(all_above_fields)
}
```

Chain verification: `GET /api/evidence/audit/verify`
- Replays all entries in order
- Recomputes each `entry_hash` and checks against stored value
- Returns `{"valid": true, "entries_checked": 47}` or `{"first_broken": 23}`

---

## API Endpoints

### Upload
```
POST /api/evidence/upload
Form fields:
  file: <binary>
  description: "Access control policy document"
  uploaded_by: "alice"
  org_id: "9de53b587b23450b87af"
  source_system: "manual"

Response: {
  "artifact_id": "EVD-ABC123456789",
  "filename": "AC_Policy_v2.pdf",
  "file_size": 245760,
  "state": "draft"
}
```

### State Transition
```
POST /api/evidence/{artifact_id}/transition
Query params:
  new_state: REVIEWED | APPROVED | PUBLISHED
  actor: "alice"
  comment: "Looks good, matches network diagram"
```

### Link to Controls
```
POST /api/evidence/{artifact_id}/link-controls
Body: {
  "control_ids": ["AC.L2-3.1.1", "AC.L2-3.1.2"],
  "objective_ids": ["3.1.1[a]", "3.1.1[b]"]
}
```

### List Artifacts
```
GET /api/evidence/?org_id=...&state=PUBLISHED&limit=100
```

### Hash Manifest (eMASS format)
```
POST /api/evidence/manifest/generate?org_id=...
GET  /api/evidence/manifest/download?org_id=...
```

---

## File Storage

Files stored at: `{EVIDENCE_DIR}/{org_id}/{artifact_id}_{filename}`

Example: `data/evidence/9de53b587b23450b87af/EVD-ABC123456789_AC_Policy_v2.pdf`

**Issue:** `EVIDENCE_DIR` currently has a Windows absolute path default (`D:/cmmc-platform/data/evidence`).
Must be relative or configurable for container deployment.

---

## Hash Manifest Format

eMASS-compatible manifest for C3PAO submission:

```
CMMC EVIDENCE HASH MANIFEST
Organization: Apex Defense Solutions
Generated: 2026-03-06T22:00:00Z
Algorithm: SHA-256
─────────────────────────────────────────────────────
AC_Policy_v2.pdf
  SHA-256: a1b2c3d4e5f6...
  Size: 245760 bytes

Network_Diagram.png
  SHA-256: f6e5d4c3b2a1...
  Size: 1048576 bytes
─────────────────────────────────────────────────────
TOTAL: 2 artifacts
```

---

## Database Schema

**`evidence_artifacts`**
```sql
id              VARCHAR PRIMARY KEY    -- EVD-{12 hex chars}
org_id          VARCHAR NOT NULL
filename        VARCHAR NOT NULL
file_path       VARCHAR NOT NULL
file_size_bytes INTEGER
mime_type       VARCHAR
sha256_hash     VARCHAR(64)           -- Set at PUBLISHED
hash_algorithm  VARCHAR DEFAULT 'SHA-256'
state           evidence_state ENUM   -- DRAFT/REVIEWED/APPROVED/PUBLISHED
evidence_type   VARCHAR
source_system   VARCHAR               -- manual, crowdstrike, m365, etc.
description     TEXT
owner           VARCHAR               -- uploaded_by
reviewed_at     TIMESTAMP
reviewed_by     VARCHAR
approved_at     TIMESTAMP
approved_by     VARCHAR
published_at    TIMESTAMP
metadata_json   JSON
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

**`evidence_control_map`**
```sql
id              VARCHAR PRIMARY KEY
evidence_id     VARCHAR FK → evidence_artifacts
control_id      VARCHAR FK → controls (nullable)
objective_id    VARCHAR FK → assessment_objectives (nullable)
```

---

## Known Gaps / TODO

- [ ] File size limit enforcement (no current limit — could accept 10GB uploads)
- [ ] MIME type validation (currently trusts Content-Type header)
- [ ] Bulk upload (upload multiple files at once)
- [ ] Evidence type tagging (Policy / Procedure / Screenshot / Log / Config / Certificate)
- [ ] Evidence expiry tracking (some evidence has a shelf life, e.g. pentest reports)
- [ ] Orphaned file cleanup (if DB insert fails after file write)
- [ ] S3/Azure Blob integration (files currently local disk only)
- [ ] Manifest hardcodes "Apex Defense Solutions" — must use actual org name
- [ ] Audit chain performance: `_get_prev_hash()` does a full DESC LIMIT 1 scan — needs index on `audit_log.id`
