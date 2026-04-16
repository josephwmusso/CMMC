"""Sanity tests for fixture loader. Run: python -m scripts.simulation.loader.test_loader"""
from __future__ import annotations

import sys
import os
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.simulation.loader.fixture_loader import load_fixture, FixtureValidationError

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "meridian_aerospace"
SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schema"

passed = 0
failed = 0


def test(name: str, fn):
    global passed, failed
    try:
        fn()
        print(f"  PASS  {name}")
        passed += 1
    except Exception as e:
        print(f"  FAIL  {name}: {e}")
        failed += 1


def run():
    global passed, failed

    print("=== Fixture Loader Tests ===\n")

    # 1. Load succeeds
    fixture = [None]

    def t_load():
        fixture[0] = load_fixture(FIXTURE_DIR, SCHEMA_DIR)
    test("load_fixture(meridian) succeeds", t_load)

    f = fixture[0]
    if f is None:
        print("\nCANNOT CONTINUE — fixture failed to load")
        return

    # 2. Company profile
    test("company_profile.firewall == SonicWall",
         lambda: assert_eq(f.company_profile.firewall_product, "SonicWall"))
    test("company_profile.employee_count == 14",
         lambda: assert_eq(f.company_profile.employee_count, 14))
    test("company_profile.primary_location == Wichita, KS",
         lambda: assert_eq(f.company_profile.primary_location, "Wichita, KS"))

    # 3. Intake count
    test(f"intake count == 135 (got {len(f.intake)})",
         lambda: assert_eq(len(f.intake), 135))

    # 4. Evidence
    test(f"evidence_artifacts count == 8 (got {len(f.evidence_artifacts)})",
         lambda: assert_eq(len(f.evidence_artifacts), 8))

    # 5. Contradictions
    test(f"contradictions count == 4 (got {len(f.contradictions)})",
         lambda: assert_eq(len(f.contradictions), 4))

    # 6. Forbidden list populated
    test(f"forbidden_tools >= 20 (got {len(f.forbidden.forbidden_tools)})",
         lambda: assert_true(len(f.forbidden.forbidden_tools) >= 20))

    # 7. Evidence content loaded
    test(f"evidence_content files >= 8 (got {len(f.evidence_content)})",
         lambda: assert_true(len(f.evidence_content) >= 8))

    # 8. No persona conflict (tools not in forbidden)
    def t_no_conflict():
        tools = {f.company_profile.identity_provider, f.company_profile.firewall_product,
                 f.company_profile.edr_product, f.company_profile.email_platform}
        tools_lower = {t.lower() for t in tools if t}
        forbidden_lower = {ft.lower() for ft in f.forbidden.forbidden_tools}
        overlap = tools_lower & forbidden_lower
        assert not overlap, f"Overlap: {overlap}"
    test("no tool in both company_profile and forbidden", t_no_conflict)

    # 9. Deliberate corruption test
    def t_corrupt():
        import tempfile, shutil, yaml
        with tempfile.TemporaryDirectory() as tmp:
            # Copy fixture
            shutil.copytree(FIXTURE_DIR, Path(tmp) / "meridian_aerospace")
            corrupt_dir = Path(tmp) / "meridian_aerospace"
            # Corrupt intake_answers by adding bogus question_id
            answers_path = corrupt_dir / "intake_answers.yaml"
            if answers_path.exists():
                data = yaml.safe_load(answers_path.read_text(encoding="utf-8"))
                data.append({"id": "m99_bogus", "module": 99, "answer_value": "nope"})
                with open(answers_path, "w", encoding="utf-8") as fw:
                    yaml.dump(data, fw)
                # Remove intake.yaml so loader uses intake_answers.yaml
                (corrupt_dir / "intake.yaml").unlink(missing_ok=True)
                try:
                    load_fixture(corrupt_dir, SCHEMA_DIR)
                    raise AssertionError("Should have raised FixtureValidationError")
                except FixtureValidationError as e:
                    assert any("m99_bogus" in err for err in e.errors), f"Expected m99_bogus error, got: {e.errors}"
            else:
                raise AssertionError("intake_answers.yaml not found for corruption test")
    test("corrupt intake_answers → validation error mentions m99_bogus", t_corrupt)

    print(f"\n=== {passed} passed, {failed} failed ===")
    return failed == 0


def assert_eq(a, b):
    assert a == b, f"expected {b!r}, got {a!r}"


def assert_true(v):
    assert v, f"expected truthy, got {v!r}"


if __name__ == "__main__":
    ok = run()
    sys.exit(0 if ok else 1)
