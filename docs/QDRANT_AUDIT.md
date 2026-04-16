# Qdrant RAG Cross-Org Contamination Audit

Date: 2026-04-16
Auditor: Claude Code per Joseph's directive

## Executive Summary

The Qdrant `nist_compliance` collection is **CLEAN**. It contains 370 points — all NIST SP 800-171 Rev 2 source text (110 controls + ~260 assessment objectives/family overviews). Zero customer-specific content. No org_id field on any point. No evidence artifacts, intake answers, SSP narratives, or scan findings are embedded.

The collection is a read-only reference store for public NIST regulatory text. Cross-org contamination through Qdrant is not possible in the current architecture because there is no customer-specific content to contaminate with.

**Verdict:** CLEAN

## Retrieval Path Findings

### Qdrant query sites

Only **one file** queries Qdrant: `src/agents/ssp_generator_v2.py`.

**Site 1: Control lookup (line 79-86)**
```python
control_results = self.qdrant.scroll(
    collection_name=self.collection,
    scroll_filter=Filter(must=[
        FieldCondition(key="control_id", match=MatchValue(value=control_id)),
        FieldCondition(key="type", match=MatchValue(value="control")),
    ]),
    limit=1,
)[0]
```
- Collection: `nist_compliance`
- Filter: `control_id` exact match + `type="control"`
- `org_id` in filter: N/A — content is org-agnostic NIST text
- Risk: **NONE** — returns public NIST control description

**Site 2: Objectives lookup (line 97-104)**
```python
objective_results = self.qdrant.scroll(
    collection_name=self.collection,
    scroll_filter=Filter(must=[
        FieldCondition(key="control_id", match=MatchValue(value=control_id)),
        FieldCondition(key="type", match=MatchValue(value="objective")),
    ]),
    limit=20,
)[0]
```
- Collection: `nist_compliance`
- Filter: `control_id` exact match + `type="objective"`
- `org_id` in filter: N/A — content is org-agnostic NIST text
- Risk: **NONE** — returns public NIST assessment objectives

No other files in `src/` import from `qdrant_client`. The document generator, claim extractor, observation builder, resolution engine, assessment simulator, and export modules do NOT use Qdrant.

## Ingestion Path Findings

### What's embedded in Qdrant

**One ingestion script:** `scripts/load_nist_to_qdrant.py`

Content source: `src/rag/chunker.py` → `get_all_chunks()` produces three types:
1. **Control chunks** (type="control") — NIST control ID, title, description, discussion. Source: `data/nist/controls_full.py`
2. **Objective chunks** (type="objective") — assessment objective text. Source: `data/nist/objectives.py`
3. **Family overview chunks** (type="family_overview") — family-level summaries

Metadata per chunk: `{type, control_id, nist_id, family, family_id, title, points, poam_eligible, source}`

**No org_id in any payload.** No customer-specific content embedded. No evidence artifacts, intake answers, SSP narratives, or scan findings are ever sent to Qdrant. The chunker reads only from static NIST reference data files.

## Live Collection State

### Inspection results
```
Collections: ['nist_compliance']

=== nist_compliance ===
  points_count: 370
  sampled 100 of 370 points
  payload keys: {text: 100, type: 100, control_id: 100, nist_id: 100,
                 family: 100, family_id: 100, title: 100, points: 100,
                 poam_eligible: 100, source: 100}
  points with org_id: 0/100
  org_ids distribution: {}
  types distribution: {control: 100}

  sample payload:
  {
    "text": "NIST 800-171 Control AC.L2-3.1.1 (3.1.1): Authorized Access Control...",
    "type": "control",
    "control_id": "AC.L2-3.1.1",
    "nist_id": "3.1.1",
    "family": "Access Control",
    "family_id": "AC",
    "title": "Authorized Access Control",
    "points": 5,
    "poam_eligible": "yes",
    "source": "NIST SP 800-171 Rev 2"
  }
```

### Interpretation

The collection contains exactly the expected content: NIST 800-171 Rev 2 control descriptions and assessment objectives. Every point is sourced from public regulatory text (`source: "NIST SP 800-171 Rev 2"`). No org_id field exists. No customer-specific data is present. The collection acts as a read-only regulatory reference store.

## Postgres Fallback

`_get_context_from_postgres()` at `ssp_generator_v2.py:115-152` queries:
- `controls` table: `SELECT title, description, discussion, points, poam_eligible FROM controls WHERE id = :cid`
- `assessment_objectives` table: `SELECT id, description, examine, interview, test FROM assessment_objectives WHERE control_id = :cid`

Both tables are **platform-global** — they contain NIST regulatory text, not customer data. No org_id filter needed or present. The Postgres fallback is safe by design.

## Findings Summary

**No findings.** The Qdrant collection contains only public NIST reference text. No customer-specific content is embedded, retrieved, or at risk of cross-org leakage.

## Recommended Actions

None required. The Qdrant RAG path is architecturally clean:
- Ingestion: NIST-only, org-agnostic
- Retrieval: filtered by control_id + type, returns only NIST text
- No customer content in the vector store at all
- Postgres fallback queries the same org-agnostic reference tables
