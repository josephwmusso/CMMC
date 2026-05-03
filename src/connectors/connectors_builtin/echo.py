"""EchoConnector — trivial built-in that yields a fixed payload.

Purpose: end-to-end proof of the framework. NOT a real evidence source.
Useful for: local smoke tests, the verification harness, demoing the
plumbing before any real connector exists.
"""

from __future__ import annotations

import json
from typing import Iterator

from src.connectors.base import BaseConnector, PulledEvidence
from src.connectors.registry import register


@register
class EchoConnector(BaseConnector):
    type_name = "echo"
    display_name = "Echo (test stub)"
    supported_controls = ["AC.L2-3.1.1"]

    def test_connection(self) -> tuple[bool, str]:
        return True, "echo connector always succeeds"

    def pull(self) -> Iterator[PulledEvidence]:
        payload = {
            "stub": True,
            "message": self.config.get("message", "hello from echo"),
            "echoed_keys": sorted(self.credentials.keys()),
        }
        yield PulledEvidence(
            filename="echo_payload.json",
            content=json.dumps(payload, sort_keys=True).encode("utf-8"),
            mime_type="application/json",
            description="Echo connector test payload (Phase 5.1 plumbing verification)",
            control_ids=["AC.L2-3.1.1"],
            metadata={"connector": "echo"},
        )
