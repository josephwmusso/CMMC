# Product Requirements Document
## CMMC Compliance AI Platform

**Version:** 0.6.0
**Status:** MVP — Pre-production
**Owner:** Solo founder
**Last updated:** 2026-03-06

---

## 1. Problem Statement

Small defense contractors (10–200 employees) face an existential threat: CMMC Level 2
certification is required to keep DoD contracts, but the compliance process is brutally
expensive ($50K–$200K+ with a C3PAO assessor) and technically complex.

The two biggest pain points:
1. **Writing the SSP** — 110 NIST 800-171 controls each need a detailed implementation
   narrative. This takes experienced compliance consultants 3–6 months. It's mostly
   structured writing that AI can do in hours.
2. **Evidence management** — Assessors require documented evidence for every control.
   Contractors struggle to collect, organize, and maintain this documentation with audit
   trails that satisfy DoD requirements.

---

## 2. Target Customer

**Primary:** Small defense subcontractors (10–200 employees) with:
- Active DoD contracts or pursuing new ones
- DFARS clause 252.204-7012 in their contracts (requires CMMC)
- In-house IT staff of 1–3 people
- No dedicated compliance team
- Budget: $500–$3,000/month for a compliance tool

**Secondary:** CMMC consultants and MSPs managing compliance for multiple contractors.

---

## 3. Core Features (MVP)

### 3.1 AI SSP Generation
**Priority: P0 — Killer feature**

Generate System Security Plan narratives for all 110 NIST 800-171 Rev 2 controls
using Claude AI + RAG over the NIST control library.

Requirements:
- [ ] Generate a single control narrative on demand (< 30 seconds)
- [ ] Generate all 110 controls as a durable background job
- [ ] Narratives must be C3PAO-acceptable (specific, evidence-referenced, objective-addressed)
- [ ] Output structured data: status, narrative, evidence gaps, objectives addressed
- [ ] Export to Word (.docx) in SSP format
- [ ] Persist generated narratives to DB (upsert on regeneration)
- [ ] Support custom org profile (tools, network, employee count, etc.)

Acceptance criteria:
- A C3PAO consultant reviewing output cannot distinguish AI-generated from human-written narratives
- Each narrative references specific tools, configs, and evidence artifacts
- Gaps and recommendations are actionable and control-specific

### 3.2 Evidence Management
**Priority: P0**

Manage the lifecycle of evidence artifacts that prove control implementation.

Requirements:
- [ ] Upload evidence files (PDF, DOCX, XLSX, PNG, etc.)
- [ ] State machine: DRAFT → REVIEWED → APPROVED → PUBLISHED
- [ ] SHA-256 hash locked at PUBLISHED (tamper-evident, eMASS-compatible)
- [ ] Link evidence to one or more controls and assessment objectives
- [ ] Generate CMMC-format hash manifests for C3PAO submission
- [ ] Verify file integrity (re-hash and compare)
- [ ] Hash-chained audit log for all state transitions (tamper-evident)

Acceptance criteria:
- Published artifacts cannot be modified without detection
- Audit chain verification passes after any sequence of valid transitions
- Manifest format is accepted by eMASS upload

### 3.3 SPRS Score Calculator
**Priority: P0**

Calculate the DoD SPRS score the contractor will self-report to PIEE.

Requirements:
- [ ] Score = 110 minus deductions per NOT MET / NOT ASSESSED control
- [ ] Account for POA&M credits (partially implemented + active POA&M = treated as MET)
- [ ] Floor: -203 (theoretical minimum)
- [ ] POA&M eligibility flag: score ≥ 88
- [ ] Per-family breakdown
- [ ] Critical gap list (5-point controls not implemented)

### 3.4 Gap Assessment Engine
**Priority: P0**

Cross-reference SSP, evidence, and controls to identify compliance gaps.

Requirements:
- [ ] Gap types: NO_SSP, NO_EVIDENCE, PARTIAL_EVIDENCE, SSP_NOT_IMPLEMENTED, SSP_PARTIAL
- [ ] Severity: CRITICAL (5pt), HIGH (3pt), MEDIUM (1pt)
- [ ] Remediation hints per gap
- [ ] POA&M status awareness (gap on POA&M = different remediation path)

### 3.5 POA&M Auto-Generator
**Priority: P1**

Auto-generate Plan of Action & Milestones for non-compliant controls.

Requirements:
- [ ] Create POA&M items for NOT MET and PARTIALLY IMPLEMENTED controls
- [ ] 180-day remediation deadline (CMMC requirement)
- [ ] Block CA.L2-3.12.4 (SSP control cannot be on POA&M)
- [ ] Block non-POA&M-eligible controls
- [ ] Skip controls with existing active POA&M items
- [ ] 5-step milestone template
- [ ] Risk level: HIGH/MODERATE/LOW based on SPRS weight

### 3.6 Dashboard
**Priority: P1**

Streamlit multi-page dashboard for non-technical compliance managers.

Pages:
- [ ] Overview: SPRS gauge, gap summary, evidence stats
- [ ] Evidence Management: upload, state transitions, control linking
- [ ] SSP & POA&M: trigger generation, view narratives, download docs
- [ ] Demo Controls: interactive demo for sales

---

## 4. Features Roadmap (Post-MVP)

### Phase 2 — Authentication & Multi-tenancy
- JWT-based auth with user roles (Admin, Reviewer, Viewer)
- Multi-org support (MSSP use case)
- Org-scoped data isolation

### Phase 3 — Advanced Compliance
- Continuous monitoring: re-assess controls on evidence changes
- CMMC Level 3 support (NIST 800-172 overlays)
- Integration with eMASS for direct submission
- Automated evidence collection from M365, CrowdStrike, etc.

### Phase 4 — Sovereign Deployment
- Air-gapped deployment option (vLLM + local embeddings)
- FedRAMP-ready infrastructure
- IL4/IL5 data handling

### Phase 5 — Assessor Tools
- C3PAO assessor portal (review, annotate, request evidence)
- Assessment workflow with formal findings
- CAP (Corrective Action Plan) tracking

---

## 5. Non-Functional Requirements

### Security
- All evidence data encrypted at rest (AES-256)
- TLS 1.2+ for all transit
- FIPS-validated hash algorithms (SHA-256)
- Tamper-evident audit log (hash chain, GENESIS seed)
- No CUI leaves the system boundary unencrypted

### Compliance
- SHA-256 hash manifests compatible with eMASS upload format
- Audit log entries preserve actor, timestamp, action, and hash chain
- Published evidence is immutable (no modifications after PUBLISHED state)

### Performance
- Single control SSP generation: < 30 seconds
- Full 110-control SSP generation: < 45 minutes (background job)
- SPRS score calculation: < 2 seconds
- Gap assessment: < 5 seconds for 110 controls

### Reliability
- SSP generation is durable via Temporal (survives worker crashes)
- Per-control progress checkpointing (resume from last completed control)
- DB transactions for all state transitions

---

## 6. Out of Scope (MVP)

- Real-time collaboration (multi-user simultaneous editing)
- Mobile app
- Direct PIEE submission integration
- Automated control testing / continuous assessment
- Legal advice or formal compliance certification guarantees
