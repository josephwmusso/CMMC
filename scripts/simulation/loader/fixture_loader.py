"""Load and validate a customer simulation fixture."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml

from scripts.simulation.loader.schemas import (
    CompanyProfile,
    Contradiction,
    EvidenceArtifact,
    ExpectedOutputs,
    Fixture,
    ForbiddenList,
    IntakeAnswer,
)


class FixtureValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"{len(errors)} validation error(s)")

    def __str__(self) -> str:
        return "\n".join(f"  - {e}" for e in self.errors)


def _load_yaml(path: Path) -> dict | list:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_schema_question_ids(schema_dir: Path) -> dict[str, dict]:
    """Load intake_schema.yaml → {question_id: {allowed_values, allows_free_text, ...}}"""
    path = schema_dir / "intake_schema.yaml"
    if not path.exists():
        return {}
    data = _load_yaml(path)
    out = {}
    for q in data:
        qid = q.get("id")
        if qid:
            out[qid] = q
    return out


def load_fixture(fixture_dir: str | Path, schema_dir: Optional[str | Path] = None) -> Fixture:
    """Load and validate a customer fixture from disk.

    Raises FixtureValidationError with all errors aggregated.
    """
    fixture_dir = Path(fixture_dir)
    if schema_dir is None:
        schema_dir = fixture_dir.parent.parent / "schema"
    else:
        schema_dir = Path(schema_dir)

    errors: list[str] = []

    # ── Required files ────────────────────────────────────────────────────
    required = {
        "company_profile.yaml": "company profile",
        "contradictions.yaml": "contradictions",
        "expected_outputs.yaml": "expected outputs",
        "forbidden.yaml": "forbidden list",
    }
    # At least one intake file
    has_intake = (fixture_dir / "intake.yaml").exists() or (fixture_dir / "intake_answers.yaml").exists()
    if not has_intake:
        errors.append("Missing intake file: need intake.yaml or intake_answers.yaml")

    for fname, desc in required.items():
        if not (fixture_dir / fname).exists():
            errors.append(f"Missing required file: {fname} ({desc})")

    # ── Load each file ────────────────────────────────────────────────────
    company_profile = None
    try:
        raw = _load_yaml(fixture_dir / "company_profile.yaml")
        # Strip internal-only keys
        if isinstance(raw, dict):
            raw.pop("_persona", None)
        company_profile = CompanyProfile(**raw)
    except Exception as e:
        errors.append(f"company_profile.yaml: {e}")

    # Intake — prefer intake.yaml (has rationale), fallback intake_answers.yaml
    intake: list[IntakeAnswer] = []
    intake_file = "intake.yaml" if (fixture_dir / "intake.yaml").exists() else "intake_answers.yaml"
    try:
        raw_intake = _load_yaml(fixture_dir / intake_file)
        for i, item in enumerate(raw_intake or []):
            if not isinstance(item, dict):
                continue
            # Normalize question_id
            qid = item.get("question_id") or item.get("id")
            if qid:
                item["question_id"] = qid
                item.setdefault("id", qid)
            try:
                intake.append(IntakeAnswer(**item))
            except Exception as e:
                errors.append(f"{intake_file}[{i}]: {e}")
    except Exception as e:
        errors.append(f"{intake_file}: {e}")

    # Evidence artifacts
    evidence: list[EvidenceArtifact] = []
    ev_file = fixture_dir / "evidence_artifacts.yaml"
    if ev_file.exists():
        try:
            raw_ev = _load_yaml(ev_file)
            items = raw_ev.get("artifacts", raw_ev) if isinstance(raw_ev, dict) else raw_ev
            for i, item in enumerate(items or []):
                try:
                    evidence.append(EvidenceArtifact(**item))
                except Exception as e:
                    errors.append(f"evidence_artifacts.yaml[{i}]: {e}")
        except Exception as e:
            errors.append(f"evidence_artifacts.yaml: {e}")

    # Contradictions
    contradictions: list[Contradiction] = []
    try:
        raw_c = _load_yaml(fixture_dir / "contradictions.yaml")
        items = raw_c.get("contradictions", raw_c) if isinstance(raw_c, dict) else raw_c
        for i, item in enumerate(items or []):
            try:
                contradictions.append(Contradiction(**item))
            except Exception as e:
                errors.append(f"contradictions.yaml[{i}]: {e}")
    except Exception as e:
        errors.append(f"contradictions.yaml: {e}")

    # Expected outputs
    expected = None
    try:
        raw_eo = _load_yaml(fixture_dir / "expected_outputs.yaml")
        expected = ExpectedOutputs(**raw_eo)
    except Exception as e:
        errors.append(f"expected_outputs.yaml: {e}")

    # Forbidden
    forbidden = None
    try:
        raw_f = _load_yaml(fixture_dir / "forbidden.yaml")
        forbidden = ForbiddenList(**raw_f)
    except Exception as e:
        errors.append(f"forbidden.yaml: {e}")

    # Evidence content (*.md files)
    evidence_content: dict[str, str] = {}
    ev_dir = fixture_dir / "evidence"
    if ev_dir.exists():
        for md in sorted(ev_dir.glob("*.md")):
            evidence_content[md.name] = md.read_text(encoding="utf-8")

    # ── Cross-file validation ─────────────────────────────────────────────
    schema_questions = _load_schema_question_ids(schema_dir)

    if schema_questions and intake:
        for ans in intake:
            qid = ans.question_id or ans.id
            if qid and qid not in schema_questions:
                errors.append(f"intake: question_id '{qid}' not in schema")

    if company_profile and forbidden:
        tools = {
            company_profile.identity_provider,
            company_profile.email_platform,
            company_profile.edr_product,
            company_profile.firewall_product,
            company_profile.siem_product,
            company_profile.backup_solution,
            company_profile.training_tool,
        }
        tools_lower = {t.lower() for t in tools if t}
        for ft in forbidden.forbidden_tools:
            if ft.lower() in tools_lower:
                errors.append(f"Persona conflict: '{ft}' in both company_profile.tools and forbidden_tools")

    if errors:
        raise FixtureValidationError(errors)

    return Fixture(
        company_profile=company_profile,
        intake=intake,
        evidence_artifacts=evidence,
        contradictions=contradictions,
        expected_outputs=expected or ExpectedOutputs(),
        forbidden=forbidden or ForbiddenList(),
        evidence_content=evidence_content,
    )
