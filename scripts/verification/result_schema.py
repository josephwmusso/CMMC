"""Standard result schema for verification layers. Stdlib only — no Pydantic."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class AssertionResult:
    name: str
    status: str          # PASS, FAIL, WARN, SKIP
    message: str = ""
    duration_ms: Optional[float] = None


@dataclass
class LayerResult:
    layer_name: str
    layer_id: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    warned: int = 0
    skipped: int = 0
    duration_seconds: float = 0.0
    assertions: list = field(default_factory=list)
    environment: str = "local"
    timestamp: str = ""
    fixture_name: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["assertions"] = [asdict(a) if not isinstance(a, dict) else a for a in self.assertions]
        return d


@dataclass
class VerificationReport:
    report_id: str = ""
    generated_at: str = ""
    environment: str = "local"
    platform_version: str = ""
    layers: list = field(default_factory=list)
    audit_summary: dict = field(default_factory=dict)
    overall_status: str = "PASS"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["layers"] = [l.to_dict() if hasattr(l, "to_dict") else l for l in self.layers]
        return d


def save_json(obj, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = obj.to_dict() if hasattr(obj, "to_dict") else asdict(obj)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def load_layer_result(path: str | Path) -> LayerResult:
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    assertions = [AssertionResult(**a) for a in d.pop("assertions", [])]
    return LayerResult(**d, assertions=assertions)
