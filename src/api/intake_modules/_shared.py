"""
src/api/intake_modules/_shared.py

Helpers shared by the CONTROL_STATUS-style modules 2-8. Not picked up by
_auto_discover (leading underscore).

The "status" question template is uniform across modules 2-8: one
single-choice question per NIST 800-171 control with the five standard
implementation-state options. Each module supplies its own hand-written
help_text referencing the demo-org tool stack
(Entra ID, M365 GCC High, CrowdStrike Falcon, Palo Alto PA-450,
Sentinel, Veeam, KnowBe4).
"""
from typing import Optional

from src.api.intake_modules import IntakeQuestion, QuestionTier, QuestionType


STATUS_OPTIONS = [
    "Fully implemented",
    "Partially implemented",
    "Planned",
    "Not implemented",
    "Not applicable",
]


HIGH_WEIGHT_WARNING = (
    "\u26a0\ufe0f High-weight control (5 SPRS points). This is among the "
    "most impactful controls for your score.\n\n"
)


def status_q(
    module_num: int,
    family_abbrev: str,
    nist_id: str,
    control_id: str,
    title: str,
    section: str,
    points: int,
    help_text: str,
    high_weight_flag: bool = False,
) -> IntakeQuestion:
    """Build a CONTROL_STATUS question for one NIST 800-171 control."""
    qid = f"m{module_num}_{family_abbrev.lower()}_{nist_id}_status"
    body = (HIGH_WEIGHT_WARNING if high_weight_flag else "") + help_text
    return IntakeQuestion(
        id=qid,
        text=f"What is your current implementation state for {control_id} — {title}?",
        question_type=QuestionType.SINGLE_CHOICE,
        tier=QuestionTier.CONTROL_STATUS,
        section=section,
        required=True,
        help_text=body,
        options=list(STATUS_OPTIONS),
        control_id=control_id,
        control_ids=[control_id],
        weight=points,
    )


def followup_q(
    module_num: int,
    family_abbrev: str,
    nist_id: str,
    suffix: str,
    text: str,
    options: list,
    help_text: str,
    control_id: str,
    weight: int,
    parent_suffix: str = "status",
    parent_value: str = "Fully implemented",
) -> IntakeQuestion:
    """Build an OBJECTIVE_CHECKLIST follow-up gated on a status answer."""
    parent_qid = f"m{module_num}_{family_abbrev.lower()}_{nist_id}_{parent_suffix}"
    qid = f"m{module_num}_{family_abbrev.lower()}_{nist_id}_{suffix}"
    return IntakeQuestion(
        id=qid,
        text=text,
        question_type=QuestionType.SINGLE_CHOICE,
        tier=QuestionTier.OBJECTIVE_CHECKLIST,
        section="Follow-up",
        required=False,
        help_text=help_text,
        options=list(options),
        control_id=control_id,
        control_ids=[control_id],
        weight=weight,
        depends_on={"question_id": parent_qid, "value": parent_value},
    )
