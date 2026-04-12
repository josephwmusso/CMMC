"""
Intranest Pipeline E2E Smoke Test
Tests: Intake -> Document Generation -> Evidence -> SSP -> SPRS -> POA&M

Usage:
  python scripts/test_pipeline_e2e.py                    # local (localhost:8001)
  python scripts/test_pipeline_e2e.py --render           # Render (cmmc.onrender.com)
  python scripts/test_pipeline_e2e.py --base-url http://custom:port
  python scripts/test_pipeline_e2e.py --skip-llm         # Skip Claude API tests
"""
import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import requests

# Windows cp1252 stdout doesn't handle box-drawing / colors by default
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ORG_ID = "9de53b587b23450b87af"
DEFAULT_TIMEOUT = 30
LLM_TIMEOUT = 300  # SSP/doc gen can be slow (Render + Claude)

# ANSI colors
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BLUE = "\033[36m"
RESET = "\033[0m"
BOLD = "\033[1m"


# ─────────────────────────────────────────────────────────────
# Apex Defense Solutions demo data
# ─────────────────────────────────────────────────────────────

APEX_ANSWERS = {
    "m0_company_name": "Apex Defense Solutions",
    "m0_cage_code": "7X4K2",
    "m0_employee_count": "45",
    "m0_locations": "1",
    "m0_primary_location": "Columbia, MD",
    "m0_dfars_clause": "yes",
    "m0_cui_types": "Technical data (drawings, specs, test results)",
    "m0_cui_flow": "CUI is in cloud storage (SharePoint, OneDrive, etc.)",
    "m0_remote_workers": "yes",
    "m0_wireless": "yes",
    "m0_email_platform": "Microsoft 365 GCC High",
    "m0_identity_provider": "Microsoft Entra ID (Azure AD) with MFA",
    "m0_edr": "CrowdStrike Falcon",
    "m0_firewall": "Palo Alto Networks",
    "m0_siem": "Microsoft Sentinel",
    "m0_existing_docs": "System Security Plan (SSP)",
}

APEX_PROFILE = {
    "org_id": ORG_ID,
    "company_name": "Apex Defense Solutions",
    "cage_code": "7X4K2",
    "duns_number": "084571239",
    "employee_count": 45,
    "facility_count": 1,
    "primary_location": "Columbia, MD",
    "cui_types": ["Technical data", "ITAR-controlled data"],
    "cui_flow": "Cloud storage (SharePoint, OneDrive)",
    "has_remote_workers": True,
    "has_wireless": True,
    "identity_provider": "Microsoft Entra ID (Azure AD) with MFA",
    "email_platform": "Microsoft 365 GCC High",
    "email_tier": "E5",
    "edr_product": "CrowdStrike Falcon",
    "firewall_product": "Palo Alto Networks",
    "siem_product": "Microsoft Sentinel",
    "backup_solution": "Veeam Backup",
    "existing_ssp": True,
    "existing_poam": True,
    "prior_assessment": False,
    "dfars_7012_clause": True,
}


# ─────────────────────────────────────────────────────────────
# Test result tracking
# ─────────────────────────────────────────────────────────────

@dataclass
class TestResult:
    index: int
    name: str
    status: str  # PASS | FAIL | SKIP
    http_code: Optional[int] = None
    summary: str = ""
    error_detail: str = ""


class TestContext:
    """Shared state between tests."""
    def __init__(self, base_url: str, skip_llm: bool):
        self.base = base_url.rstrip("/")
        self.skip_llm = skip_llm
        self.results: list[TestResult] = []
        self.session_id: Optional[str] = None
        self.document_id: Optional[str] = None
        self.evidence_id: Optional[str] = None
        self.evidence_artifact_from_doc: Optional[str] = None

    def record(self, result: TestResult):
        self.results.append(result)
        # Print as we go
        color = {"PASS": GREEN, "FAIL": RED, "SKIP": YELLOW}[result.status]
        name_padded = result.name.ljust(44, ".")
        code = f"({result.http_code})" if result.http_code else ""
        print(f"[{result.index:2d}/20] {name_padded} {color}{result.status}{RESET} {code} {result.summary}")
        if result.error_detail:
            print(f"         {RED}{result.error_detail}{RESET}")


# ─────────────────────────────────────────────────────────────
# HTTP helper
# ─────────────────────────────────────────────────────────────

def request(method: str, url: str, timeout: int = DEFAULT_TIMEOUT, **kwargs) -> requests.Response:
    """Make HTTP request with consistent error handling."""
    return requests.request(method, url, timeout=timeout, **kwargs)


def summarize_error(resp: requests.Response) -> str:
    """Extract error detail from response."""
    try:
        data = resp.json()
        if isinstance(data, dict):
            return data.get("detail") or data.get("error") or data.get("message") or str(data)[:200]
        return str(data)[:200]
    except Exception:
        return resp.text[:200]


# ─────────────────────────────────────────────────────────────
# Individual tests
# ─────────────────────────────────────────────────────────────

def test_01_health(ctx: TestContext) -> TestResult:
    try:
        r = request("GET", f"{ctx.base}/health")
        if r.status_code != 200:
            return TestResult(1, "Health check", "FAIL", r.status_code, error_detail=summarize_error(r))
        data = r.json()
        if data.get("status") != "ok":
            return TestResult(1, "Health check", "FAIL", r.status_code, error_detail=f"Unexpected: {data}")
        return TestResult(1, "Health check", "PASS", r.status_code, f"version={data.get('version','?')}")
    except Exception as e:
        return TestResult(1, "Health check", "FAIL", None, error_detail=f"Connection error: {e}")


def test_02_create_session(ctx: TestContext) -> TestResult:
    try:
        r = request("POST", f"{ctx.base}/api/intake/sessions", json={"org_id": ORG_ID})
        if r.status_code not in (200, 201):
            return TestResult(2, "Create intake session", "FAIL", r.status_code, error_detail=summarize_error(r))
        data = r.json()
        ctx.session_id = data.get("session_id")
        if not ctx.session_id:
            return TestResult(2, "Create intake session", "FAIL", r.status_code, error_detail="No session_id in response")
        return TestResult(2, "Create intake session", "PASS", r.status_code, f"session_id={ctx.session_id[:12]}...")
    except Exception as e:
        return TestResult(2, "Create intake session", "FAIL", None, error_detail=str(e))


def test_03_submit_module0(ctx: TestContext) -> TestResult:
    if not ctx.session_id:
        return TestResult(3, "Submit Module 0 responses", "SKIP", None, "No session_id from Test 2")
    try:
        answers = []
        for qid, value in APEX_ANSWERS.items():
            # Determine answer_type from question id patterns
            if qid in ("m0_employee_count", "m0_locations"):
                answer_type = "number"
            elif qid in ("m0_company_name", "m0_cage_code", "m0_primary_location"):
                answer_type = "text"
            elif qid in ("m0_dfars_clause", "m0_remote_workers", "m0_wireless"):
                answer_type = "yes_no_unsure"
            else:
                answer_type = "multiple_choice"
            answers.append({
                "question_id": qid,
                "module_id": 0,
                "control_ids": [],
                "answer_type": answer_type,
                "answer_value": value,
            })
        r = request("POST", f"{ctx.base}/api/intake/sessions/{ctx.session_id}/responses",
                    json={"answers": answers})
        if r.status_code != 200:
            return TestResult(3, "Submit Module 0 responses", "FAIL", r.status_code, error_detail=summarize_error(r))
        data = r.json()
        saved = data.get("saved", 0)
        gaps = data.get("progress", {}).get("gaps", 0)
        return TestResult(3, "Submit Module 0 responses", "PASS", r.status_code,
                          f"{saved} answers saved, {gaps} gaps flagged")
    except Exception as e:
        return TestResult(3, "Submit Module 0 responses", "FAIL", None, error_detail=str(e))


def test_04_save_company_profile(ctx: TestContext) -> TestResult:
    try:
        r = request("POST", f"{ctx.base}/api/intake/company-profile", json=APEX_PROFILE)
        if r.status_code != 200:
            return TestResult(4, "Save company profile", "FAIL", r.status_code, error_detail=summarize_error(r))
        data = r.json()
        return TestResult(4, "Save company profile", "PASS", r.status_code,
                          f"profile_id={data.get('profile_id','?')[:12]}...")
    except Exception as e:
        return TestResult(4, "Save company profile", "FAIL", None, error_detail=str(e))


def test_05_get_company_profile(ctx: TestContext) -> TestResult:
    try:
        r = request("GET", f"{ctx.base}/api/intake/company-profile/{ORG_ID}")
        if r.status_code != 200:
            return TestResult(5, "Get company profile", "FAIL", r.status_code, error_detail=summarize_error(r))
        data = r.json()
        if data.get("company_name") != "Apex Defense Solutions":
            return TestResult(5, "Get company profile", "FAIL", r.status_code,
                              error_detail=f"Wrong company_name: {data.get('company_name')}")
        return TestResult(5, "Get company profile", "PASS", r.status_code,
                          f"company_name={data.get('company_name')}")
    except Exception as e:
        return TestResult(5, "Get company profile", "FAIL", None, error_detail=str(e))


def test_06_list_templates(ctx: TestContext) -> TestResult:
    try:
        r = request("GET", f"{ctx.base}/api/documents/templates")
        if r.status_code != 200:
            return TestResult(6, "List document templates", "FAIL", r.status_code, error_detail=summarize_error(r))
        data = r.json()
        templates = data.get("templates", data) if isinstance(data, dict) else data
        count = len(templates) if isinstance(templates, list) else 0
        if count < 7:
            return TestResult(6, "List document templates", "FAIL", r.status_code,
                              error_detail=f"Expected 7 templates, got {count}")
        return TestResult(6, "List document templates", "PASS", r.status_code, f"{count} templates")
    except Exception as e:
        return TestResult(6, "List document templates", "FAIL", None, error_detail=str(e))


def test_07_generate_document(ctx: TestContext) -> TestResult:
    if ctx.skip_llm:
        return TestResult(7, "Generate document (LLM)", "SKIP", None, "--skip-llm flag")
    # Try integrated_security_policy first (seeded template)
    doc_type = "integrated_security_policy"
    try:
        r = request("POST", f"{ctx.base}/api/documents/generate/{doc_type}", timeout=LLM_TIMEOUT)
        if r.status_code != 200:
            return TestResult(7, "Generate document (LLM)", "FAIL", r.status_code, error_detail=summarize_error(r))
        data = r.json()
        ctx.document_id = data.get("doc_id")
        ctx.evidence_artifact_from_doc = data.get("evidence_artifact_id")
        wc = data.get("word_count", 0)
        return TestResult(7, "Generate document (LLM)", "PASS", r.status_code,
                          f"doc_id={str(ctx.document_id)[:12]}..., {wc} words")
    except Exception as e:
        return TestResult(7, "Generate document (LLM)", "FAIL", None, error_detail=str(e))


def test_08_list_documents(ctx: TestContext) -> TestResult:
    try:
        r = request("GET", f"{ctx.base}/api/documents")
        if r.status_code != 200:
            return TestResult(8, "List generated documents", "FAIL", r.status_code, error_detail=summarize_error(r))
        data = r.json()
        docs = data.get("documents", data) if isinstance(data, dict) else data
        count = len(docs) if isinstance(docs, list) else 0
        return TestResult(8, "List generated documents", "PASS", r.status_code, f"{count} documents")
    except Exception as e:
        return TestResult(8, "List generated documents", "FAIL", None, error_detail=str(e))


def test_09_list_evidence(ctx: TestContext) -> TestResult:
    try:
        r = request("GET", f"{ctx.base}/api/evidence/?limit=100")
        if r.status_code != 200:
            return TestResult(9, "List evidence artifacts", "FAIL", r.status_code, error_detail=summarize_error(r))
        data = r.json()
        artifacts = data.get("artifacts", data) if isinstance(data, dict) else data
        count = len(artifacts) if isinstance(artifacts, list) else data.get("count", 0)
        # Grab an artifact ID for transition tests — prefer DRAFT
        if artifacts:
            draft_artifact = next((a for a in artifacts if a.get("state") == "DRAFT"), None)
            ctx.evidence_id = (draft_artifact or artifacts[0]).get("id")
        # Fallback to artifact created by document generation
        if not ctx.evidence_id and ctx.evidence_artifact_from_doc:
            ctx.evidence_id = ctx.evidence_artifact_from_doc
        detail = f"{count} artifacts"
        if ctx.evidence_id:
            detail += f", test_id={ctx.evidence_id[:12]}..."
        return TestResult(9, "List evidence artifacts", "PASS", r.status_code, detail)
    except Exception as e:
        return TestResult(9, "List evidence artifacts", "FAIL", None, error_detail=str(e))


def _transition(ctx: TestContext, new_state: str) -> requests.Response:
    # NOTE: transition endpoint uses QUERY PARAMS, not JSON body
    return request("POST",
                   f"{ctx.base}/api/evidence/{ctx.evidence_id}/transition",
                   params={"new_state": new_state, "comment": "e2e smoke test"})


def test_10_transition_reviewed(ctx: TestContext) -> TestResult:
    if not ctx.evidence_id:
        return TestResult(10, "Evidence DRAFT->REVIEWED", "SKIP", None, "No evidence_id available")
    try:
        r = _transition(ctx, "REVIEWED")
        if r.status_code != 200:
            return TestResult(10, "Evidence DRAFT->REVIEWED", "FAIL", r.status_code, error_detail=summarize_error(r))
        return TestResult(10, "Evidence DRAFT->REVIEWED", "PASS", r.status_code, "transitioned")
    except Exception as e:
        return TestResult(10, "Evidence DRAFT->REVIEWED", "FAIL", None, error_detail=str(e))


def test_11_transition_approved(ctx: TestContext) -> TestResult:
    if not ctx.evidence_id:
        return TestResult(11, "Evidence REVIEWED->APPROVED", "SKIP", None, "No evidence_id available")
    try:
        r = _transition(ctx, "APPROVED")
        if r.status_code != 200:
            return TestResult(11, "Evidence REVIEWED->APPROVED", "FAIL", r.status_code, error_detail=summarize_error(r))
        return TestResult(11, "Evidence REVIEWED->APPROVED", "PASS", r.status_code, "transitioned")
    except Exception as e:
        return TestResult(11, "Evidence REVIEWED->APPROVED", "FAIL", None, error_detail=str(e))


def test_12_transition_published(ctx: TestContext) -> TestResult:
    if not ctx.evidence_id:
        return TestResult(12, "Evidence APPROVED->PUBLISHED", "SKIP", None, "No evidence_id available")
    try:
        r = _transition(ctx, "PUBLISHED")
        if r.status_code != 200:
            return TestResult(12, "Evidence APPROVED->PUBLISHED", "FAIL", r.status_code, error_detail=summarize_error(r))
        return TestResult(12, "Evidence APPROVED->PUBLISHED", "PASS", r.status_code, "immutable + hashed")
    except Exception as e:
        return TestResult(12, "Evidence APPROVED->PUBLISHED", "FAIL", None, error_detail=str(e))


def test_13_verify_hash(ctx: TestContext) -> TestResult:
    if not ctx.evidence_id:
        return TestResult(13, "Verify published evidence has hash", "SKIP", None, "No evidence_id")
    try:
        r = request("GET", f"{ctx.base}/api/evidence/{ctx.evidence_id}")
        if r.status_code != 200:
            return TestResult(13, "Verify published evidence has hash", "FAIL", r.status_code,
                              error_detail=summarize_error(r))
        data = r.json()
        state = data.get("state")
        hash_val = data.get("sha256_hash") or data.get("file_hash") or data.get("hash")
        if state != "PUBLISHED":
            return TestResult(13, "Verify published evidence has hash", "FAIL", r.status_code,
                              error_detail=f"State is {state}, expected PUBLISHED")
        if not hash_val:
            return TestResult(13, "Verify published evidence has hash", "FAIL", r.status_code,
                              error_detail="No SHA-256 hash on published artifact")
        return TestResult(13, "Verify published evidence has hash", "PASS", r.status_code,
                          f"hash={hash_val[:16]}..., state=PUBLISHED")
    except Exception as e:
        return TestResult(13, "Verify published evidence has hash", "FAIL", None, error_detail=str(e))


def test_14_sprs_score(ctx: TestContext) -> TestResult:
    try:
        r = request("GET", f"{ctx.base}/api/scoring/sprs")
        if r.status_code != 200:
            return TestResult(14, "Get SPRS score", "FAIL", r.status_code, error_detail=summarize_error(r))
        data = r.json()
        score = data.get("score", "?")
        met = data.get("met", "?")
        return TestResult(14, "Get SPRS score", "PASS", r.status_code, f"score={score}, met={met}")
    except Exception as e:
        return TestResult(14, "Get SPRS score", "FAIL", None, error_detail=str(e))


def test_15_generate_ssp_single(ctx: TestContext) -> TestResult:
    if ctx.skip_llm:
        return TestResult(15, "Generate SSP for one control (LLM)", "SKIP", None, "--skip-llm flag")
    try:
        r = request("POST", f"{ctx.base}/api/ssp/generate",
                    json={"control_id": "AC.L2-3.1.1"}, timeout=LLM_TIMEOUT)
        if r.status_code != 200:
            return TestResult(15, "Generate SSP for one control (LLM)", "FAIL", r.status_code,
                              error_detail=summarize_error(r))
        data = r.json()
        if data.get("error"):
            return TestResult(15, "Generate SSP for one control (LLM)", "FAIL", r.status_code,
                              error_detail=data["error"])
        narrative_len = len(data.get("narrative", ""))
        gen_time = data.get("generation_time_sec", 0)
        return TestResult(15, "Generate SSP for one control (LLM)", "PASS", r.status_code,
                          f"{narrative_len} chars in {gen_time}s")
    except Exception as e:
        return TestResult(15, "Generate SSP for one control (LLM)", "FAIL", None, error_detail=str(e))


def test_16_ssp_narrative(ctx: TestContext) -> TestResult:
    try:
        r = request("GET", f"{ctx.base}/api/ssp/narrative/AC.L2-3.1.1")
        if r.status_code == 404:
            return TestResult(16, "Get SSP narrative (AC.L2-3.1.1)", "FAIL", r.status_code,
                              error_detail="No narrative found — SSP generation may have failed silently")
        if r.status_code != 200:
            return TestResult(16, "Get SSP narrative (AC.L2-3.1.1)", "FAIL", r.status_code,
                              error_detail=summarize_error(r))
        data = r.json()
        narrative = data.get("narrative") or ""
        if not narrative or len(narrative) < 50:
            return TestResult(16, "Get SSP narrative (AC.L2-3.1.1)", "FAIL", r.status_code,
                              error_detail=f"Narrative too short or empty ({len(narrative)} chars)")
        return TestResult(16, "Get SSP narrative (AC.L2-3.1.1)", "PASS", r.status_code,
                          f"{len(narrative)} chars")
    except Exception as e:
        return TestResult(16, "Get SSP narrative (AC.L2-3.1.1)", "FAIL", None, error_detail=str(e))


def test_17_overview(ctx: TestContext) -> TestResult:
    try:
        r = request("GET", f"{ctx.base}/api/scoring/overview")
        if r.status_code != 200:
            return TestResult(17, "Get compliance overview", "FAIL", r.status_code, error_detail=summarize_error(r))
        data = r.json()
        sprs = data.get("sprs", {})
        met = sprs.get("met", "?")
        partial = sprs.get("partial", "?")
        not_met = sprs.get("not_met", "?")
        return TestResult(17, "Get compliance overview", "PASS", r.status_code,
                          f"met={met}, partial={partial}, not_met={not_met}")
    except Exception as e:
        return TestResult(17, "Get compliance overview", "FAIL", None, error_detail=str(e))


def test_18_generate_poam(ctx: TestContext) -> TestResult:
    try:
        r = request("POST", f"{ctx.base}/api/scoring/poam/generate")
        if r.status_code != 200:
            return TestResult(18, "Generate POA&M items", "FAIL", r.status_code, error_detail=summarize_error(r))
        data = r.json()
        if data.get("error"):
            return TestResult(18, "Generate POA&M items", "FAIL", r.status_code, error_detail=data["error"])
        created = data.get("created", 0)
        skipped = data.get("skipped", 0)
        return TestResult(18, "Generate POA&M items", "PASS", r.status_code,
                          f"{created} created, {skipped} skipped")
    except Exception as e:
        return TestResult(18, "Generate POA&M items", "FAIL", None, error_detail=str(e))


def test_19_poam_summary(ctx: TestContext) -> TestResult:
    try:
        r = request("GET", f"{ctx.base}/api/scoring/poam")
        if r.status_code != 200:
            return TestResult(19, "Get POA&M summary", "FAIL", r.status_code, error_detail=summarize_error(r))
        data = r.json()
        items = data.get("items", [])
        total = data.get("total_items", len(items))
        return TestResult(19, "Get POA&M summary", "PASS", r.status_code, f"{total} items")
    except Exception as e:
        return TestResult(19, "Get POA&M summary", "FAIL", None, error_detail=str(e))


def test_20_audit_chain(ctx: TestContext) -> TestResult:
    try:
        r = request("GET", f"{ctx.base}/api/evidence/audit/verify")
        if r.status_code != 200:
            return TestResult(20, "Verify audit chain integrity", "FAIL", r.status_code,
                              error_detail=summarize_error(r))
        data = r.json()
        valid = data.get("valid")
        entries = data.get("entries_checked", "?")
        if valid is not True:
            return TestResult(20, "Verify audit chain integrity", "FAIL", r.status_code,
                              error_detail=f"Chain invalid: first_broken={data.get('first_broken')}")
        return TestResult(20, "Verify audit chain integrity", "PASS", r.status_code,
                          f"chain valid, {entries} entries")
    except Exception as e:
        return TestResult(20, "Verify audit chain integrity", "FAIL", None, error_detail=str(e))


# ─────────────────────────────────────────────────────────────
# Test runner
# ─────────────────────────────────────────────────────────────

TESTS = [
    test_01_health,
    test_02_create_session,
    test_03_submit_module0,
    test_04_save_company_profile,
    test_05_get_company_profile,
    test_06_list_templates,
    test_07_generate_document,
    test_08_list_documents,
    test_09_list_evidence,
    test_10_transition_reviewed,
    test_11_transition_approved,
    test_12_transition_published,
    test_13_verify_hash,
    test_14_sprs_score,
    test_15_generate_ssp_single,
    test_16_ssp_narrative,
    test_17_overview,
    test_18_generate_poam,
    test_19_poam_summary,
    test_20_audit_chain,
]


def run_all(ctx: TestContext) -> int:
    print(f"\n{BOLD}{BLUE}================================================================{RESET}")
    print(f"{BOLD}{BLUE}  INTRANEST PIPELINE E2E SMOKE TEST{RESET}")
    print(f"{BOLD}{BLUE}================================================================{RESET}")
    print(f"Base URL: {ctx.base}")
    print(f"Skip LLM: {ctx.skip_llm}")
    print()

    for test in TESTS:
        ctx.record(test(ctx))

    # Summary
    passed = sum(1 for r in ctx.results if r.status == "PASS")
    failed = sum(1 for r in ctx.results if r.status == "FAIL")
    skipped = sum(1 for r in ctx.results if r.status == "SKIP")

    print()
    print(f"{BOLD}================================================================{RESET}")
    print(f"{BOLD}PIPELINE SMOKE TEST RESULTS{RESET}")
    print(f"{BOLD}================================================================{RESET}")
    print(f"{GREEN}PASS: {passed}{RESET}  {RED}FAIL: {failed}{RESET}  {YELLOW}SKIP: {skipped}{RESET}")
    print(f"Total: {len(ctx.results)}")

    failures = [r for r in ctx.results if r.status == "FAIL"]
    if failures:
        print(f"\n{RED}{BOLD}FAILURES:{RESET}")
        for r in failures:
            print(f"  [{r.index}] {r.name} — {r.http_code or 'no-response'}: {r.error_detail}")

    # Next steps based on failures
    if failures:
        print(f"\n{YELLOW}{BOLD}NEXT STEPS:{RESET}")
        for r in failures:
            if r.index == 1:
                print(f"  - Backend not reachable at {ctx.base} — is it running?")
            elif r.index in (2, 3):
                print(f"  - Intake endpoint broken — check src/api/intake_routes.py")
            elif r.index in (4, 5):
                print(f"  - Company profile endpoint broken — check request body shape")
            elif r.index == 6:
                print(f"  - Document templates not seeded — run scripts/init_document_engine_db.py")
            elif r.index == 7:
                print(f"  - Document generation broken — likely LLM or context loading issue")
            elif r.index == 8:
                print(f"  - Document listing broken")
            elif r.index == 9:
                print(f"  - Evidence listing broken or document generation didn't create artifact")
            elif r.index in (10, 11, 12):
                print(f"  - Evidence state transition broken — check state_machine.py")
            elif r.index == 13:
                print(f"  - Published evidence missing hash — check hasher.py integration")
            elif r.index == 14:
                print(f"  - SPRS scoring broken — check scoring/sprs.py")
            elif r.index in (15, 16):
                print(f"  - SSP generation broken — check ssp_generator_v2.py + Claude API key")
            elif r.index == 17:
                print(f"  - Overview endpoint broken — check scoring_routes.py /overview")
            elif r.index in (18, 19):
                print(f"  - POA&M generation broken — check scoring/poam.py")
            elif r.index == 20:
                print(f"  - Audit chain broken — run scripts/fix_audit_chain.py (if exists)")

    print(f"{BOLD}================================================================{RESET}")
    return 0 if failed == 0 else 1


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="E2E pipeline smoke test")
    parser.add_argument("--render", action="store_true",
                        help="Test against Render (cmmc.onrender.com)")
    parser.add_argument("--base-url", default=None,
                        help="Custom base URL (overrides --render)")
    parser.add_argument("--skip-llm", action="store_true",
                        help="Skip Claude-backed tests (doc gen, SSP gen)")
    args = parser.parse_args()

    if args.base_url:
        base = args.base_url
    elif args.render:
        base = "https://cmmc.onrender.com"
    else:
        base = "http://localhost:8001"

    ctx = TestContext(base, args.skip_llm)
    return run_all(ctx)


if __name__ == "__main__":
    sys.exit(main())
