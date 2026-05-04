"""Defensive guards on src/evidence/storage.py."""

from __future__ import annotations

import pytest

from src.evidence.storage import link_evidence_to_controls


def test_link_evidence_objective_only_raises():
    """Calling with empty control_ids and non-empty objective_ids raises
    ValueError before any SQL runs (the underlying INSERT would otherwise
    violate the NOT NULL constraint on evidence_control_map.control_id).
    """
    with pytest.raises(ValueError, match="control_ids required"):
        link_evidence_to_controls(
            db=None,  # never reached — guard fires first
            artifact_id="EVD-TEST",
            control_ids=[],
            objective_ids=["AC.L2-3.1.1[a]"],
        )
