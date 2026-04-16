"""Hallucination detector tests. Run: python -m scripts.simulation.detectors.test_detector"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.simulation.loader.fixture_loader import load_fixture
from scripts.simulation.detectors.hallucination_detector import detect

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "meridian_aerospace"
SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schema"

passed = 0
failed = 0


def test(name, fn):
    global passed, failed
    try:
        fn()
        print(f"  PASS  {name}")
        passed += 1
    except Exception as e:
        print(f"  FAIL  {name}: {e}")
        failed += 1


def _grounding():
    """Mock grounding universe matching Meridian's actual stack."""
    return {
        "tools": ["Google Identity", "Google Workspace", "SonicWall",
                   "Microsoft Defender Antivirus", "Google Drive", "Google Forms"],
        "company_terms": ["Meridian Aerospace Components, LLC", "Meridian",
                          "Wichita, KS", "Wichita", "KS"],
        "evidence_titles": ["Employee Handbook v4.2", "Acceptable Use Policy",
                            "Incident Response Procedures", "Visitor Access Log",
                            "Google Workspace Admin Screenshot", "Network Diagram",
                            "Annual Security Training Record", "Vendor List"],
        "evidence_free_text": (
            "sonicwall tz370 google workspace 2-step verification synology nas "
            "microsoft defender antivirus google drive google forms vsdx network diagram "
            "visitor access log employee handbook acceptable use policy"
        ),
    }


def _forbidden():
    f = load_fixture(FIXTURE_DIR, SCHEMA_DIR)
    d = {
        "forbidden_tools": f.forbidden.forbidden_tools,
        "forbidden_ip_ranges": {"allowed_cidr": "192.168.10.0/24"},
        "allowed_hostnames": f.forbidden.allowed_hostnames,
        "allowed_evidence_titles": f.forbidden.allowed_evidence_titles,
        "forbidden_facts": {
            "employee_count_other_than": 14,
        },
        "date_constraints": {
            "earliest_allowed": "2023-01-01",
            "latest_allowed": "2026-04-15",
        },
        "_known_plugin_ids": ["42873", "81606", "15901", "10107", "57608",
                               "84502", "97737", "153953", "10884", "10860",
                               "96982", "58453"],
        "_known_cves": ["CVE-2017-0144", "CVE-2017-0145"],
    }
    return d


def run():
    global passed, failed
    print("=== Hallucination Detector Tests ===\n")

    g = _grounding()
    f = _forbidden()

    # 1. Clean sample — uses only Meridian's real tools
    def t_clean():
        text = (
            "Meridian Aerospace Components employs Google Identity for centralized "
            "authentication across all 14 employees in Wichita, KS. The SonicWall TZ370 "
            "firewall enforces boundary protection with deny-by-default policies. "
            "Microsoft Defender Antivirus provides real-time malware scanning on all "
            "Windows endpoints. Per the Employee Handbook v4.2, all users must complete "
            "annual security awareness training administered via Google Forms."
        )
        r = detect(text, artifact_id="clean_test", grounding_universe=g, forbidden=f)
        assert r.severity == "clean", f"Expected clean, got {r.severity}: {[h.entity for h in r.hits]}"
    test("clean sample → severity: clean", t_clean)

    # 2. Forbidden tool
    def t_forbidden_tool():
        text = "We use CrowdStrike Falcon for endpoint detection and response."
        r = detect(text, artifact_id="t2", grounding_universe=g, forbidden=f)
        cats = [h.category for h in r.hits]
        assert "FORBIDDEN_TOOL" in cats, f"Expected FORBIDDEN_TOOL, got {cats}"
        assert r.severity == "violations"
    test("forbidden tool (CrowdStrike) → violation", t_forbidden_tool)

    # 3. Bad IP
    def t_bad_ip():
        text = "The server at 10.0.0.5 hosts the CUI repository."
        r = detect(text, artifact_id="t3", grounding_universe=g, forbidden=f)
        cats = [h.category for h in r.hits]
        assert "BAD_IP" in cats, f"Expected BAD_IP, got {cats}"
    test("bad IP (10.0.0.5) → violation", t_bad_ip)

    # 4. Bad hostname
    def t_bad_hostname():
        text = "Connect to dc-primary-01 for domain authentication."
        r = detect(text, artifact_id="t4", grounding_universe=g, forbidden=f)
        cats = [h.category for h in r.hits]
        assert "BAD_HOSTNAME" in cats, f"Expected BAD_HOSTNAME, got {cats}"
    test("bad hostname (dc-primary-01) → warning", t_bad_hostname)

    # 5. Fabricated plugin ID
    def t_bad_plugin():
        text = "Nessus scan identified plugin 999999 on the host."
        r = detect(text, artifact_id="t5", grounding_universe=g, forbidden=f)
        cats = [h.category for h in r.hits]
        assert "FABRICATED_CITATION" in cats, f"Expected FABRICATED_CITATION, got {cats}"
    test("fabricated plugin (999999) → violation", t_bad_plugin)

    # 6. Known plugin ID — should NOT flag
    def t_known_plugin():
        text = "Nessus scan identified plugin 153953 showing legacy auth is enabled."
        r = detect(text, artifact_id="t6", grounding_universe=g, forbidden=f)
        plugin_hits = [h for h in r.hits if h.category == "FABRICATED_CITATION" and "153953" in h.entity]
        assert len(plugin_hits) == 0, f"Known plugin 153953 falsely flagged: {plugin_hits}"
    test("known plugin (153953) → no flag", t_known_plugin)

    # 7. Wrong employee count
    def t_wrong_count():
        text = "The organization employs 45 employees across its facilities."
        r = detect(text, artifact_id="t7", grounding_universe=g, forbidden=f)
        cats = [h.category for h in r.hits]
        assert "EMPLOYEE_COUNT_WRONG" in cats, f"Expected EMPLOYEE_COUNT_WRONG, got {cats}"
    test("wrong employee count (45 vs 14) → violation", t_wrong_count)

    # 8. Future date
    def t_future_date():
        text = "The policy was last reviewed on 2028-01-15 by the ISSM."
        r = detect(text, artifact_id="t8", grounding_universe=g, forbidden=f)
        cats = [h.category for h in r.hits]
        assert "DATE_OUT_OF_RANGE" in cats, f"Expected DATE_OUT_OF_RANGE, got {cats}"
    test("future date (2028-01-15) → violation", t_future_date)

    # 9. Allowed IP — should NOT flag
    def t_allowed_ip():
        text = "The file server at 192.168.10.20 stores CUI data."
        r = detect(text, artifact_id="t9", grounding_universe=g, forbidden=f)
        ip_hits = [h for h in r.hits if h.category == "BAD_IP"]
        assert len(ip_hits) == 0, f"Allowed IP falsely flagged: {ip_hits}"
    test("allowed IP (192.168.10.20) → no flag", t_allowed_ip)

    print(f"\n=== {passed} passed, {failed} failed ===")
    return failed == 0


if __name__ == "__main__":
    ok = run()
    sys.exit(0 if ok else 1)
