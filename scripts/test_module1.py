"""
scripts/test_module1.py
Integration test for Module 1 (Access Control) intake questions.

Usage:
    python scripts/test_module1.py
"""

import sys
import requests

BASE = "http://localhost:8001/api/intake"
ORG_ID = "9de53b587b23450b87af"

passed = 0
failed = 0
total = 0


def check(name, condition, detail=""):
    global passed, failed, total
    total += 1
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name}{' - ' + detail if detail else ''}")


def main():
    print("=" * 60)
    print("MODULE 1 INTEGRATION TEST")
    print("=" * 60)

    # ── Step 0: Create session ──
    print("\n--- Session Setup ---\n")
    try:
        r = requests.post(f"{BASE}/sessions", json={"org_id": ORG_ID}, timeout=5)
        check("Session created", r.status_code == 200, f"HTTP {r.status_code}")
        sess = r.json()
        session_id = sess["session_id"]
        print(f"  Session ID: {session_id}")
    except Exception as e:
        print(f"  FATAL: Cannot connect to backend at {BASE} - {e}")
        print("  Make sure uvicorn is running on port 8001.")
        sys.exit(1)

    # ── Step 1: Load Module 1 questions ──
    print("\n--- Step 1: Load Module 1 Questions ---\n")
    r = requests.get(f"{BASE}/sessions/{session_id}/module/1", timeout=5)
    check("Module 1 endpoint returns 200", r.status_code == 200, f"HTTP {r.status_code}")

    mod = r.json()
    questions = mod.get("questions", [])
    check("Module 1 title is 'Access Control'", "Access Control" in mod.get("title", ""), mod.get("title", ""))
    check("28 questions returned", len(questions) == 28, f"got {len(questions)}")
    check("Module status is not 'not_available'", mod.get("status") != "not_available")

    # Also load Module 0 to verify it still works
    r0 = requests.get(f"{BASE}/sessions/{session_id}/module/0", timeout=5)
    mod0 = r0.json()
    check("Module 0 still returns questions", len(mod0.get("questions", [])) == 16, f"got {len(mod0.get('questions', []))}")

    # ── Step 2: Control coverage ──
    print("\n--- Step 2: AC Control Coverage ---\n")
    all_ac = {f"AC.L2-3.1.{i}" for i in range(1, 23)}
    covered = set()
    for q in questions:
        for cid in q.get("control_ids", []):
            covered.add(cid)

    check("All 22 AC controls covered", all_ac.issubset(covered), f"missing: {all_ac - covered}" if not all_ac.issubset(covered) else "")
    check(f"Covered controls count: {len(covered & all_ac)}/22", len(covered & all_ac) == 22)

    # ── Step 3: Schema integrity ──
    print("\n--- Step 3: Schema Integrity ---\n")

    VALID_SECTIONS = {"account_management", "login_session", "remote_access", "wireless_mobile", "external_cui_flow"}
    VALID_ANSWER_TYPES = {"single_choice", "multi_choice"}
    VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM"}

    required_fields = {"id", "module", "section", "control_ids", "question", "answer_type", "options", "branching", "help_text"}
    schema_errors = []

    for q in questions:
        qid = q.get("id", "?")

        # Required fields
        missing = required_fields - set(q.keys())
        if missing:
            schema_errors.append(f"{qid}: missing fields {missing}")

        # Module must be 1
        if q.get("module") != 1:
            schema_errors.append(f"{qid}: module is {q.get('module')}, expected 1")

        # Valid section
        if q.get("section") not in VALID_SECTIONS:
            schema_errors.append(f"{qid}: invalid section '{q.get('section')}'")

        # Valid answer type
        if q.get("answer_type") not in VALID_ANSWER_TYPES:
            schema_errors.append(f"{qid}: invalid answer_type '{q.get('answer_type')}'")

        # Options validation
        options = q.get("options", [])
        if not options:
            schema_errors.append(f"{qid}: no options")
        for opt in options:
            if not isinstance(opt, dict):
                schema_errors.append(f"{qid}: option is not a dict: {opt}")
                continue
            if "value" not in opt or "label" not in opt:
                schema_errors.append(f"{qid}: option missing value/label: {opt}")
            if opt.get("gap") and opt.get("severity") and opt["severity"] not in VALID_SEVERITIES:
                schema_errors.append(f"{qid}: invalid severity '{opt['severity']}'")

        # control_ids must be a list
        if not isinstance(q.get("control_ids", []), list):
            schema_errors.append(f"{qid}: control_ids is not a list")

    check(f"All 28 questions have required fields", len(schema_errors) == 0,
          f"{len(schema_errors)} error(s): {'; '.join(schema_errors[:5])}" if schema_errors else "")

    # Count gap options
    gap_options = sum(1 for q in questions for o in q.get("options", []) if isinstance(o, dict) and o.get("gap"))
    check(f"Gap options found: {gap_options}", gap_options > 0, "no gap options detected")

    # ── Step 4: Branching targets ──
    print("\n--- Step 4: Branching Targets ---\n")

    question_ids = {q["id"] for q in questions}
    branching_errors = []

    for q in questions:
        branching = q.get("branching", {})
        for answer_val, branch_action in branching.items():
            if isinstance(branch_action, dict) and "skip_to" in branch_action:
                target = branch_action["skip_to"]
                if target not in question_ids:
                    branching_errors.append(f"{q['id']}: skip_to '{target}' does not exist")

    check("All skip_to targets reference valid question IDs",
          len(branching_errors) == 0,
          "; ".join(branching_errors) if branching_errors else "")

    # Count branching rules
    alerts = sum(1 for q in questions for b in q.get("branching", {}).values()
                 if isinstance(b, dict) and "alert" in b)
    skips = sum(1 for q in questions for b in q.get("branching", {}).values()
                if isinstance(b, dict) and "skip_to" in b)
    check(f"Branching rules: {alerts} alerts, {skips} skip_to", alerts > 0 or skips > 0)

    # ── Step 5: Submit a test response ──
    print("\n--- Step 5: Save Test Response ---\n")

    test_answer = {
        "answers": [{
            "question_id": "m1_q01",
            "module_id": 1,
            "control_ids": ["AC.L2-3.1.1"],
            "answer_type": "single_choice",
            "answer_value": "formal_process",
        }]
    }

    r = requests.post(f"{BASE}/sessions/{session_id}/responses", json=test_answer, timeout=5)
    check("Response saved (HTTP 200)", r.status_code == 200, f"HTTP {r.status_code}")

    result = r.json()
    check("Response confirms save", result.get("saved", 0) >= 1, f"saved={result.get('saved')}")
    check("Progress updated", result.get("progress", {}).get("answered", 0) >= 1)

    # Test gap-triggering answer
    gap_answer = {
        "answers": [{
            "question_id": "m1_q08",
            "module_id": 1,
            "control_ids": ["AC.L2-3.1.7"],
            "answer_type": "single_choice",
            "answer_value": "yes_local_admin",
        }]
    }

    r2 = requests.post(f"{BASE}/sessions/{session_id}/responses", json=gap_answer, timeout=5)
    result2 = r2.json()
    has_flag = len(result2.get("flags", [])) > 0
    check("Gap-triggering answer produces flag", has_flag,
          f"flags={result2.get('flags')}" if not has_flag else "")

    # ── Summary ──
    print(f"\n{'='*60}")
    print(f"RESULTS: {passed}/{total} passed, {failed} failed")
    print(f"{'='*60}")
    print(f"\n  Questions: {len(questions)}/28")
    print(f"  Controls: {len(covered & all_ac)}/22")
    print(f"  Schema errors: {len(schema_errors)}")
    print(f"  Branching errors: {len(branching_errors)}")
    print(f"  Gap options: {gap_options}")
    print(f"  Alert rules: {alerts}")
    print(f"  Skip rules: {skips}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
