"""
src/agents/org_profile.py

Build the org_profile dict from company_profiles for SSP + document generation.
Single source of truth — matches /api/truth/grounding-context pattern.
Used by SSP generator, document generator, and any future generators.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


class CompanyProfileMissing(Exception):
    pass


def build_org_profile(org_id: str, db: Session) -> dict:
    """Build org_profile dict from company_profiles.

    Returns a dict matching the shape format_org_context() expects:
    name, description, employee_count, facilities, cui_types, contracts,
    systems{...}, org_id.

    Raises CompanyProfileMissing if no row exists — caller converts to
    HTTP 400 with "organization must complete onboarding."
    """
    row = db.execute(text("""
        SELECT company_name, identity_provider, email_platform, email_tier,
               edr_product, firewall_product, siem_product, backup_solution,
               training_solution, primary_location, employee_count, cui_types,
               cage_code, uei, has_remote_workers, has_wireless,
               dfars_7012_clause
        FROM company_profiles
        WHERE org_id = :org_id
        ORDER BY updated_at DESC NULLS LAST
        LIMIT 1
    """), {"org_id": org_id}).fetchone()

    if not row:
        raise CompanyProfileMissing(
            f"No company_profiles row for org_id={org_id}. "
            "Organization must complete onboarding first."
        )

    import json as _json
    cui = row.cui_types
    if isinstance(cui, str):
        try:
            cui = _json.loads(cui)
        except Exception:
            cui = [cui] if cui else []
    if not isinstance(cui, list):
        cui = []

    name = row.company_name or "Organization"
    location = row.primary_location or ""
    emp = row.employee_count or 0
    has_dfars = row.dfars_7012_clause if hasattr(row, "dfars_7012_clause") else True

    return {
        "org_id":         org_id,
        "name":           name,
        "company_name":   name,
        "description":    f"{emp}-employee organization in {location}" if location else f"{emp}-employee organization",
        "employee_count": emp,
        "facilities":     f"Single facility in {location}" if location else "Single facility",
        "cui_types":      ", ".join(cui) if cui else "CUI",
        "contracts":      "Contractor operating under DFARS 252.204-7012" if has_dfars else "Government contractor",
        "systems": {
            "identity":            row.identity_provider or "Not specified",
            "email_collaboration": row.email_platform or "Not specified",
            "endpoint_protection": row.edr_product or "Not specified",
            "network_security":    row.firewall_product or "Not specified",
            "siem":                row.siem_product or "No SIEM",
            "network_architecture": "Network segmented per security zones",
            "encryption":          "Encryption per organizational policy",
            "training":            row.training_solution or "No formal training platform",
            "ticketing":           "Internal tracking",
            "physical_security":   "Physical access controls in place",
        },
    }


# Backward-compatible alias
build_ssp_org_profile = build_org_profile
