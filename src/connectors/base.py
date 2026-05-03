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
