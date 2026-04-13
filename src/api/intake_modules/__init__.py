"""
src/api/intake_modules/__init__.py

Dynamic intake module registry. Submodules named ``module*.py`` (e.g.
``module0_foundation.py``) are auto-imported at package load time. Each
submodule ends with ``register_module(...)`` so its questions become
available via ``get_module()`` / ``get_all_modules()``.

Python 3.11: use ``Optional[X]`` rather than ``X | None`` for dataclass
defaults (PEP 604 at field declarations still interacts oddly with
``field(default=None)`` on some 3.11 patches).
"""
from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass, field
from typing import Optional


# ── Tier / type constants (string values the DB + frontend already use) ──


class QuestionTier:
    SCREENING = "screening"
    CONTROL_STATUS = "control_status"
    OBJECTIVE_CHECKLIST = "objective_checklist"
    EVIDENCE_VALIDATION = "evidence_validation"
    CONTRADICTION = "contradiction"


class QuestionType:
    SINGLE_CHOICE = "single_choice"
    MULTI_CHOICE = "multi_choice"
    # Legacy alias — Module 0 data was stored as "multiple_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"
    YES_NO = "yes_no"
    # Legacy alias — Module 0 data was stored as "yes_no_unsure"
    YES_NO_UNSURE = "yes_no_unsure"
    CHECKLIST = "checklist"
    NUMBER = "number"


# ── Dataclasses ───────────────────────────────────────────────────────────


@dataclass
class IntakeQuestion:
    id: str
    text: str
    question_type: str
    tier: str
    section: str
    required: bool = True
    help_text: Optional[str] = None
    # Options may be list[str] (Module 0 shape) or list[dict] (Module 1
    # shape with value/label/gap/severity keys). Left untyped for that
    # reason — the DB and the frontend already handle both shapes.
    options: Optional[list] = None
    control_id: Optional[str] = None
    depends_on: Optional[dict] = None
    placeholder: Optional[str] = None
    weight: Optional[int] = None
    # Extensions for the existing data / save_responses logic:
    control_ids: list = field(default_factory=list)
    # Free-form bag for Module 0's ``branch`` / Module 1's ``branching``
    # and ``skip_to``. Keys are spread into the top level of to_dict() so
    # save_responses() keeps finding them exactly where it did before.
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "text": self.text,
            "question_type": self.question_type,
            # Legacy alias — existing frontend + save_responses reads this:
            "answer_type": self.question_type,
            "tier": self.tier,
            "section": self.section,
            "required": self.required,
            "help_text": self.help_text,
            "help": self.help_text,  # legacy alias
            "options": self.options,
            "control_id": self.control_id,
            "control_ids": self.control_ids,
            "depends_on": self.depends_on,
            "placeholder": self.placeholder,
            "weight": self.weight,
        }
        # Spread metadata (branch / branching / skip_to / flag / …) so that
        # save_responses()'s existing .get("branch") / .get("branching") /
        # .get("options") calls keep working unchanged.
        for k, v in self.metadata.items():
            d[k] = v
        return d


@dataclass
class ModuleDefinition:
    number: int
    name: str
    description: str
    families: list
    control_ids: list = field(default_factory=list)
    estimated_minutes: int = 15
    questions: list = field(default_factory=list)
    doc_templates: list = field(default_factory=list)

    @property
    def control_count(self) -> int:
        return len(self.control_ids)

    @property
    def question_count(self) -> int:
        return len(self.questions)

    @property
    def sections(self) -> list:
        seen: list = []
        for q in self.questions:
            if q.section and q.section not in seen:
                seen.append(q.section)
        return seen

    def to_summary(self) -> dict:
        return {
            "number": self.number,
            "name": self.name,
            "description": self.description,
            "families": self.families,
            "control_ids": self.control_ids,
            "control_count": self.control_count,
            "question_count": self.question_count,
            "estimated_minutes": self.estimated_minutes,
            "sections": self.sections,
            "doc_templates": self.doc_templates,
        }

    def to_full(self) -> dict:
        return {
            **self.to_summary(),
            "questions": [q.to_dict() for q in self.questions],
        }


# ── Registry ──────────────────────────────────────────────────────────────


_REGISTRY: dict = {}  # {number: ModuleDefinition}


def register_module(module: ModuleDefinition) -> None:
    _REGISTRY[module.number] = module


def get_module(number: int) -> Optional[ModuleDefinition]:
    return _REGISTRY.get(number)


def get_all_modules() -> list:
    return [_REGISTRY[n] for n in sorted(_REGISTRY)]


def get_module_count() -> int:
    return len(_REGISTRY)


def find_question(question_id: str) -> Optional[IntakeQuestion]:
    """Locate a question across all registered modules. Used by save_responses."""
    for mod in _REGISTRY.values():
        for q in mod.questions:
            if q.id == question_id:
                return q
    return None


# ── Auto-discovery of submodules ──────────────────────────────────────────


def _auto_discover() -> None:
    """Import every ``module*.py`` in this package so their register_module()
    calls run. Subpackages are skipped."""
    for _finder, mod_name, is_pkg in pkgutil.iter_modules(__path__):
        if is_pkg or not mod_name.startswith("module"):
            continue
        importlib.import_module(f"{__name__}.{mod_name}")


_auto_discover()
