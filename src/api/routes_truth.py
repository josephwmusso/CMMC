"""
src/api/routes_truth.py

Truth-model debugging/verification endpoints. The grounding-context
endpoint reconstructs the exact input universe the SSP generator saw
for a given control — used by the hallucination detector to distinguish
grounded output from fabrication.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.auth import get_current_user
from src.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/truth", tags=["truth"])


_GENERIC_FIRST_WORDS = {"The", "A", "An", "New", "Global", "National", "International"}


def _extract_company_terms(org_name: str, location: str | None) -> list[str]:
    """Emit only high-signal terms: full name, first word (if distinctive),
    and location fragments. Avoids leaking generic words like 'Defense' or
    'Solutions' that would over-ground the detector."""
    terms: set[str] = set()
    if org_name:
        terms.add(org_name)
        parts = org_name.split()
        if parts and len(parts[0]) >= 4 and parts[0] not in _GENERIC_FIRST_WORDS:
            terms.add(parts[0])
    if location:
        terms.add(location)
        for p in location.split(","):
            p = p.strip()
            if len(p) >= 2:
                terms.add(p)
    return sorted(terms)


def _build_grounding_universe(
    control: dict,
    org_profile: dict,
    evidence: list[dict],
) -> dict:
    """Flatten the three context sources into a single grounding universe.

    Pure function — callable from detector tests without HTTP context.
    """
    tools_raw = org_profile.get("tools", {})
    tools = sorted(set(
        v for v in tools_raw.values()
        if v and isinstance(v, str) and v.lower() not in ("none", "null", "", "no log collection")
    ))

    company_terms = _extract_company_terms(
        org_profile.get("company_name") or "",
        org_profile.get("location"),
    )

    ev_titles = [e.get("filename", "") for e in evidence if e.get("filename")]
    ev_descriptions = " ".join(
        (e.get("description") or "").lower() for e in evidence
    ).strip()

    return {
        "tools":             tools,
        "company_terms":     sorted(company_terms),
        "evidence_titles":   ev_titles,
        "evidence_free_text": ev_descriptions,
    }


@router.get("/grounding-context/{control_id}")
def grounding_context(
    control_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Return the exact input universe the SSP generator sees for this
    control. No audit entry — read-only verification endpoint."""
    org_id = user["org_id"]

    # ── 1. Control text (same path as SSPGeneratorV2.get_control_context) ──
    ctrl_row = db.execute(text("""
        SELECT id, title, description, points, poam_eligible
        FROM controls WHERE id = :cid
    """), {"cid": control_id}).fetchone()
    if not ctrl_row:
        raise HTTPException(404, f"Control {control_id} not found")

    obj_rows = db.execute(text("""
        SELECT id, description FROM assessment_objectives
        WHERE control_id = :cid ORDER BY id
    """), {"cid": control_id}).fetchall()
    objectives = [r.description for r in obj_rows]
    objectives_text = "\n".join(
        f"- {r.id}: {r.description}" for r in obj_rows
    )

    control_data = {
        "title":           ctrl_row.title,
        "description":     ctrl_row.description,
        "objectives":      objectives,
        "objectives_text": objectives_text,
        "sprs_points":     ctrl_row.points,
        "poam_eligible":   ctrl_row.poam_eligible,
    }

    # ── 2. Org profile (from company_profiles, latest by updated_at) ──
    profile_row = db.execute(text("""
        SELECT company_name, cage_code, employee_count, primary_location,
               identity_provider, email_platform, edr_product,
               firewall_product, siem_product, backup_solution,
               training_solution, cui_types
        FROM company_profiles
        WHERE org_id = :o
        ORDER BY updated_at DESC NULLS LAST
        LIMIT 1
    """), {"o": org_id}).fetchone()

    org_name_row = db.execute(text(
        "SELECT name FROM organizations WHERE id = :o"
    ), {"o": org_id}).fetchone()

    if profile_row:
        import json as _json
        cui = profile_row.cui_types
        if isinstance(cui, str):
            try:
                cui = _json.loads(cui)
            except Exception:
                cui = [cui] if cui else []
        if not isinstance(cui, list):
            cui = []

        org_profile = {
            "company_name":  profile_row.company_name or (org_name_row.name if org_name_row else org_id),
            "tools": {
                "identity_provider": profile_row.identity_provider,
                "email_platform":    profile_row.email_platform,
                "edr_product":       profile_row.edr_product,
                "firewall_product":  profile_row.firewall_product,
                "siem_product":      profile_row.siem_product,
                "backup_solution":   profile_row.backup_solution,
                "training_tool":     profile_row.training_solution,
            },
            "location":       profile_row.primary_location,
            "employee_count": profile_row.employee_count,
            "cui_types":      cui,
        }
    else:
        logger.warning("No company_profiles for org %s", org_id)
        org_profile = {
            "company_name":  org_name_row.name if org_name_row else org_id,
            "tools":         {},
            "location":      None,
            "employee_count": None,
            "cui_types":     [],
        }

    # ── 3. Evidence artifacts linked to this control ──
    ev_rows = db.execute(text("""
        SELECT ea.id, ea.filename, ea.evidence_type, ea.description, ea.state
        FROM evidence_artifacts ea
        JOIN evidence_control_map ecm ON ecm.evidence_id = ea.id
        WHERE ea.org_id = :o AND ecm.control_id = :cid
        ORDER BY ea.state DESC, ea.updated_at DESC NULLS LAST
    """), {"o": org_id, "cid": control_id}).fetchall()

    evidence = [
        {
            "artifact_id":   r.id,
            "filename":      r.filename,
            "evidence_type": r.evidence_type,
            "description":   r.description,
            "state":         r.state,
        }
        for r in ev_rows
    ]

    grounding = _build_grounding_universe(control_data, org_profile, evidence)

    return {
        "control_id":         control_id,
        "control":            control_data,
        "org_profile":        org_profile,
        "evidence":           evidence,
        "grounding_universe": grounding,
    }
