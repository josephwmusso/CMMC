"""Registration tests for M365GccHighConnector — Pass F.3d visibility contract.

F.3d flipped the eager-import that gated production visibility through
F.2/F.3a/F.3b/F.3c. The connector class is registered via the @register
decorator AND eager-imported from src/connectors/__init__.py, so
/api/connectors/types now returns m365_gcc_high alongside echo and
entra_id in production.

Visibility mechanism: src.connectors.registry.list_types() iterates the
full _REGISTRY and the /api/connectors/types route returns it directly.
A connector becomes visible to /api/connectors/types the moment its
module is imported anywhere — there is no separate "eager-imported
allowlist". So in production, the only thing that decides what the
endpoint shows is which modules src/connectors/__init__.py imports.

Why a static-source check rather than a runtime registry-state check:
once any pytest test file imports M365GccHighConnector, the @register
decorator permanently adds it to _REGISTRY for the rest of the session.
A runtime "list_types() should contain m365_gcc_high" assertion would
pass even before F.3d's flip — purely because of test-collection
ordering, not because the production import graph actually loads the
module. The static check directly enforces the production-relevant
invariant: "the eager-import line IS in the file that gates production
visibility."

This pollution-mitigation reasoning is structural — it survived the
F.3d flip unchanged. The check inverts (presence-asserting now, was
absence-asserting through F.2/F.3a/F.3b/F.3c) but the SHAPE of the
check (read source, scan for the import line) is the right one
regardless of which side of the contract is being enforced.
"""

from __future__ import annotations

from pathlib import Path

# Direct import — this fires @register and adds m365_gcc_high to _REGISTRY
# for the rest of the pytest session. That's expected and is what
# TestRegistration relies on. Production visibility is a separate concern,
# enforced at the source-file level by TestVisibilityContract below.
from src.connectors.connectors_builtin.m365_gcc_high import M365GccHighConnector
from src.connectors.registry import _REGISTRY, get_connector_class


class TestRegistration:
    """The @register decorator placed M365GccHighConnector in the registry
    after this file imported the module. This proves the registration
    mechanism works; production visibility is a separate concern,
    enforced by TestVisibilityContract below.
    """

    def test_m365_gcc_high_in_registry_after_direct_import(self):
        assert "m365_gcc_high" in _REGISTRY

    def test_get_connector_class_returns_m365_gcc_high(self):
        cls = get_connector_class("m365_gcc_high")
        assert cls is M365GccHighConnector


class TestVisibilityContract:
    """F.3d flipped the eager-import in src/connectors/__init__.py so
    production /api/connectors/types now shows m365_gcc_high alongside
    echo and entra_id.

    These are static-source checks — order-independent, robust to test
    pollution of the runtime registry, and they assert the actual
    production-relevant invariant. Inversion of F.2's invisibility
    contract; the check shape is unchanged because the source-file
    invariant is the right thing to test on either side of the flip.
    """

    @staticmethod
    def _connectors_init_path() -> Path:
        return (
            Path(__file__).parents[2]
            / "src" / "connectors" / "__init__.py"
        )

    def test_eager_imported_in_connectors_init(self):
        """src/connectors/__init__.py MUST contain the eager-import line
        for m365_gcc_high. F.3d landed this; future maintainers must not
        regress it (same defensive shape as the entra_id and echo
        regression bars below).
        """
        source = self._connectors_init_path().read_text(encoding="utf-8")
        assert (
            "from src.connectors.connectors_builtin import m365_gcc_high"
            in source
        ), (
            "src/connectors/__init__.py must eager-import m365_gcc_high "
            "(F.3d landed this line; do not remove it without a deliberate "
            "visibility-rollback decision documented in the commit)."
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
            "(Pass E.3d landed this line; F.3d must not regress it)."
        )

    def test_echo_still_eager_imported(self):
        """Regression bar: same defensive check for the echo connector."""
        source = self._connectors_init_path().read_text(encoding="utf-8")
        assert (
            "from src.connectors.connectors_builtin import echo"
            in source
        ), (
            "src/connectors/__init__.py must still eager-import echo "
            "(Pass E.2 landed this line; F.3d must not regress it)."
        )
