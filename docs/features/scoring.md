# Feature: Compliance Scoring
## SPRS Score, Gap Assessment & POA&M Generation

---

## Overview

Three interconnected engines that tell a contractor exactly where they stand:

1. **SPRS Calculator** — the number they self-report to DoD via PIEE
2. **Gap Assessment Engine** — what's wrong and why
3. **POA&M Generator** — the remediation plan with 180-day deadlines

---

## 1. SPRS Calculator

### Methodology (NIST SP 800-171 DoD Assessment)

```
Start:     110 points (perfect score)
Subtract:  N points for each NOT MET control (N = control's SPRS weight)
Subtract:  N points for each NOT ASSESSED control
Credit:    Partially Implemented + active POA&M = treated as MET (0 deduction)
Floor:     -203 (theoretical minimum if all 5-point controls fail)
POA&M:     Score ≥ 88 required for conditional certification with POA&M items
```

### Control Weights (SPRS points)

Controls are weighted 1, 3, or 5 points based on criticality:
- **5 points** = CRITICAL — Identity & Auth, Incident Response, System Protection
- **3 points** = HIGH — Access Control, Audit, Configuration Management
- **1 point** = MEDIUM — Maintenance, Media Protection, Personnel Security

### Implementation

```python
SPRSCalculator(org_id).calculate() → SPRSResult
SPRSCalculator(org_id).get_score_summary() → dict

SPRSResult fields:
  score: int                    # -203 to 110
  max_score: int = 110
  floor: int = -203
  poam_threshold: int = 88
  poam_eligible: bool           # score >= 88
  met_count: int
  not_met_count: int
  partial_count: int
  not_assessed_count: int
  total_controls: int
  total_deductions: int
  critical_gaps: list[ControlScore]
  families: dict[str, FamilyScore]
```

### API

```
GET /api/scoring/sprs?org_id=...
Response: {
  "score": 82,
  "max_score": 110,
  "percentage": 74.5,
  "met": 85,
  "not_met": 12,
  "partial": 8,
  "not_assessed": 5,
  "total_deductions": 28,
  "poam_eligible": false,
  "critical_gaps": [...],
  "families": { "AC": {...}, "SC": {...}, ... }
}
```

---

## 2. Gap Assessment Engine

### Gap Types

| Type | Condition | Meaning |
|---|---|---|
| `NO_SSP` | No ssp_sections row for this control | Control was never assessed |
| `SSP_NOT_IMPLEMENTED` | implementation_status = "Not Implemented" | Fully non-compliant |
| `SSP_PARTIAL` | Partially Implemented + no active POA&M | Scores as NOT MET |
| `NO_EVIDENCE` | No evidence_artifacts linked | Missing proof for assessors |
| `PARTIAL_EVIDENCE` | Evidence exists but none PUBLISHED | Evidence not finalized |

### Severity

| Points | Severity |
|---|---|
| 5 | CRITICAL |
| 3 | HIGH |
| 1 | MEDIUM |

### Implementation

```python
GapAssessmentEngine(org_id).assess() → GapAssessmentResult
GapAssessmentEngine(org_id).get_summary() → dict

ControlGap fields:
  control_id: str
  family: str
  gap_type: str
  severity: str
  description: str           # Human-readable explanation
  remediation_hint: str      # Actionable next step
  on_poam: bool
  poam_eligible: bool
  evidence_info: EvidenceInfo
```

### API

```
GET /api/scoring/gaps?org_id=...
GET /api/scoring/gaps/critical?org_id=...   # 5-point controls only
```

---

## 3. POA&M Generator

### Rules

1. **Cannot POA&M:** `CA.L2-3.12.4` (System Security Plan itself must exist)
2. **Cannot POA&M:** Controls where `controls.poam_eligible = false`
3. **No duplicates:** Skip if active POA&M (OPEN or IN_PROGRESS) already exists
4. **180-day deadline:** `scheduled_completion = now + timedelta(days=180)`
5. **Risk level:** HIGH (5pt) / MODERATE (3pt) / LOW (1pt)

### Milestone Template (auto-generated)

```
Step 1 (Day 30):  Gap analysis complete
Step 2 (Day 60):  Remediation plan approved
Step 3 (Day 120): Implementation complete
Step 4 (Day 150): Evidence collected and published
Step 5 (Day 180): SSP narrative updated
```

### POA&M Status Enum

`OPEN` → `IN_PROGRESS` → `CLOSED`
                        → `OVERDUE` (set externally when deadline passes)

### Implementation

```python
gen = POAMGenerator(org_id)
created, skipped = gen.generate_from_ssp()   # auto-creates items
summary = gen.get_poam_summary()              # current status
```

### API

```
POST /api/scoring/poam/generate?org_id=...
Response: { "created": 12, "skipped": 3, "summary": {...} }

GET /api/scoring/poam?org_id=...
Response: {
  "total_items": 12,
  "status_counts": {"OPEN": 10, "IN_PROGRESS": 2, "CLOSED": 0, "OVERDUE": 0},
  "total_points_at_risk": 34,
  "items": [...]
}
```

---

## Combined Overview Endpoint

```
GET /api/scoring/overview?org_id=...
Response: {
  "sprs": { ...score summary... },
  "gaps": { ...gap summary... },
  "poam": { ...poam summary... }
}
```

Used by the dashboard to load all scoring data in one call.

---

## Known Gaps / TODO

- [ ] Score recalculation trigger — SPRS should auto-recalculate when SSP is updated
- [ ] OVERDUE status automation — cron job to flip IN_PROGRESS → OVERDUE past deadline
- [ ] POA&M update workflow — currently no endpoint to update milestones or close items
- [ ] Score history — track SPRS score over time (trend graph)
- [ ] Export to PIEE-compatible format — the format DoD PIEE system accepts for self-reporting
- [ ] CA.L2-3.12.4 check is hardcoded — should come from `controls.poam_eligible = false` in DB
- [ ] Score inconsistency warning — if SSP generation is in progress, show "score is partial"
- [ ] Family-level remediation priority — which family to fix first for maximum SPRS improvement
