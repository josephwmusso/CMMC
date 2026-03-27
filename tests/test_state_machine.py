"""
tests/test_state_machine.py

Tests for evidence state machine and audit chain.
Uses an in-memory SQLite DB so no Postgres required.

Run: pytest tests/test_state_machine.py -v
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from src.evidence.state_machine import (
    VALID_TRANSITIONS,
    StateTransitionError,
    _compute_entry_hash,
    _get_prev_hash,
    transition_evidence,
    verify_audit_chain,
)


class TestValidTransitions:
    def test_draft_can_go_to_reviewed(self):
        assert "REVIEWED" in VALID_TRANSITIONS["DRAFT"]

    def test_reviewed_can_go_to_approved_or_draft(self):
        assert "APPROVED" in VALID_TRANSITIONS["REVIEWED"]
        assert "DRAFT" in VALID_TRANSITIONS["REVIEWED"]

    def test_approved_can_go_to_published_or_reviewed(self):
        assert "PUBLISHED" in VALID_TRANSITIONS["APPROVED"]
        assert "REVIEWED" in VALID_TRANSITIONS["APPROVED"]

    def test_published_is_terminal(self):
        assert VALID_TRANSITIONS["PUBLISHED"] == []

    def test_draft_cannot_skip_to_published(self):
        assert "PUBLISHED" not in VALID_TRANSITIONS["DRAFT"]

    def test_draft_cannot_skip_to_approved(self):
        assert "APPROVED" not in VALID_TRANSITIONS["DRAFT"]


class TestComputeEntryHash:
    def test_returns_64_char_hex(self):
        h = _compute_entry_hash(
            actor="user1",
            actor_type="user",
            action="evidence.REVIEWED",
            target_type="evidence_artifact",
            target_id="EVD-001",
            details={"from_state": "DRAFT", "to_state": "REVIEWED"},
            prev_hash="GENESIS",
            timestamp="2026-03-01T00:00:00+00:00",
        )
        assert isinstance(h, str)
        assert len(h) == 64

    def test_deterministic(self):
        kwargs = dict(
            actor="u", actor_type="user", action="ev.R",
            target_type="evidence_artifact", target_id="EVD-1",
            details={}, prev_hash="GENESIS", timestamp="2026-01-01T00:00:00+00:00",
        )
        assert _compute_entry_hash(**kwargs) == _compute_entry_hash(**kwargs)

    def test_different_inputs_produce_different_hashes(self):
        base = dict(
            actor="u", actor_type="user", action="ev.R",
            target_type="evidence_artifact", target_id="EVD-1",
            details={}, prev_hash="GENESIS", timestamp="2026-01-01T00:00:00+00:00",
        )
        modified = {**base, "actor": "different_user"}
        assert _compute_entry_hash(**base) != _compute_entry_hash(**modified)

    def test_changing_prev_hash_changes_output(self):
        base = dict(
            actor="u", actor_type="user", action="ev.R",
            target_type="evidence_artifact", target_id="EVD-1",
            details={}, prev_hash="GENESIS", timestamp="2026-01-01T00:00:00+00:00",
        )
        modified = {**base, "prev_hash": "abc123"}
        assert _compute_entry_hash(**base) != _compute_entry_hash(**modified)


class TestTransitionEvidence:
    def _make_mock_db(self, current_state: str, artifact_id: str = "EVD-001"):
        """Build a mock SQLAlchemy session that simulates an artifact row."""
        db = MagicMock()

        # Simulate the SELECT returning (id, org_id, filename, file_path, state, sha256_hash)
        mock_row = (artifact_id, "org-1", "policy.pdf", "/tmp/policy.pdf", current_state, None)
        db.execute.return_value.fetchone.return_value = mock_row

        # Simulate _get_prev_hash returning GENESIS
        genesis_row = MagicMock()
        genesis_row.__getitem__ = lambda self, i: "GENESIS"

        return db

    def test_draft_to_reviewed_succeeds(self):
        db = self._make_mock_db("DRAFT")
        with patch("src.evidence.state_machine._get_prev_hash", return_value="GENESIS"):
            result = transition_evidence(db, "EVD-001", "REVIEWED", actor="alice")
        assert result["new_state"] == "REVIEWED"
        assert result["previous_state"] == "DRAFT"
        assert result["actor"] == "alice"

    def test_invalid_transition_raises(self):
        db = self._make_mock_db("DRAFT")
        with pytest.raises(StateTransitionError):
            transition_evidence(db, "EVD-001", "PUBLISHED", actor="alice")

    def test_published_is_immutable(self):
        db = self._make_mock_db("PUBLISHED")
        with pytest.raises(StateTransitionError, match="immutable"):
            transition_evidence(db, "EVD-001", "REVIEWED", actor="alice")

    def test_missing_artifact_raises(self):
        db = MagicMock()
        db.execute.return_value.fetchone.return_value = None
        with pytest.raises(ValueError, match="not found"):
            transition_evidence(db, "NONEXISTENT", "REVIEWED", actor="alice")

    def test_published_transition_hashes_file(self, tmp_path):
        """Publishing should compute SHA-256 of the actual file."""
        test_file = tmp_path / "evidence.pdf"
        test_file.write_bytes(b"test evidence content")

        db = MagicMock()
        mock_row = ("EVD-001", "org-1", "evidence.pdf", str(test_file), "APPROVED", None)
        db.execute.return_value.fetchone.return_value = mock_row

        with patch("src.evidence.state_machine._get_prev_hash", return_value="GENESIS"):
            result = transition_evidence(db, "EVD-001", "PUBLISHED", actor="bob")

        assert result["new_state"] == "PUBLISHED"
        assert result["sha256_hash"] is not None
        assert len(result["sha256_hash"]) == 64


class TestVerifyAuditChain:
    def test_empty_chain_is_valid(self):
        db = MagicMock()
        db.execute.return_value.fetchall.return_value = []
        result = verify_audit_chain(db)
        assert result["valid"] is True
        assert result["entries_checked"] == 0
        assert result["first_broken"] is None

    def test_valid_single_entry_chain(self):
        """A single genesis entry should verify cleanly."""
        from datetime import datetime, timezone

        db = MagicMock()

        details = {"from_state": "DRAFT", "to_state": "REVIEWED"}
        ts = "2026-03-01T00:00:00+00:00"
        entry_hash = _compute_entry_hash(
            actor="alice",
            actor_type="user",
            action="evidence.REVIEWED",
            target_type="evidence_artifact",
            target_id="EVD-001",
            details=details,
            prev_hash="GENESIS",
            timestamp=ts,
        )

        mock_row = (
            1, "alice", "user", "evidence.REVIEWED",
            "evidence_artifact", "EVD-001",
            details, "GENESIS", entry_hash, ts,
        )
        db.execute.return_value.fetchall.return_value = [mock_row]

        result = verify_audit_chain(db)
        assert result["valid"] is True
        assert result["entries_checked"] == 1

    def test_tampered_entry_detected(self):
        """A chain entry with a wrong hash should fail verification."""
        db = MagicMock()
        ts = "2026-03-01T00:00:00+00:00"
        mock_row = (
            1, "alice", "user", "evidence.REVIEWED",
            "evidence_artifact", "EVD-001",
            {}, "GENESIS", "wrong_hash_here", ts,
        )
        db.execute.return_value.fetchall.return_value = [mock_row]

        result = verify_audit_chain(db)
        assert result["valid"] is False
        assert result["first_broken"] == 1
