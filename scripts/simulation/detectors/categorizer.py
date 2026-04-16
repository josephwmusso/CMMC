"""Categorize extracted entities as safe vocabulary, potential hallucination,
or ambiguous."""
from __future__ import annotations

from scripts.simulation.detectors.entity_extractor import Entity

SAFE_VOCAB = {
    # NIST / CMMC terminology
    "nist", "cmmc", "800-171", "800-171a", "800-53", "800-172",
    "c3pao", "dibcac", "dib", "sprs", "poa&m", "poam", "ssp",
    "cui", "cti", "cdi", "fips", "fedramp", "dfars", "itar", "ear",
    "nist sp", "nist 800-171", "nist 800-53",
    # Platform
    "intranest", "anthropic", "claude",
    # Standards bodies
    "dod", "department of defense", "nsa", "cisa",
    # Generic roles
    "system administrator", "information system security manager",
    "senior official", "affirming official", "issm", "isso",
    # Common process terms
    "access control", "audit", "incident response", "risk assessment",
    "configuration management", "identification", "authentication",
    "media protection", "physical protection", "personnel security",
    "system protection", "information integrity",
    # Regulatory
    "32 cfr 170", "252.204-7012", "emass", "piee",
}

# Lowercase set for fast lookup
_SAFE_LOWER = {s.lower() for s in SAFE_VOCAB}


def categorize(entity: Entity) -> str:
    """Return SAFE_VOCAB | POTENTIAL_HALLUCINATION | AMBIGUOUS."""
    canon = entity.canonical.lower()

    if canon in _SAFE_LOWER:
        return "SAFE_VOCAB"
    for sv in _SAFE_LOWER:
        if canon == sv or sv in canon:
            return "SAFE_VOCAB"

    if entity.label in ("ORG", "PRODUCT"):
        return "POTENTIAL_HALLUCINATION"
    if entity.label == "PERSON":
        return "POTENTIAL_HALLUCINATION"
    if entity.label == "DATE":
        return "POTENTIAL_HALLUCINATION"
    if entity.label == "CARDINAL":
        return "AMBIGUOUS"
    if entity.label == "GPE":
        return "AMBIGUOUS"

    return "AMBIGUOUS"
