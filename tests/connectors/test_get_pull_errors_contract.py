"""Contract tests for BaseConnector.get_pull_errors() and runner integration.

Pass E.3b — the contract by which connectors expose per-control errors
accumulated internally during pull(). Default returns []; subclasses may
override.

These tests are framework-level. They use synthetic test connectors, NOT
EntraIdConnector (which doesn't yet consume the contract; that's Pass E.3c).
"""

from __future__ import annotations

from typing import Iterator
from unittest.mock import patch, MagicMock

import pytest

from src.connectors.base import BaseConnector, PulledEvidence


# ──────────────────────────────────────────────────────────────────────
# Synthetic test connectors
# ──────────────────────────────────────────────────────────────────────

class _SilentConnector(BaseConnector):
    """Inherits default get_pull_errors() — returns []."""

    type_name = "_test_silent"
    display_name = "Test: silent"
    supported_controls = ["AC.L2-3.1.1"]
    credentials_schema = []
    setup_component = None

    def __init__(self, config: dict, credentials: dict):
        super().__init__(config, credentials)

    def test_connection(self) -> tuple[bool, str]:
        return (True, "ok")

    def pull(self) -> Iterator[PulledEvidence]:
        yield PulledEvidence(
            filename="silent.json",
            content=b"{}",
            control_ids=["AC.L2-3.1.1"],
        )


class _AccumulatingConnector(BaseConnector):
    """Overrides get_pull_errors() to expose accumulated errors."""

    type_name = "_test_accumulating"
    display_name = "Test: accumulating"
    supported_controls = ["AC.L2-3.1.1", "AC.L2-3.1.5"]
    credentials_schema = []
    setup_component = None

    def __init__(self, config: dict, credentials: dict):
        super().__init__(config, credentials)
        self._pull_errors: list[str] = []

    def test_connection(self) -> tuple[bool, str]:
        return (True, "ok")

    def pull(self) -> Iterator[PulledEvidence]:
        # Reset at start of pull — belt-and-suspenders.
        self._pull_errors = []

        # First control succeeds.
        yield PulledEvidence(
            filename="success.json",
            content=b"{}",
            control_ids=["AC.L2-3.1.1"],
        )

        # Second control "fails" — caught internally, error accumulated,
        # no yield for that control.
        self._pull_errors.append(
            "AC.L2-3.1.5 | /test | RuntimeError: simulated failure"
        )

    def get_pull_errors(self) -> list[str]:
        return list(self._pull_errors)


# ──────────────────────────────────────────────────────────────────────
# BaseConnector default behavior
# ──────────────────────────────────────────────────────────────────────

class TestDefaultGetPullErrors:

    def test_default_returns_empty_list(self):
        c = _SilentConnector(config={}, credentials={})
        assert c.get_pull_errors() == []

    def test_default_is_callable_after_pull_exhausts(self):
        c = _SilentConnector(config={}, credentials={})
        list(c.pull())  # exhaust
        assert c.get_pull_errors() == []

    def test_default_is_callable_before_pull(self):
        # Calling before pull() runs is allowed (returns []).
        c = _SilentConnector(config={}, credentials={})
        assert c.get_pull_errors() == []


# ──────────────────────────────────────────────────────────────────────
# Subclass override behavior
# ──────────────────────────────────────────────────────────────────────

class TestOverriddenGetPullErrors:

    def test_override_surfaces_accumulated_errors(self):
        c = _AccumulatingConnector(config={}, credentials={})
        list(c.pull())  # exhaust
        errors = c.get_pull_errors()
        assert len(errors) == 1
        assert "AC.L2-3.1.5" in errors[0]
        assert "simulated failure" in errors[0]

    def test_override_returns_copy_not_reference(self):
        # Mutating the returned list should not mutate connector state.
        c = _AccumulatingConnector(config={}, credentials={})
        list(c.pull())
        errors = c.get_pull_errors()
        errors.append("mutation")
        assert "mutation" not in c.get_pull_errors()

    def test_pull_resets_accumulator(self):
        # Two sequential pulls on the same instance — second pull resets.
        c = _AccumulatingConnector(config={}, credentials={})
        list(c.pull())
        assert len(c.get_pull_errors()) == 1
        list(c.pull())
        assert len(c.get_pull_errors()) == 1  # still one, not two

    def test_yield_count_unchanged_by_accumulation(self):
        # Accumulation is a side channel — it doesn't affect what pull yields.
        c = _AccumulatingConnector(config={}, credentials={})
        items = list(c.pull())
        assert len(items) == 1
        assert items[0].control_ids == ["AC.L2-3.1.1"]


# ──────────────────────────────────────────────────────────────────────
# Runner integration — runner.run_connector consumes get_pull_errors()
# ──────────────────────────────────────────────────────────────────────

class TestRunnerConsumesGetPullErrors:
    """Integration test: runner -> get_pull_errors() -> summary.errors[].

    Uses the actual run_connector function with mocked storage and
    upload_evidence dependencies.
    """

    def test_runner_extends_errors_with_accumulated_errors(self):
        from src.connectors import runner

        with patch.object(runner, "reg") as mock_reg, \
             patch.object(runner, "cstore") as mock_cstore, \
             patch.object(runner, "upload_evidence") as mock_upload, \
             patch.object(runner, "link_evidence_to_controls"):

            mock_reg.get_connector_class.return_value = _AccumulatingConnector

            # cstore.get_connector returns a dict (storage.py:74-110 actual shape).
            # Only fields the runner reads: type, config, credentials.
            mock_cstore.get_connector.return_value = {
                "type": "_test_accumulating",
                "config": {},
                "credentials": {},
            }
            # cstore.create_connector_run returns a string ID.
            mock_cstore.create_connector_run.return_value = "CRUN-TEST"
            # upload_evidence returns a dict with artifact_id.
            mock_upload.return_value = {"artifact_id": "EVD-TEST"}

            captured_summary: dict = {}

            def capture_update(*args, **kwargs):
                if "summary" in kwargs:
                    captured_summary.update(kwargs["summary"])

            mock_cstore.update_connector_run.side_effect = capture_update

            mock_db = MagicMock()
            runner.run_connector(
                db=mock_db,
                connector_id="CONN-TEST",
                org_id="9de53b587b23450b87af",
                triggered_by="manual",
                triggered_by_user_id="USR-TEST",
            )

            errors = captured_summary.get("errors", [])
            assert len(errors) == 1, f"expected 1 error, got: {errors}"
            assert "AC.L2-3.1.5" in errors[0]
            assert "simulated failure" in errors[0]

    def test_runner_does_not_call_get_pull_errors_on_catastrophic_failure(self):
        # If pull() itself raises, the catastrophic outer except runs.
        # get_pull_errors() should NOT be called there — we don't want
        # to surface accumulator state when the generator died.

        from src.connectors import runner

        class _CatastrophicConnector(_SilentConnector):
            type_name = "_test_catastrophic"
            get_pull_errors_call_count = 0

            def pull(self):
                raise RuntimeError("catastrophic")
                yield  # pragma: no cover

            def get_pull_errors(self):
                # If this gets called during the catastrophic path, we'll
                # see it via the class attribute.
                type(self).get_pull_errors_call_count += 1
                return ["should not appear"]

        _CatastrophicConnector.get_pull_errors_call_count = 0

        with patch.object(runner, "reg") as mock_reg, \
             patch.object(runner, "cstore") as mock_cstore, \
             patch.object(runner, "upload_evidence"):

            mock_reg.get_connector_class.return_value = _CatastrophicConnector
            mock_cstore.get_connector.return_value = {
                "type": "_test_catastrophic",
                "config": {},
                "credentials": {},
            }
            mock_cstore.create_connector_run.return_value = "CRUN-CAT"

            captured_summary: dict = {}

            def capture_update(*args, **kwargs):
                if "summary" in kwargs:
                    captured_summary.update(kwargs["summary"])

            mock_cstore.update_connector_run.side_effect = capture_update

            mock_db = MagicMock()
            with pytest.raises(RuntimeError):
                runner.run_connector(
                    db=mock_db,
                    connector_id="CONN-CAT",
                    org_id="9de53b587b23450b87af",
                    triggered_by="manual",
                    triggered_by_user_id="USR-TEST",
                )

            # The "should not appear" string from the connector's
            # get_pull_errors() must NOT be in summary.errors.
            errors = captured_summary.get("errors", [])
            assert "should not appear" not in errors
            # And the catastrophic error message should be there.
            assert any("catastrophic" in e for e in errors), errors
            # get_pull_errors should not have been called.
            assert _CatastrophicConnector.get_pull_errors_call_count == 0
