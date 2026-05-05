"""Registration tests for M365GccHighConnector — Pass F.2 invisibility contract.

F.2 ships the connector class on disk and registers it via the @register
decorator (which fires when this file imports the module), but the module
is NOT eager-imported from src/connectors/__init__.py. F.3d flips that
switch.

Visibility mechanism: src.connectors.registry.list_types() iterates the
full _REGISTRY and the /api/connectors/types route returns it directly.
A connector becomes visible to /api/connectors/types the moment its
module is imported anywhere — there is no separate "eager-imported
allowlist". So in production, the only thing that decides what the
endpoint shows is which modules src/connectors/__init__.py imports.

Why a static-source check rather than a runtime registry-state check:
once any pytest test file imports M365GccHighConnector, the @register
decorator permanently adds it to _REGISTRY for the rest of the session.
A runtime "list_types() should not contain m365_gcc_high" assertion
would fail purely based on test-collection ordering, not on a real
contract violation. The static check directly enforces the production-
relevant invariant: "the eager-import line is not in the file that
gates production visibility."
"""

from __future__ import annotations

from pathlib import Path

# Direct import — this fires @register and adds m365_gcc_high to _REGISTRY
# for the rest of the pytest session. That's expected and is what
# TestRegistration relies on. The invisibility contract is enforced at
# the source-file level by TestInvisibilityContract, not at runtime.
from src.connectors.connectors_builtin.m365_gcc_high import M365GccHighConnector
from src.connectors.registry import _REGISTRY, get_connector_class


class TestRegistration:
    """The @register decorator placed M365GccHighConnector in the registry
    after this file imported the module. This proves the registration
    mechanism works for F.2; production visibility is a separate concern,
    enforced by TestInvisibilityContract below.
    """

    def test_m365_gcc_high_in_registry_after_direct_import(self):
        assert "m365_gcc_high" in _REGISTRY

    def test_get_connector_class_returns_m365_gcc_high(self):
        cls = get_connector_class("m365_gcc_high")
        assert cls is M365GccHighConnector


class TestInvisibilityContract:
    """F.2 ships code-on-disk; F.3d flips the switch by adding the
    eager-import to src/connectors/__init__.py. Until then, production
    /api/connectors/types must NOT show m365_gcc_high.

    These are static-source checks — order-independent, robust to test
    pollution of the runtime registry, and they assert the actual
    production-relevant invariant.
    """

    @staticmethod
    def _connectors_init_path() -> Path:
        return (
            Path(__file__).parents[2]
            / "src" / "connectors" / "__init__.py"
        )

    def test_not_eager_imported_in_connectors_init(self):
        """src/connectors/__init__.py must contain NO non-comment line
        referencing m365_gcc_high. F.3d adds the line.
        """
        source = self._connectors_init_path().read_text(encoding="utf-8")
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            assert "m365_gcc_high" not in stripped, (
                f"src/connectors/__init__.py must NOT eager-import "
                f"m365_gcc_high until F.3d. Offending line: {line!r}"
            )

    def test_entra_id_still_eager_imported(self):
        """Regression bar: confirm Pass E's entra_id eager-import is still
        in place. Without this, an editor accidentally removing it (e.g.
        while cleaning up comments) would slip past review.
        """
        source = self._connectors_init_path().read_text(encoding="utf-8")
        assert (
            "from src.connectors.connectors_builtin import entra_id"
            in source
        ), (
            "src/connectors/__init__.py must still eager-import entra_id "
            "(Pass E.3d landed this line; F.2 must not regress it)."
        )

    def test_echo_still_eager_imported(self):
        """Regression bar: same defensive check for the echo connector."""
        source = self._connectors_init_path().read_text(encoding="utf-8")
        assert (
            "from src.connectors.connectors_builtin import echo"
            in source
        ), (
            "src/connectors/__init__.py must still eager-import echo "
            "(Pass E.2 landed this line; F.2 must not regress it)."
        )
