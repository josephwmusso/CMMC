"""Tests for PulledEvidence framework contracts (F.1).

Verifies the F.1 default-respect contract: PulledEvidence's new optional
fields default to backward-compatible values so that connectors written
before F.1 (Pass E EntraIdConnector, EchoConnector, framework synthetic
test connectors) continue to construct PulledEvidence objects with no
edits required.

Per Phase 2 design: advisory Literal annotations only, no runtime validation
(no __post_init__ raise on invalid values). Type checkers catch typos
statically; runtime is permissive.
"""

from __future__ import annotations

from src.connectors.base import PulledEvidence


class TestPulledEvidenceDefaults:
    """F.1 default-respect contract.

    A PulledEvidence constructed with only the required fields (filename,
    content) must produce sensible defaults for the new F.1 fields. Pre-F.1
    connectors do not set these fields explicitly.
    """

    def test_minimum_required_fields_default_to_full_raw_not_degraded(self):
        pe = PulledEvidence(filename="x.json", content=b"{}")
        assert pe.coverage_scope == "full"
        assert pe.missing_sources == []
        assert pe.evidence_directness == "raw_config"
        assert pe.degraded is False
        assert pe.degradation_reason is None

    def test_pre_f1_kwargs_still_work_unchanged(self):
        # Mirrors Pass E EntraIdConnector / EchoConnector construction style.
        pe = PulledEvidence(
            filename="entra_users.json",
            content=b'{"users":[]}',
            mime_type="application/json",
            description="Users from Entra",
            control_ids=["AC.L2-3.1.1"],
            metadata={"user_count": 0},
        )
        # Pre-F.1 fields preserved exactly.
        assert pe.filename == "entra_users.json"
        assert pe.content == b'{"users":[]}'
        assert pe.mime_type == "application/json"
        assert pe.description == "Users from Entra"
        assert pe.control_ids == ["AC.L2-3.1.1"]
        assert pe.metadata == {"user_count": 0}
        # F.1 fields take their defaults — no edit required at the call site.
        assert pe.coverage_scope == "full"
        assert pe.missing_sources == []
        assert pe.evidence_directness == "raw_config"
        assert pe.degraded is False
        assert pe.degradation_reason is None

    # ---- explicit round-trips for each new field ----

    def test_partial_coverage_with_missing_sources_round_trip(self):
        pe = PulledEvidence(
            filename="x.json",
            content=b"{}",
            coverage_scope="partial",
            missing_sources=["dlp_policies", "label_policies"],
        )
        assert pe.coverage_scope == "partial"
        assert pe.missing_sources == ["dlp_policies", "label_policies"]
        # Other F.1 fields take defaults.
        assert pe.evidence_directness == "raw_config"
        assert pe.degraded is False
        assert pe.degradation_reason is None

    def test_aggregate_directness_round_trip(self):
        pe = PulledEvidence(
            filename="secure_score.json",
            content=b"{}",
            evidence_directness="aggregate",
        )
        assert pe.evidence_directness == "aggregate"
        # Other F.1 fields take defaults.
        assert pe.coverage_scope == "full"
        assert pe.missing_sources == []
        assert pe.degraded is False

    def test_degraded_with_reason_round_trip(self):
        pe = PulledEvidence(
            filename="intune_unavailable.json",
            content=b"{}",
            degraded=True,
            degradation_reason="Intune license not found",
        )
        assert pe.degraded is True
        assert pe.degradation_reason == "Intune license not found"
        # Other F.1 fields take defaults.
        assert pe.coverage_scope == "full"
        assert pe.evidence_directness == "raw_config"

    def test_all_f1_fields_explicit_round_trip(self):
        """Sanity: setting all five F.1 fields together at once works."""
        pe = PulledEvidence(
            filename="combined.json",
            content=b"{}",
            coverage_scope="partial",
            missing_sources=["exchange_online_tls"],
            evidence_directness="aggregate",
            degraded=True,
            degradation_reason="No Defender license",
        )
        assert pe.coverage_scope == "partial"
        assert pe.missing_sources == ["exchange_online_tls"]
        assert pe.evidence_directness == "aggregate"
        assert pe.degraded is True
        assert pe.degradation_reason == "No Defender license"

    # ---- design assertion: no runtime validation ----

    def test_invalid_literal_values_do_not_raise_at_runtime(self):
        """Per Phase 2 design: advisory annotations only. Type checkers
        flag typos statically; runtime is permissive. This test documents
        the design choice — change it (and the design) together if we ever
        decide to enforce at runtime."""
        # A semantically-invalid value passes through silently.
        pe = PulledEvidence(
            filename="x.json",
            content=b"{}",
            coverage_scope="aprtial",  # type: ignore[arg-type]  # intentional typo
        )
        assert pe.coverage_scope == "aprtial"

        pe2 = PulledEvidence(
            filename="x.json",
            content=b"{}",
            evidence_directness="rwa_config",  # type: ignore[arg-type]
        )
        assert pe2.evidence_directness == "rwa_config"
