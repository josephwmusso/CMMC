# Known Issues

## CRITICAL: SSP generator reads DEMO_ORG_PROFILE for non-demo orgs

**Severity:** Critical — causes every non-demo customer's SSP to reference
Apex Defense Solutions' tool stack (CrowdStrike, Entra ID, Palo Alto PA-450,
Sentinel, GCC High).

**Root cause:** `OrgProfileInput` (Pydantic model in `src/api/ssp_routes.py`)
lacks a `systems` nested field. When `use_demo_profile=True` (default),
`to_dict()` fills missing keys from `DEMO_ORG_PROFILE`. Pydantic silently
drops unknown fields. The SSP prompt template reads `systems.identity`,
`systems.endpoint_protection`, etc. → every non-Apex org gets Apex tools.

**Fix (preferred):** Option (b) — SSP generator reads `company_profiles`
directly (matching `/api/truth/grounding-context/` pattern). Single source
of truth for tool stack per org.

**Discovered by:** 3A.2b harness, commit `6b7964f`.

**Validation:** Re-run `python -m scripts.simulation.run --fixture meridian_aerospace`
→ `ssp.all_clean` passes (0 FORBIDDEN_TOOL violations).

---

## MEDIUM: Nessus plugin 153953 maps to SI instead of IA

**Severity:** Medium — blocks `resolutions.conflicts_match_fixture.IA_01`.

**Root cause:** Plugin 153953 (legacy IMAP/SMTP auth) has `pluginFamily="Misc."`.
The Nessus parser's `FAMILY_CONTROL_MAP` routes `Misc.` → `SI.L2-3.14.1`.
Semantically this finding belongs on `IA.L2-3.5.3` (authentication policy).

**Fix:** Add keyword override: if synopsis/description contains "legacy auth"
or "IMAP" or "SMTP" → add `IA.L2-3.5.3` to mapped controls.

---

## LOW: Binder ZIP hash varies between runs

**Severity:** Low — expected behavior, not a bug.

PDFs inside the ZIP embed generation timestamps. `submission_fields_hash`
IS deterministic. Documented in Phase 6.3.
