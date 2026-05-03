"""
Connector framework (Phase 5.1).

External-system integrations that pull evidence into the platform.
Connectors run on customer compute, hit customer-owned APIs, and
produce DRAFT evidence_artifacts. No data leaves the customer's
deployment boundary.
"""

# Eagerly import the builtins package so registered connector classes are
# visible to registry consumers as soon as src.connectors is imported. This
# runs before any HTTP request can call list_types() or run_connector().
from src.connectors.connectors_builtin import echo  # noqa: F401  (registers EchoConnector)
