"""Abstract base for all connectors + the PulledEvidence contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class PulledEvidence:
    """A single evidence artifact yielded by a connector pull.

    Attributes:
        filename: Display name; will be persisted as evidence_artifacts.filename.
        content: Raw bytes to be written to disk and SHA-256 hashed.
        mime_type: Content type. Default is application/json (most API pulls).
        description: Human-readable description. Stored on the artifact row.
        control_ids: CMMC control IDs (e.g., "AC.L2-3.1.1") this evidence supports.
        metadata: Connector-specific extras. Persisted into the artifact's
                  source-system field path or an audit detail; not surfaced to
                  the user directly in 5.1.
    """

    filename: str
    content: bytes
    mime_type: str = "application/json"
    description: str = ""
    control_ids: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class BaseConnector(ABC):
    """Subclass and register via @register to add a new connector type.

    Required class attributes (override in every subclass):
        type_name:          stable string ID, e.g. "entra_id"
        display_name:       human label, e.g. "Microsoft Entra ID"
        supported_controls: CMMC control IDs this connector can produce
                            evidence for. Informational only in 5.1; not
                            enforced.
    """

    type_name: str = ""
    display_name: str = ""
    supported_controls: list[str] = []

    # ----- Setup wizard contract --------------------------------------------
    #
    # credentials_schema declares the fields the setup form will render.
    # The generic frontend renderer handles four field types only:
    #
    #     text     | password    | select    | textarea
    #
    # A field declaration looks like:
    #
    #     {
    #         "name": "tenant_id",            # required, becomes the key in
    #                                          #   the credentials dict
    #         "label": "Tenant ID",           # required, shown above the input
    #         "type": "text",                 # required, one of the four above
    #         "required": True,               # optional, default False
    #         "help": "Found in Entra...",    # optional, rendered below input
    #         "placeholder": "00000000-...",  # optional, text/password only
    #         "options": [                    # required for type=select
    #             {"value": "us-1", "label": "US-1 (Commercial)"},
    #             ...
    #         ],
    #     }
    #
    # HARD BOUNDARY RULES — do not break these when adding new connectors:
    #
    #   1. Schema fields cannot reference other fields. No conditional
    #      visibility, no cross-field validation. If you need that, set
    #      setup_component instead.
    #
    #   2. Schema cannot embed code, expressions, or callbacks. No regex
    #      validators, no JS hooks. If you need that, set setup_component.
    #
    # When either rule would be tempting to break, the answer is always
    # "use setup_component and write a real React component." The schema
    # stays a contract, not a DSL.
    #
    credentials_schema: list[dict] = []

    # If set, the frontend renders the named component from
    # src/app/components/connector-setup/registry.ts instead of the
    # generic form. Use only when credentials_schema cannot express
    # the setup flow (OAuth redirects, multi-step wizards, region
    # cascades, custom widgets).
    setup_component: str | None = None

    def __init__(self, config: dict, credentials: dict):
        """config is non-secret tunables; credentials is the decrypted secrets dict."""
        self.config = config or {}
        self.credentials = credentials or {}

    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """Return (success, message). Must NOT raise.

        Called before pull() to short-circuit obvious credential or
        network failures. Message surfaces to the API caller.
        """

    @abstractmethod
    def pull(self) -> Iterator[PulledEvidence]:
        """Yield PulledEvidence items.

        May raise on unrecoverable errors; the runner will mark the run
        FAILED in that case. Per-item failures should be handled inside
        pull() — yield what works, log what doesn't.
        """
