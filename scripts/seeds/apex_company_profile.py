"""Canonical Apex Defense Solutions company_profiles seed.

Idempotent UPSERT — safe to run on every backend boot. Ensures Apex's
demo org always has a complete company_profiles row so generators never
fall back to hardcoded constants.
"""
import json
import logging

logger = logging.getLogger(__name__)

APEX_ORG_ID = "9de53b587b23450b87af"

APEX_COMPANY_PROFILE = {
    "company_name": "Apex Defense Solutions",
    "identity_provider": "Microsoft Entra ID (Azure AD) with MFA",
    "email_platform": "Microsoft 365 GCC High",
    "email_tier": "GCC High",
    "edr_product": "CrowdStrike Falcon",
    "firewall_product": "Palo Alto Networks",
    "siem_product": "Microsoft Sentinel",
    "backup_solution": "Veeam",
    "training_solution": "KnowBe4",
    "primary_location": "Columbia, MD",
    "employee_count": 45,
    "cui_types": ["Technical data (ITAR)", "Specifications", "Test results"],
    "has_remote_workers": True,
    "has_wireless": True,
    "dfars_7012_clause": True,
    "existing_ssp": False,
    "existing_poam": False,
    "prior_assessment": False,
}


def seed_apex_company_profile(cur) -> None:
    """Idempotently seed Apex's company_profiles row.

    Uses psycopg2 cursor to match render_startup.py's seed pattern.
    ON CONFLICT (org_id) DO UPDATE fills any missing fields.
    """
    import hashlib
    pid = hashlib.sha256(f"profile:{APEX_ORG_ID}".encode()).hexdigest()[:20]
    p = APEX_COMPANY_PROFILE

    cur.execute("""
        INSERT INTO company_profiles
            (id, org_id, company_name, identity_provider, email_platform, email_tier,
             edr_product, firewall_product, siem_product, backup_solution,
             training_solution, primary_location, employee_count, cui_types,
             has_remote_workers, has_wireless, dfars_7012_clause,
             existing_ssp, existing_poam, prior_assessment,
             created_at, updated_at)
        VALUES
            (%s, %s, %s, %s, %s, %s,
             %s, %s, %s, %s,
             %s, %s, %s, %s,
             %s, %s, %s,
             %s, %s, %s,
             NOW(), NOW())
        ON CONFLICT (org_id) DO UPDATE SET
            company_name       = EXCLUDED.company_name,
            identity_provider  = COALESCE(company_profiles.identity_provider, EXCLUDED.identity_provider),
            email_platform     = COALESCE(company_profiles.email_platform, EXCLUDED.email_platform),
            email_tier         = COALESCE(company_profiles.email_tier, EXCLUDED.email_tier),
            edr_product        = COALESCE(company_profiles.edr_product, EXCLUDED.edr_product),
            firewall_product   = COALESCE(company_profiles.firewall_product, EXCLUDED.firewall_product),
            siem_product       = COALESCE(company_profiles.siem_product, EXCLUDED.siem_product),
            backup_solution    = COALESCE(company_profiles.backup_solution, EXCLUDED.backup_solution),
            training_solution  = COALESCE(company_profiles.training_solution, EXCLUDED.training_solution),
            updated_at         = NOW()
    """, (
        pid, APEX_ORG_ID,
        p["company_name"], p["identity_provider"], p["email_platform"], p["email_tier"],
        p["edr_product"], p["firewall_product"], p["siem_product"], p["backup_solution"],
        p["training_solution"], p["primary_location"], p["employee_count"],
        json.dumps(p["cui_types"]),
        p["has_remote_workers"], p["has_wireless"], p["dfars_7012_clause"],
        p["existing_ssp"], p["existing_poam"], p["prior_assessment"],
    ))
    logger.info("Apex company_profiles seeded (idempotent)")
