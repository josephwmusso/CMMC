"""Assertion recorder with collect-all semantics."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class AssertionResult:
    name: str
    passed: bool
    actual: Any = None
    expected: Any = None
    detail: str = ""
    ts: str = ""


class AssertionFailure(Exception):
    def __init__(self, result: AssertionResult):
        self.result = result
        super().__init__(f"FAIL: {result.name}: {result.detail}")


class AssertionRecorder:
    def __init__(self, fail_fast: bool = False):
        self.results: list[AssertionResult] = []
        self.fail_fast = fail_fast

    def expect(self, name: str, condition: bool, actual: Any = None,
               expected: Any = None, detail: str = "") -> bool:
        result = AssertionResult(
            name=name, passed=condition, actual=actual,
            expected=expected, detail=detail,
            ts=datetime.now(timezone.utc).isoformat(),
        )
        self.results.append(result)
        if not condition and self.fail_fast:
            raise AssertionFailure(result)
        return condition

    def warn(self, name: str, detail: str = "", actual: Any = None):
        self.results.append(AssertionResult(
            name=name, passed=True, actual=actual,
            detail=f"WARNING: {detail}",
            ts=datetime.now(timezone.utc).isoformat(),
        ))

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def all_passed(self) -> bool:
        return self.failed_count == 0

    def failures(self) -> list[AssertionResult]:
        return [r for r in self.results if not r.passed]

    def warnings(self) -> list[AssertionResult]:
        return [r for r in self.results if r.passed and "WARNING" in (r.detail or "")]

    def by_stage(self, prefix: str) -> tuple[int, int]:
        stage = [r for r in self.results if r.name.startswith(prefix)]
        p = sum(1 for r in stage if r.passed)
        f = sum(1 for r in stage if not r.passed)
        return p, f

    def flush(self, run_dir: Path):
        path = run_dir / "assertions.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                [{"name": r.name, "passed": r.passed, "actual": str(r.actual)[:500],
                  "expected": str(r.expected)[:500], "detail": r.detail, "ts": r.ts}
                 for r in self.results],
                f, indent=2, default=str,
            )

    def summary_text(self, run_dir: Path, fixture_name: str, backend_url: str,
                     org_id: str, duration_s: float) -> str:
        now = datetime.now(timezone.utc).isoformat()
        lines = [
            f"Phase 3A.2a Run — {now}",
            f"Fixture: {fixture_name}",
            f"Backend: {backend_url}",
            f"Duration: {duration_s:.0f}s",
            f"Org ID: {org_id}",
            "",
            "Stage Results:",
        ]
        for stage in ["setup", "intake", "evidence", "scans", "cross"]:
            p, f = self.by_stage(f"{stage}.")
            if p + f == 0:
                continue
            status = "✓" if f == 0 else "✗"
            w = len([r for r in self.results if r.name.startswith(f"{stage}.") and "WARNING" in (r.detail or "")])
            parts = [f"{p}/{p+f} passed"]
            if w:
                parts.append(f"{w} warning(s)")
            if f:
                parts.append(f"{f} FAILED")
            lines.append(f"  {stage:<12} {status} {', '.join(parts)}")

        fails = self.failures()
        if fails:
            lines += ["", "FAILURES:"]
            for r in fails:
                lines.append(f"  {r.name}")
                if r.expected:
                    lines.append(f"    expected: {str(r.expected)[:200]}")
                if r.actual:
                    lines.append(f"    actual:   {str(r.actual)[:200]}")
                if r.detail:
                    lines.append(f"    detail:   {r.detail}")

        warns = self.warnings()
        if warns:
            lines += ["", "WARNINGS:"]
            for r in warns:
                lines.append(f"  {r.name}: {r.detail}")

        return "\n".join(lines)
