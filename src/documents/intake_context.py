"""
src/documents/intake_context.py

Build the template-context dict consumed by the document generator from
what the org has actually answered in the intake questionnaire.

Pulls from three sources:
  1. company_profiles  — the structured Module 0 output
  2. intake_responses  — every question answered (joined via intake_sessions
                         to resolve the org's active session)
  3. intake_modules registry — the source of truth for question IDs,
                               control IDs, and per-module totals.

Everything is read-only; this module never writes.

No imports from src.documents.generator — the generator will call us, not
the other way around.
"""
from __future__ import annotations

import json
from collections import defaultdict
from typing import Any, Optional

from sqlalchemy import text

from src.api.intake_modules import get_all_modules, get_module
from src.db.session import get_session


# =============================================================================
# Constants
# =============================================================================

# Module 0 question_id -> context field name. Only fields that appear
# directly in intake_responses; company_profiles columns are handled
# separately below.
M0_TO_CONTEXT = {
    "m0_company_name":       "org_name",
    "m0_primary_location":   "org_location",
    "m0_employee_count":     "employee_count",
    "m0_cage_code":          "cage_code",
    "m0_locations":          "physical_locations",
    "m0_cui_flow":           "cui_flow",
    "m0_identity_provider":  "identity_provider",
    "m0_email_platform":     "email_platform",
    "m0_edr":                "edr_tool",
    "m0_firewall":           "firewall",
    "m0_siem":               "siem",
    "m0_training_tool":      "training_tool",
    "m0_existing_docs":      "existing_docs",
}


# Control families → the controls_dict name exposed on the context.
FAMILY_BUCKET = {
    "AC": "ac_controls",
    "AT": "at_controls",
    "AU": "au_controls",
    "CM": "cm_controls",
    "IA": "ia_controls",
    "IR": "ir_controls",
    "MA": "ma_controls",
    "MP": "mp_controls",
    "PE": "pe_controls",
    "PS": "ps_controls",
    "RA": "ra_controls",
    "CA": "ca_controls",
    "SC": "sc_controls",
    "SI": "si_controls",
}


# Template → dependent modules. "Ready" = all deps > 0% answered.
# "Fully ready" = all deps at 100%.
TEMPLATE_MODULE_DEPS: dict[str, list[int]] = {
    "scope_package":    [0],
    "policy_manual":    [0, 1, 5],
    "cm_plan":          [0, 3],
    "ir_plan":          [0, 4],
    "training_program": [0, 2],
    "risk_assessment":  [0, 6],
    "crm":              [0],
}


# Demo-org defaults. Returned when a field hasn't been answered so the
# document generator doesn't crash on missing variables.
DEFAULTS: dict[str, Any] = {
    "org_name":             "Organization Name",
    "org_location":         "Location",
    "employee_count":       0,
    "cage_code":            "",
    "physical_locations":   1,
    "cui_types":            "",
    "cui_flow":             "",
    "identity_provider":    "Identity Provider",
    "email_platform":       "Email Platform",
    "edr_tool":             "Endpoint Protection Tool",
    "firewall":             "Firewall",
    "siem":                 "SIEM",
    "backup_tool":          "Backup Solution",
    "training_tool":        "Security Awareness Training Tool",
    "msp_provider":         None,
    "mfa_scope":            "Not specified",
    "fips_scope":           "Not specified",
    "existing_docs":        "",
}


# =============================================================================
# DB helpers
# =============================================================================

def _get_company_profile(org_id: str, db) -> dict:
    row = db.execute(text("""
        SELECT company_name, cage_code, duns_number, employee_count,
               facility_count, primary_location, cui_types, cui_flow,
               has_remote_workers, has_wireless,
               identity_provider, email_platform, email_tier,
               edr_product, firewall_product, siem_product, backup_solution,
               existing_ssp, existing_poam, prior_assessment, dfars_7012_clause
        FROM company_profiles
        WHERE org_id = :org_id
    """), {"org_id": org_id}).fetchone()

    if not row:
        return {}

    cui_types = row[6]
    if isinstance(cui_types, str):
        try:
            cui_types = json.loads(cui_types) if cui_types else []
        except Exception:
            cui_types = []
    if not isinstance(cui_types, list):
        cui_types = []

    return {
        "company_name":      row[0],
        "cage_code":         row[1],
        "duns_number":       row[2],
        "employee_count":    row[3],
        "facility_count":    row[4],
        "primary_location":  row[5],
        "cui_types":         cui_types,
        "cui_flow":          row[7],
        "has_remote_workers": row[8],
        "has_wireless":      row[9],
        "identity_provider": row[10],
        "email_platform":    row[11],
        "email_tier":        row[12],
        "edr_product":       row[13],
        "firewall_product":  row[14],
        "siem_product":      row[15],
        "backup_solution":   row[16],
        "existing_ssp":      row[17],
        "existing_poam":     row[18],
        "prior_assessment":  row[19],
        "dfars_7012_clause": row[20],
    }


def _get_intake_responses(org_id: str, db) -> dict[str, str]:
    """Return {question_id: answer_value} across ALL sessions for this org,
    with the most recent answer winning on duplicates."""
    rows = db.execute(text("""
        SELECT ir.question_id, ir.answer_value
        FROM intake_responses ir
        JOIN intake_sessions  s ON s.id = ir.session_id
        WHERE s.org_id = :org_id
        ORDER BY ir.answered_at DESC
    """), {"org_id": org_id}).fetchall()

    answers: dict[str, str] = {}
    for qid, val in rows:
        if qid not in answers:  # first hit is most recent
            answers[qid] = val
    return answers


def _get_free_text_narratives(org_id: str, db) -> dict[str, str]:
    """Return {question_id: ssp_narrative_context} for answers saved from
    a free-text classification. Most recent answer wins on duplicates.

    Only returns entries where answer_details.source == 'free_text' and
    the classification produced a non-empty ssp_narrative_context."""
    rows = db.execute(text("""
        SELECT ir.question_id, ir.answer_details
        FROM intake_responses ir
        JOIN intake_sessions  s ON s.id = ir.session_id
        WHERE s.org_id = :org_id
        ORDER BY ir.answered_at DESC
    """), {"org_id": org_id}).fetchall()

    narratives: dict[str, str] = {}
    for qid, details in rows:
        if qid in narratives:
            continue
        if isinstance(details, str):
            try:
                details = json.loads(details) if details else {}
            except Exception:
                continue
        if not isinstance(details, dict):
            continue
        if details.get("source") != "free_text":
            continue
        classification = details.get("classification") or {}
        narrative = classification.get("ssp_narrative_context")
        if narrative:
            narratives[qid] = narrative
    return narratives


# =============================================================================
# Mapping helpers
# =============================================================================

def _map_module0_to_profile(answers: dict, profile: dict, narratives: Optional[dict] = None) -> dict:
    """Merge Module 0 intake answers with company_profiles row into the
    canonical context field names. intake_responses wins over profile
    when both have a value (the response is always at least as fresh).

    When a question has a free-text classification with an
    ``ssp_narrative_context``, that narrative is preferred over the raw
    answer_value for document-generation context — it's richer, more
    specific, and already written in SSP-ready prose."""
    ctx: dict[str, Any] = {}
    narratives = narratives or {}

    # 1. From Module 0 answers (fresher source). Prefer the LLM-generated
    # narrative if one was saved for this question.
    for qid, field in M0_TO_CONTEXT.items():
        if qid in narratives and narratives[qid]:
            ctx[field] = narratives[qid]
        elif qid in answers and answers[qid]:
            ctx[field] = answers[qid]

    # 2. Profile fallbacks — company_profiles carries some things that
    # the intake never asks (backup_solution, CAGE code for some flows).
    if profile:
        if "org_name" not in ctx and profile.get("company_name"):
            ctx["org_name"] = profile["company_name"]
        if "org_location" not in ctx and profile.get("primary_location"):
            ctx["org_location"] = profile["primary_location"]
        if "employee_count" not in ctx and profile.get("employee_count") is not None:
            ctx["employee_count"] = profile["employee_count"]
        if "cage_code" not in ctx and profile.get("cage_code"):
            ctx["cage_code"] = profile["cage_code"]
        if "identity_provider" not in ctx and profile.get("identity_provider"):
            ctx["identity_provider"] = profile["identity_provider"]
        if "email_platform" not in ctx and profile.get("email_platform"):
            ctx["email_platform"] = profile["email_platform"]
        if "edr_tool" not in ctx and profile.get("edr_product"):
            ctx["edr_tool"] = profile["edr_product"]
        if "firewall" not in ctx and profile.get("firewall_product"):
            ctx["firewall"] = profile["firewall_product"]
        if "siem" not in ctx and profile.get("siem_product"):
            ctx["siem"] = profile["siem_product"]
        if profile.get("backup_solution"):
            ctx["backup_tool"] = profile["backup_solution"]
        if "training_tool" not in ctx and profile.get("training_solution"):
            ctx["training_tool"] = profile["training_solution"]
        if profile.get("cui_types"):
            types = profile["cui_types"]
            if isinstance(types, list) and types:
                ctx["cui_types"] = ", ".join(types)
        if profile.get("cui_flow"):
            ctx["cui_flow"] = profile["cui_flow"]
        if profile.get("facility_count") is not None and "physical_locations" not in ctx:
            ctx["physical_locations"] = profile["facility_count"]

    # 3. Coerce employee_count + physical_locations to int where possible
    for key in ("employee_count", "physical_locations"):
        if key in ctx:
            try:
                ctx[key] = int(str(ctx[key]).strip())
            except (ValueError, TypeError):
                pass

    # 4. Flatten cui_types if it's still a list/JSON
    if "cui_types" not in ctx and answers.get("m0_cui_types"):
        ctx["cui_types"] = answers["m0_cui_types"]

    # m0_existing_docs is multi-select stored as text — keep as-is.
    if "existing_docs" in ctx and isinstance(ctx["existing_docs"], list):
        ctx["existing_docs"] = ", ".join(ctx["existing_docs"])

    return ctx


def _map_control_statuses(answers: dict) -> dict[str, dict[str, str]]:
    """Group control-status answers by family via the registry.

    Returns {'ac_controls': {'AC.L2-3.1.1': 'Fully implemented', ...}, ...}.
    Every family bucket is always present (even if empty) so templates
    can render a predictable shape.
    """
    buckets: dict[str, dict[str, str]] = {name: {} for name in FAMILY_BUCKET.values()}

    for mod in get_all_modules():
        if mod.number == 0:
            continue  # Module 0 is company profile, no control statuses
        for q in mod.questions:
            # Only the primary CONTROL_STATUS rows populate the per-family
            # dict — follow-ups (MFA scope, FIPS scope) are picked up
            # separately as named fields.
            if q.tier != "control_status":
                continue
            if not q.control_id:
                continue
            family = q.control_id.split(".", 1)[0]  # "AC.L2-3.1.1" -> "AC"
            bucket_name = FAMILY_BUCKET.get(family)
            if not bucket_name:
                continue
            val = answers.get(q.id)
            if val:
                buckets[bucket_name][q.control_id] = val

    return buckets


def _compute_implementation_summary(controls_by_family: dict[str, dict[str, str]]) -> dict:
    """Count how many controls fall into each implementation state."""
    implemented = 0
    partial = 0
    not_implemented = 0
    planned = 0
    not_applicable = 0

    for bucket in controls_by_family.values():
        for value in bucket.values():
            v = (value or "").strip().lower()
            if v == "fully implemented":
                implemented += 1
            elif v == "partially implemented":
                partial += 1
            elif v == "planned":
                planned += 1
            elif v == "not implemented":
                not_implemented += 1
            elif v == "not applicable":
                not_applicable += 1

    total_answered = implemented + partial + not_implemented + planned + not_applicable

    if total_answered == 0:
        summary = "No control statuses answered yet."
    else:
        summary = (
            f"{implemented} of 110 controls fully implemented, "
            f"{partial} partially implemented, "
            f"{not_implemented} not implemented"
        )
        if planned or not_applicable:
            summary += f" ({planned} planned, {not_applicable} not applicable)"

    return {
        "implemented_count":      implemented,
        "partial_count":          partial,
        "not_implemented_count":  not_implemented,
        "planned_count":          planned,
        "not_applicable_count":   not_applicable,
        "total_answered":         total_answered,
        "implementation_summary": summary,
    }


def _compute_module_completion(answers: dict) -> dict[int, float]:
    """For each registered module, return % of its questions that have an answer."""
    result: dict[int, float] = {}
    for mod in get_all_modules():
        total = mod.question_count
        if total == 0:
            result[mod.number] = 0.0
            continue
        answered = sum(1 for q in mod.questions if answers.get(q.id))
        result[mod.number] = round(100.0 * answered / total, 1)
    return result


def _compute_readiness(module_completion: dict[int, float]) -> dict[str, dict]:
    """For each template: {ready, fully_ready, dependent_modules, module_completion}."""
    out: dict[str, dict] = {}
    for tmpl, deps in TEMPLATE_MODULE_DEPS.items():
        dep_pcts = {d: module_completion.get(d, 0.0) for d in deps}
        # Ready iff every dep has *some* progress (>0%).
        ready = all(pct > 0 for pct in dep_pcts.values()) if deps else True
        fully_ready = all(pct >= 100 for pct in dep_pcts.values()) if deps else True
        out[tmpl] = {
            "ready":              ready,
            "fully_ready":        fully_ready,
            "dependent_modules":  deps,
            "module_completion":  dep_pcts,
        }
    return out


def _apply_defaults(ctx: dict) -> dict:
    """Fill in DEFAULTS for any field not already set. Mutates + returns ctx."""
    for key, default in DEFAULTS.items():
        if ctx.get(key) in (None, ""):
            ctx[key] = default
    return ctx


# =============================================================================
# Public API
# =============================================================================

def _build_context(org_id: str, db) -> dict:
    profile = _get_company_profile(org_id, db)
    answers = _get_intake_responses(org_id, db)
    narratives = _get_free_text_narratives(org_id, db)

    # Module 0 / company profile mapping
    ctx = _map_module0_to_profile(answers, profile, narratives)

    # Per-family control status dicts
    controls = _map_control_statuses(answers)
    ctx.update(controls)

    # Named follow-up answers
    ctx["mfa_scope"]  = answers.get("m3_ia_3.5.3_mfa_scope")  or DEFAULTS["mfa_scope"]
    ctx["fips_scope"] = answers.get("m7_sc_3.13.11_fips_scope") or DEFAULTS["fips_scope"]

    # Implementation summary
    ctx.update(_compute_implementation_summary(controls))

    # Per-module completion
    completion = _compute_module_completion(answers)
    ctx["module_completion"] = completion

    # Template readiness (summary form — compat with old templates_ready flag)
    readiness = _compute_readiness(completion)
    ctx["templates_ready"] = {tmpl: r["ready"] for tmpl, r in readiness.items()}
    ctx["templates_readiness_detail"] = readiness

    # Overall intake percent (average across all registered modules)
    if completion:
        ctx["overall_intake_pct"] = round(sum(completion.values()) / len(completion), 1)
    else:
        ctx["overall_intake_pct"] = 0.0

    # Raw answers for AI prompts that need the full bag
    ctx["raw_answers"] = answers

    return _apply_defaults(ctx)


def get_intake_context(org_id: str, db=None) -> dict:
    """Build the template-context dict for ``org_id``.

    ``db`` is an optional SQLAlchemy session. When omitted a session is
    opened for the duration of the call, so routes and background jobs
    can both use this cleanly.
    """
    if db is not None:
        return _build_context(org_id, db)
    with get_session() as session:
        return _build_context(org_id, session)


def get_template_readiness(org_id: str, db=None) -> dict:
    """Return just the per-template readiness info + overall intake %.

    Lightweight companion to :func:`get_intake_context` for frontend
    polling where the full context is more than needed.
    """
    def _readiness_only(session) -> dict:
        answers = _get_intake_responses(org_id, session)
        completion = _compute_module_completion(answers)
        readiness = _compute_readiness(completion)
        overall = round(sum(completion.values()) / len(completion), 1) if completion else 0.0
        return {
            "templates":          readiness,
            "module_completion":  completion,
            "overall_intake_pct": overall,
        }

    if db is not None:
        return _readiness_only(db)
    with get_session() as session:
        return _readiness_only(session)
