# Data Integrity Audit — 2026-04-16

Purpose: map every location where platform can populate customer-facing output
with data not originating from that customer's input or NIST/CMMC source text.

Commit trail: 048259a (harness baseline) → 3d30a6e (DEMO_ORG_PROFILE fix) → b1c5b68 (kill DEMO_ORG_PROFILE) → c0a1961 (hostname regex) → b97c679 (SC.L2-3.13.11 + compound adjectives).

## Summary

- Total findings: 22
- Critical: 5 (ALL RESOLVED)
- High: 7 (ALL RESOLVED)
- Medium: 6
- Low: 4
- Deferred (UI/tests/scripts-only): 3

## Resolution Status

### CRITICAL — All 5 Resolved
- 1.1: Resolved in b1c5b68 — format_org_context raises on empty, no DEMO_ORG_PROFILE fallback
- 1.2: Resolved in b1c5b68 — DocumentGenerator reads from company_profiles via build_org_profile
- 1.3: Resolved in b1c5b68 — OrgProfileInput.to_dict() no longer fills from DEMO_ORG_PROFILE
- 2.1: Resolved in c0a1961 — SAFE_ACRONYMS + structural hostname detection
- 2.2: Resolved — flag-and-preserve pattern: original narrative stored in original_narrative column,
  gap report shown as default, review_status tracks human review, original retrievable via API
- 4.1: Resolved in b1c5b68 — reset_demo_data preserves company_profiles + boot seed

### HIGH — All 7 Resolved
- 1.4: Resolved in b1c5b68 — SSP export uses build_org_profile(current_user.org_id, db)
- 1.5/3.1: Resolved in this commit — DEFAULTS stubs replaced with "[NOT PROVIDED — complete Module 0]"
- 1.6: Resolved in this commit — scoring_routes reads org name from organizations table
- 1.7: Resolved in this commit — export fallbacks default to "Organization" not "Apex Defense Solutions"
- 2.3: Resolved in this commit — VERSION_PATTERN skips numbers preceded by "L2-" or "800-"
- 4.2: Resolved in b1c5b68 — seed_apex_company_profile wired into render_startup.py boot

## Findings by Commitment

### 1. Seed Data Bleed (9 findings)

#### 1.1 [CRITICAL] DEMO_ORG_PROFILE fallback in format_org_context()
- **File:** `src/agents/ssp_prompts_v2.py:47`
- **Pattern:** `profile = org_profile or DEMO_ORG_PROFILE`
- **Violation:** If org_profile is None or falsy, every SSP prompt receives Apex's full tool stack (Entra ID, CrowdStrike, Palo Alto, Sentinel, KnowBe4, GCC High). This is the function that formats the technology stack section of every SSP narrative.
- **Evidence this is reachable:** Default code path — SSPGeneratorV2.__init__ falls back to DEMO_ORG_PROFILE when no org_profile passed (line 49-50), and format_org_context has its own independent fallback.
- **Recommended fix direction:** Remove fallback. Require org_profile to be non-None. Raise explicit error if missing.
- **Blast radius:** Every non-Apex org's SSP, document, and assessor finding. PARTIALLY FIXED by 3d30a6e for SSP routes, but format_org_context still has independent fallback.

#### 1.2 [CRITICAL] Document generator DEMO_ORG_PROFILE fallback
- **File:** `src/documents/generator.py:273`
- **Pattern:** `self.org_profile = org_profile or DEMO_ORG_PROFILE`
- **Violation:** Document generation (Policy Manual, IR Plan, Training Program, etc.) falls back to Apex profile for non-Apex orgs if org_profile not passed. These documents are customer-signed compliance artifacts.
- **Evidence this is reachable:** Default path when generator instantiated without explicit org_profile.
- **Recommended fix direction:** Same as 1.1 — read from company_profiles via build_ssp_org_profile helper.
- **Blast radius:** All 7 generated document templates for non-Apex orgs.

#### 1.3 [CRITICAL] OrgProfileInput Pydantic defaults hardcode Apex
- **File:** `src/api/ssp_routes.py:93-100`
- **Pattern:**
  ```python
  org_name: str = Field(default="Apex Defense Solutions")
  system_name: str = Field(default="Apex Secure Enclave (ASE)")
  employee_count: int = Field(default=45)
  ```
- **Violation:** Any endpoint that still uses OrgProfileInput (full-SSP job at line 500, temporal path) fills empty fields with Apex values. PARTIALLY FIXED for single-control path by 3d30a6e, but OrgProfileInput class still exists with Apex defaults.
- **Recommended fix direction:** Delete OrgProfileInput class entirely. All callers use build_ssp_org_profile.
- **Blast radius:** Full-SSP background jobs, temporal workflow path.

#### 1.4 [HIGH] SSP export-latest DOCX uses DEMO_ORG_PROFILE
- **File:** `src/api/ssp_routes.py:500-501`
- **Pattern:**
  ```python
  from src.agents.ssp_prompts_v2 import DEMO_ORG_PROFILE
  org_profile = DEMO_ORG_PROFILE
  ```
- **Violation:** The DOCX export endpoint reconstructs SSP from DB but uses Apex profile for the cover page and org context formatting.
- **Recommended fix direction:** Use build_ssp_org_profile(current_user["org_id"], db).
- **Blast radius:** SSP DOCX exports for non-Apex orgs.

#### 1.5 [HIGH] DEFAULTS dict fills stub names into document context
- **File:** `src/documents/intake_context.py:89-108`
- **Pattern:**
  ```python
  "identity_provider": "Identity Provider",
  "edr_tool": "Endpoint Protection Tool",
  "firewall": "Firewall",
  "training_tool": "Security Awareness Training Tool",
  ```
- **Violation:** When a customer hasn't answered an intake question, the document generator receives generic stub strings ("Identity Provider", "Firewall") that render verbatim into SSP narratives and compliance documents. These look like placeholder text in a customer's signed SSP.
- **Recommended fix direction:** Replace stubs with explicit "Not yet provided" or "[MISSING — complete intake Module 0]" markers that are clearly incomplete rather than looking like real tool names.
- **Blast radius:** All document templates for orgs with incomplete intake.

#### 1.6 [HIGH] scoring_routes hardcodes "Apex Defense Solutions" in overview
- **File:** `src/api/scoring_routes.py:171`
- **Pattern:** `"org_name": "Apex Defense Solutions",`
- **Violation:** The /api/scoring/overview endpoint returns a hardcoded org name for all orgs.
- **Recommended fix direction:** Query organizations.name for current_user.org_id.
- **Blast radius:** Overview dashboard org name display for all non-Apex orgs.

#### 1.7 [HIGH] Export fallbacks hardcode "Apex Defense Solutions"
- **Files:**
  - `src/ssp/pdf_export.py:44` — `org_name="Apex Defense Solutions"` default param
  - `src/ssp/pdf_export.py:107` — `org_row[0] if org_row else "Apex Defense Solutions"`
  - `src/ssp/poam_export.py:49` — same pattern
  - `src/ssp/binder_export.py:46` — `org_name="Apex Defense Solutions"` default param
- **Violation:** PDF/DOCX export functions default to "Apex Defense Solutions" when org name lookup fails or is not passed. These are customer-facing downloadable documents.
- **Recommended fix direction:** Raise error instead of defaulting. A nameless export is a bug, not a feature.
- **Blast radius:** POA&M PDF, SSP PDF, Evidence Binder for any org where name lookup fails.

#### 1.8 [MEDIUM] Module 2 help text references Apex by name
- **File:** `src/api/intake_modules/module2_at_au.py:25`
- **Pattern:** `"For Apex Defense (45 employees on Entra ID + M365 GCC High), KnowBe4 delivers..."`
- **Violation:** Intake question help text references Apex's specific tools. This text is returned to ALL orgs via the module endpoint. Not customer-facing output per se, but confusing for non-Apex users.
- **Recommended fix direction:** Genericize to "For a typical 50-employee contractor using [identity provider] and [training platform]..."
- **Blast radius:** Module 2 AT.L2-3.2.1 help text for all orgs.

#### 1.9 [LOW] auth.py DEV_USER dict hardcodes Apex identity
- **File:** `src/api/auth.py:52-60`
- **Pattern:**
  ```python
  DEV_USER = {
      "email": "david.kim@apex-defense.us",
      "org_id": "9de53b587b23450b87af",
  }
  ```
- **Violation:** ALLOW_ANONYMOUS dev bypass uses Apex org_id. Any endpoint called without auth defaults to Apex. Development-only, but can mask org-isolation bugs during testing.
- **Recommended fix direction:** Acceptable for dev. Document that ALLOW_ANONYMOUS must be false in production.
- **Blast radius:** Dev/test only.

### 2. Detector False Positives (4 findings)

#### 2.1 [CRITICAL] HOSTNAME_PATTERN flags "AD", "MFA", "EDR" as fabricated hostnames
- **File:** `src/agents/hallucination_detector.py:92-96`
- **Pattern:**
  ```python
  HOSTNAME_PATTERN = re.compile(
      r'\b(?:SRV|DC|FS|FILE|MAIL|WEB|APP|DB|SQL|AD|DNS|DHCP|CA|PKI|WSUS|SCCM|PRINT)'
      r'[-_]?\d{0,3}\b',
      re.IGNORECASE
  )
  ```
- **Violation:** This regex matches standalone "AD" (Azure AD), "CA" (Certificate Authority or California), "DNS", "DHCP", "PKI" as fabricated hostnames. These are common compliance terms. Any narrative mentioning "AD" or "CA" gets flagged as hallucinated, triggering automatic gap-report conversion.
- **Tokens falsely flagged:** AD, CA, PKI, DNS, DHCP, DB, FS. Also "MFA" if any variant prefix matches.
- **Action on match:** `severity="critical"` → triggers gap-report auto-conversion at `ssp_generator_v2.py:257`.
- **Reversibility:** Silent and irreversible. The original narrative is discarded and replaced with gap-report boilerplate. No log of what the original said.
- **Recommended fix direction:** Require hostname pattern to include hyphen+digit suffix (e.g., `SRV-01`, `DC-02`). Standalone acronyms should never match.
- **Blast radius:** Every SSP narrative mentioning Azure AD, PKI, DNS, DHCP, CA, or database terminology.

#### 2.2 [CRITICAL] Gap-report auto-conversion discards legitimate narrative
- **File:** `src/agents/ssp_generator_v2.py:256-270`
- **Pattern:**
  ```python
  if not verification.passed:
      parsed = self._convert_to_gap_report(...)
      generation_mode = "gap_report_auto"
  ```
- **Violation:** ANY critical finding from the internal detector (including false positives from 2.1) causes the entire generated narrative to be silently replaced with a gap-report template. The LLM's actual output — which may be perfectly accurate — is destroyed. No option to review, override, or recover.
- **Recommended fix direction:** Log the original narrative alongside the gap report. Add an admin override flag. Consider downgrading to "narrative with warnings" instead of full replacement.
- **Blast radius:** Every SSP control where the narrative mentions any false-positive trigger term.

#### 2.3 [HIGH] VERSION_PATTERN flags NIST control IDs as version numbers
- **File:** `src/agents/hallucination_detector.py:99-101`
- **Pattern:** `r'\b[vV]?\d+\.\d+\.\d+(?:\.\d+)?\b'`
- **Violation:** Matches "3.1.1", "3.5.3", "3.13.11" — which are NIST control ID suffixes that legitimately appear in SSP narratives. Flagged as `severity="warning"`, which doesn't trigger gap-report but adds noise.
- **Recommended fix direction:** Exclude patterns matching `\d+\.\d+\.\d+` that are preceded by "L2-" or "800-171".
- **Blast radius:** Warning noise on every narrative that references control IDs by number.

#### 2.4 [MEDIUM] SPECIFIC_DATE_PATTERN flags all dates as suspicious
- **File:** `src/agents/hallucination_detector.py:118-125`
- **Violation:** Every date in a narrative that isn't in the evidence corpus text is flagged. But legitimate dates (assessment date, policy review date, training completion date) come from intake answers, not evidence artifacts. The detector doesn't check intake_responses as a grounding source.
- **Recommended fix direction:** Expand evidence_text_corpus to include intake answer_details and company_profiles data.
- **Blast radius:** Warning noise on dates from intake.

### 3. Fabricated Fallbacks (3 findings)

#### 3.1 [HIGH] intake_context DEFAULTS render as tool names in documents
- **File:** `src/documents/intake_context.py:89-108`
- **Pattern:** Same as 1.5 — `"identity_provider": "Identity Provider"`
- **Violation from Commitment 3 lens:** When these defaults flow into LLM prompts for document generation, the LLM treats "Identity Provider" as the actual tool name and writes SSP prose like "The organization uses Identity Provider for centralized authentication." This is fabricated content — the LLM is inventing plausible-sounding prose around a placeholder string.
- **Recommended fix direction:** Use explicit "[NOT PROVIDED]" marker that the LLM will not prose-ify, or skip the field entirely from the prompt context.
- **Blast radius:** All 7 document templates when intake is incomplete.

#### 3.2 [MEDIUM] ssp_org_profile.py generates description from sparse data
- **File:** `src/agents/ssp_org_profile.py:64-65`
- **Pattern:**
  ```python
  "description": f"{emp}-employee defense subcontractor in {location}"
  ```
- **Violation:** The helper constructs a description string that assumes "defense subcontractor" — which may not be accurate for all customers (could be a software company, testing lab, etc.). This fabricated description enters the SSP prompt.
- **Recommended fix direction:** Use intake answers for industry/description, or leave as "Organization profile" when not provided.
- **Blast radius:** SSP narratives for non-defense-contractor customers (low current risk since all current customers are DIB).

#### 3.3 [LOW] ssp_org_profile.py hardcodes "DoD subcontractor under DFARS 7012 clause"
- **File:** `src/agents/ssp_org_profile.py:69`
- **Pattern:** `"contracts": "DoD subcontractor under DFARS 7012 clause"`
- **Violation:** Assumes all customers have DFARS 7012. True for CMMC platform customers, but still a hardcoded assumption.
- **Recommended fix direction:** Read from company_profiles.dfars_7012_clause field.
- **Blast radius:** Minimal — all CMMC customers do have DFARS 7012.

### 4. Half-Populated Orgs (3 findings)

#### 4.1 [CRITICAL] reset_demo_data deletes company_profiles without re-seeding
- **File:** `scripts/reset_demo_data.py:222-223`
- **Pattern:** `DELETE FROM company_profiles WHERE org_id = :oid`
- **Violation:** After reset, Apex's organizations row exists but company_profiles is gone. Every fallback path that checks company_profiles before DEMO_ORG_PROFILE now hits the empty-profile branch. This is the exact state that caused the 3A.2b harness to find Apex with no company_profiles row.
- **Recommended fix direction:** After DELETE, re-INSERT Apex company_profiles with full tool stack. Or make reset_demo_data re-run the seed.
- **Blast radius:** Apex demo org after any reset. Cascades to SSP generation, document generation, grounding endpoint, scoring overview.

#### 4.2 [HIGH] seed_organization doesn't seed company_profiles
- **File:** `scripts/render_startup.py:796-806`
- **Violation:** `seed_organization` creates the organizations row but NOT the company_profiles row. A fresh Render deployment has Apex org but no company_profiles. Every generator falls back to DEMO_ORG_PROFILE. The fix at 3d30a6e made SSP routes query company_profiles — which will now fail with CompanyProfileMissing on a fresh deployment.
- **Recommended fix direction:** Add a seed_company_profile function called after seed_organization. Or merge into seed_organization.
- **Blast radius:** Fresh Render deployments. Apex SSP generation will 400 with "must complete onboarding."

#### 4.3 [MEDIUM] reset_demo_data.py is not transactional
- **File:** `scripts/reset_demo_data.py:100-235`
- **Violation:** Deletions use individual `_exec_count()` calls with try/except. If the script crashes mid-run (e.g., table doesn't exist), the org is left in a partially-deleted state. Some tables cleared, others not.
- **Recommended fix direction:** Wrap entire delete sequence in a single transaction with rollback on any failure.
- **Blast radius:** Demo org consistency after interrupted resets.

### 5. Cross-Org Contamination (3 findings)

#### 5.1 [MEDIUM] auth.py register fallback assigns to Apex org
- **File:** `src/api/auth.py:306-307`
- **Pattern:** `assigned_org_id = "9de53b587b23450b87af"  # demo org fallback`
- **Violation:** When ALLOW_ANONYMOUS is true and no invite/org_id provided, new users silently join Apex's org. In production (ALLOW_ANONYMOUS=false), this path is unreachable. But in any dev/staging environment with ALLOW_ANONYMOUS=true, random registrations pollute Apex's user list.
- **Recommended fix direction:** Remove fallback. Require invite_code for all registrations when no org_id provided.
- **Blast radius:** Dev/staging only.

#### 5.2 [MEDIUM] audit_log has no org_id column
- **File:** `scripts/render_startup.py` (audit_log DDL)
- **Violation:** The audit_log table is global — all orgs' audit entries share one table with no org_id filter. The evidence binder export includes the FULL audit log (`SELECT * FROM audit_log ORDER BY id ASC`), meaning Org B's binder contains Org A's audit entries.
- **Recommended fix direction:** Add org_id to audit_log. Filter binder export by org. This is a larger migration.
- **Blast radius:** Evidence binder exports expose cross-org audit entries.

#### 5.3 [LOW] Frontend AppContext hardcodes "Apex Defense Solutions"
- **File:** `D:\CMMC_mm\src\app\context\AppContext.tsx:86`
- **Pattern:** `name: 'Apex Defense Solutions'`
- **Violation:** The default organization state in the frontend React context is Apex. Overwritten on login by the /me endpoint, but briefly visible during loading states or if /me fails.
- **Recommended fix direction:** Default to empty string or "Loading...".
- **Blast radius:** Brief flash of "Apex Defense Solutions" on slow connections for non-Apex orgs.

## Severity Definitions

- **CRITICAL:** actively produces or can produce fabricated customer-facing output in default code path. Jason-blocker.
- **HIGH:** can produce fabricated output in reasonable-but-non-default code path (admin-only, specific flag, edge case). Fix before external customer.
- **MEDIUM:** could produce fabricated output only under unusual conditions; or produces content that's technically accurate but feels "stubby" (placeholder-ish). Fix before production.
- **LOW:** technical debt, code smell, or fabrication risk only under intentional misuse. Fix when convenient.

## Methodology

1. Systematic grep for hardcoded Apex identifiers (DEMO_ORG_PROFILE, "Apex Defense", org_id, tool names)
2. Regex audit of all `re.compile` patterns in `src/agents/` against common compliance term false-positives
3. Audit of every Pydantic model default value in `src/api/`
4. Trace of reset/seed paths for company_profiles population gaps
5. Grep for unscoped DB queries (FROM table without org_id filter)
6. Frontend grep for hardcoded company/tool references

## Known Limitations of This Audit

- Frontend audit limited to specific grep patterns; did not read every component file
- Did not run code — all findings are from static analysis of source
- Regex false-positive analysis was manual: tested specific tokens but may have missed edge cases
- Did not audit third-party dependencies or Qdrant vector store content for data leakage
- Did not audit the Streamlit dashboard (`src/ui/dashboard.py`) beyond grep — it's a legacy interface being replaced by the React frontend
