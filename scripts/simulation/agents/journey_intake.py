"""Stage 2: Post 135 intake answers, verify contradictions fire."""
from __future__ import annotations

import time

from scripts.simulation.agents.api_client import ApiClient
from scripts.simulation.agents.assertions import AssertionRecorder
from scripts.simulation.loader.schemas import Fixture


def run_intake(api: ApiClient, fixture: Fixture, recorder: AssertionRecorder,
               session_id: str) -> None:
    answers = fixture.intake
    if not answers:
        recorder.expect("intake.has_answers", False, detail="No intake answers in fixture")
        return

    # ── Post all answers in batches of 10 ──
    saved_count = 0
    errors = []
    for i in range(0, len(answers), 10):
        batch = answers[i:i + 10]
        payload = {
            "answers": [
                {
                    "question_id": a.question_id or a.id,
                    "module_id": a.module,
                    "control_ids": a.controls or [],
                    "answer_type": "single_choice",
                    "answer_value": a.answer_value,
                    "answer_details": None,
                }
                for a in batch
            ]
        }
        r = api.post(f"/api/intake/sessions/{session_id}/responses", json=payload)
        if r.ok:
            saved_count += r.json().get("saved", 0)
        else:
            errors.append(f"Batch {i//10}: {r.status_code} {r.text[:200]}")

    recorder.expect("intake.all_135_saved",
                    saved_count >= len(answers),
                    actual=saved_count, expected=len(answers),
                    detail="; ".join(errors[:3]) if errors else "")

    # ── Wait for contradiction engine ──
    time.sleep(3)

    # ── Fetch contradictions ──
    r = api.get("/api/contradictions")
    contradictions = r.json() if r.ok else []
    if isinstance(contradictions, dict):
        contradictions = contradictions.get("items", contradictions.get("contradictions", []))
    if not isinstance(contradictions, list):
        contradictions = []

    triggered_rules = {c.get("rule_id") for c in contradictions if c.get("status") == "OPEN"}

    recorder.expect("intake.contradictions.triggered_count",
                    len(triggered_rules) >= 1,
                    actual=len(triggered_rules),
                    detail=f"Rules: {sorted(triggered_rules)}")

    # ── Assert required intake-layer contradictions ──
    expected = fixture.expected_outputs
    if expected and expected.intake_contradictions_must_catch:
        must = expected.intake_contradictions_must_catch
        for rule_id in must.required:
            full_rule = f"CONTRADICTION_{rule_id}"
            recorder.expect(
                f"intake.contradictions.{rule_id}_triggered",
                full_rule in triggered_rules,
                actual=sorted(triggered_rules),
                expected=full_rule,
            )
        for rule_id in (must.likely_also or []):
            full_rule = f"CONTRADICTION_{rule_id}"
            if full_rule in triggered_rules:
                recorder.warn(f"intake.contradictions.{rule_id}_likely",
                              detail=f"Diagnostic: {full_rule} triggered (expected)")
            else:
                recorder.warn(f"intake.contradictions.{rule_id}_likely",
                              detail=f"Diagnostic: {full_rule} NOT triggered (acceptable)")

    # ── Warn on unexpected criticals ──
    expected_rules = set()
    if expected and expected.intake_contradictions_must_catch:
        for r_id in (expected.intake_contradictions_must_catch.required +
                     expected.intake_contradictions_must_catch.likely_also +
                     expected.intake_contradictions_must_catch.diagnostic_bonus):
            expected_rules.add(f"CONTRADICTION_{r_id}")

    unexpected_criticals = [
        c for c in contradictions
        if c.get("status") == "OPEN"
        and c.get("severity", "").upper() == "CRITICAL"
        and c.get("rule_id") not in expected_rules
    ]
    if unexpected_criticals:
        recorder.warn("intake.contradictions.no_unexpected_criticals",
                      detail=f"Unexpected CRITICAL rules: {[c.get('rule_id') for c in unexpected_criticals]}",
                      actual=len(unexpected_criticals))
