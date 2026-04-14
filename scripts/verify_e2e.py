"""
scripts/verify_e2e.py

Automated end-to-end verification of the Intranest pipeline:
  reset → login → onboarding → intake context → generate docs → scan.

Phases (all against local backend http://localhost:8001):
  0. Reset demo org via scripts/reset_demo_data.py
  1. Login as admin@intranest.ai, capture JWT
  2. POST /api/onboarding/complete with the full Apex profile
  3. Verify the intake-context build picks up every tool-stack field
  4. POST /api/documents/regenerate-all — all 7 templates
  5. Fetch each doc and scan for hallucination patterns + org-term presence
  6. Print a summary matrix

Usage:
    python scripts/verify_e2e.py                      # full run (slow: ~8 min)
    python scripts/verify_e2e.py --skip-reset         # re-run without wiping
    python scripts/verify_e2e.py --skip-gen           # skip doc regen (fast)
    python scripts/verify_e2e.py --base-url URL       # target a different host
    python scripts/verify_e2e.py --verbose            # dump doc content per flag
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import textwrap
from typing import Optional

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from colorama import init as _colorama_init, Fore, Style
    _colorama_init()
    def _c(c: str, s: str) -> str: return f"{c}{s}{Style.RESET_ALL}"
except Exception:  # pragma: no cover
    class _F:
        RESET_ALL = CYAN = GREEN = YELLOW = RED = MAGENTA = BLUE = ""
    Fore = Style = _F()  # type: ignore
    def _c(_c, s): return s

import requests


# ── Config ──────────────────────────────────────────────────────────────────

DEMO_ORG_ID = "9de53b587b23450b87af"
ADMIN_EMAIL = "admin@intranest.ai"
ADMIN_PASSWORD = "Intranest2026!"

# Expected canonical answers once onboarding + intake map Apex values.
EXPECTED_FIELDS = [
    # (field in intake-context dict, substring that must appear)
    ("identity_provider", "Entra"),
    ("email_platform",    "GCC High"),
    ("edr_tool",          "CrowdStrike"),
    ("firewall",          "Palo Alto"),
    ("siem",              "Sentinel"),
    ("backup_tool",       "Veeam"),
    ("training_tool",     "KnowBe4"),
]

# Doc templates known to the engine (7 types). shared_responsibility_matrix
# is conditional on GCC-family email platform — Apex uses GCC High so it fires.
EXPECTED_DOC_TYPES = {
    "integrated_security_policy",
    "incident_response_plan",
    "config_management_plan",
    "risk_assessment_report",
    "training_program",
    "scope_package",
    "shared_responsibility_matrix",
}

ORG_TERMS_EXPECTED = [
    "Apex Defense", "Columbia", "CrowdStrike", "Entra",
    "Sentinel", "Palo Alto", "Veeam", "KnowBe4", "GCC High",
]

# Hallucination patterns — some are hard fails (placeholder / DEFAULTS bleed),
# others are warnings (IPs may be legit in a network description).
#
# Only truly unique DEFAULTS strings count as FAIL. Values like
# "Identity Provider", "Firewall", "SIEM", "Email Platform", "Backup Solution"
# are common English technical terms that legitimately appear in any
# security document (e.g. "Palo Alto Networks firewall management"),
# so flagging them causes false positives. We keep them as WARN instead.
FAIL_PATTERNS = [
    ("placeholder_token",
     r"\[(INSERT|TBD|ORGANIZATION NAME|COMPANY)[^\]]*\]|\{(company_name|org_name|tenant)[^}]*\}|\{\{[^}]+\}\}"),
    # These two DEFAULTS strings have no natural English use — seeing
    # them means the context fallback bled through to the LLM.
    ("default_bleed",
     r"\b(Security Awareness Training Tool|Endpoint Protection Tool)\b"),
]

WARN_PATTERNS = [
    ("phantom_evidence_ref", r"\bEVD-\d+\b|See Artifact:\s*|Artifact:\s*EVD"),
    ("fabricated_ip",        r"\b(?:10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)\b"),
    ("fabricated_hostname",  r"\b(?:SERVER|DC|FS|DB|WEB|APP|MAIL|FILE)-?\d{1,3}\b"),
    ("fabricated_version",   r"\bv?\d+\.\d+\.\d+\.\d+\b"),
    ("registry_key",         r"(HKLM|HKEY_LOCAL_MACHINE|HKCU|HKEY_CURRENT_USER)\\\\"),
    # Common DEFAULTS terms — legitimate as English nouns but worth noting
    # so a human can eyeball whether they're being used as real labels
    # (PASS) or as values (FAIL — context didn't reach the prompt).
    ("common_default_term",
     r"\b(Identity Provider|Email Platform|Backup Solution)\b"),
]


# ── Helpers ─────────────────────────────────────────────────────────────────

def hr(msg: str, color=None) -> None:
    line = "=" * 70
    if color is not None:
        print(_c(color, line))
        print(_c(color, msg))
        print(_c(color, line))
    else:
        print(line); print(msg); print(line)


def die(msg: str) -> None:
    print(_c(Fore.RED, f"FATAL: {msg}"))
    sys.exit(1)


def _excerpt(text: str, match: re.Match, pad: int = 40) -> str:
    start = max(0, match.start() - pad)
    end = min(len(text), match.end() + pad)
    return text[start:end].replace("\n", " ")


class Client:
    def __init__(self, base: str):
        self.base = base.rstrip("/")
        self.token: Optional[str] = None

    def _hdrs(self) -> dict:
        h = {"Accept": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def post(self, path: str, **kw) -> requests.Response:
        return requests.post(self.base + path, headers={**self._hdrs(), **kw.pop("headers", {})}, **kw)

    def get(self, path: str, **kw) -> requests.Response:
        return requests.get(self.base + path, headers={**self._hdrs(), **kw.pop("headers", {})}, **kw)


# ── Phases ──────────────────────────────────────────────────────────────────

def phase_reset() -> tuple[bool, str]:
    """Phase 0 — run reset script. Returns (ok, message)."""
    script = os.path.join(_PROJECT_ROOT, "scripts", "reset_demo_data.py")
    try:
        res = subprocess.run(
            [sys.executable, script],
            capture_output=True, text=True, cwd=_PROJECT_ROOT, timeout=120,
        )
    except Exception as exc:
        return False, f"reset script failed to invoke: {exc}"
    if res.returncode != 0:
        return False, f"reset exited {res.returncode}\n{res.stdout}\n{res.stderr}"

    # Verify evidence is actually empty + audit has just the genesis row.
    try:
        from sqlalchemy import create_engine, text
        from configs.settings import DATABASE_URL
        eng = create_engine(DATABASE_URL)
        with eng.connect() as conn:
            ev = conn.execute(
                text("SELECT COUNT(*) FROM evidence_artifacts WHERE org_id=:o"),
                {"o": DEMO_ORG_ID},
            ).scalar()
            au = conn.execute(text("SELECT COUNT(*) FROM audit_log")).scalar()
            ob = conn.execute(
                text("SELECT onboarding_complete FROM users WHERE email=:e"),
                {"e": ADMIN_EMAIL},
            ).scalar()
    except Exception as exc:
        return False, f"post-reset DB check failed: {exc}"

    if ev != 0:
        return False, f"expected 0 evidence, got {ev}"
    if au != 1:
        return False, f"expected 1 audit row (genesis), got {au}"
    if ob is not False:
        return False, f"expected admin.onboarding_complete=False, got {ob}"
    return True, f"evidence={ev} audit={au} admin.onboarding={ob}"


def phase_login(client: Client) -> tuple[bool, str]:
    form = {"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    try:
        r = requests.post(
            client.base + "/api/auth/login",
            data=form,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
    except Exception as exc:
        return False, f"login connect error: {exc}"
    if r.status_code != 200:
        return False, f"login HTTP {r.status_code}: {r.text[:200]}"
    try:
        tok = r.json()["access_token"]
    except Exception:
        return False, f"login response missing access_token: {r.text[:200]}"
    client.token = tok
    return True, f"got token len={len(tok)}"


def phase_onboarding(client: Client) -> tuple[bool, str]:
    body = {
        "organization": {
            "name": "Apex Defense Solutions",
            "city": "Columbia",
            "state": "MD",
            "employee_count": 45,
            "system_name": "Apex Secure Enclave",
        },
        "tech_stack": {
            "identity_provider": "Microsoft Entra ID",
            "mfa_enabled": True,
            "email_platform":   "Microsoft 365 GCC High",
            "edr_tool":         "CrowdStrike Falcon",
            "firewall":         "Palo Alto Networks",  # matches option in m0_firewall
            "siem":             "Microsoft Sentinel",
            "backup_tool":      "Veeam Backup & Replication",
            "training_tool":    "KnowBe4",
        },
        "cui_types": [
            "Controlled Technical Information (CTI)",
            "ITAR-controlled data",
        ],
    }
    try:
        r = client.post("/api/onboarding/complete", json=body, timeout=30)
    except Exception as exc:
        return False, f"onboarding connect error: {exc}"
    if r.status_code not in (200, 201):
        return False, f"onboarding HTTP {r.status_code}: {r.text[:300]}"
    data = r.json()
    if not data.get("success"):
        return False, f"onboarding non-success: {data}"
    saved = data.get("responses_saved", 0)
    # Expect 10 — 9 originals + m0_training_tool. Allow >= 10 for future adds.
    ok = saved >= 10
    return ok, f"responses_saved={saved} session_id={data.get('session_id')}"


def phase_context() -> tuple[bool, int, list[str]]:
    """Phase 3 — run the context builder directly and verify key fields."""
    from src.documents.intake_context import get_intake_context
    ctx = get_intake_context(DEMO_ORG_ID)
    results: list[str] = []
    passes = 0
    for key, expected in EXPECTED_FIELDS:
        val = str(ctx.get(key, "") or "")
        ok = expected.lower() in val.lower()
        if ok:
            passes += 1
            results.append(_c(Fore.GREEN, f"  PASS ") + f"{key:<20} contains {expected!r} (value={val!r})")
        else:
            results.append(_c(Fore.RED, f"  FAIL ") + f"{key:<20} missing {expected!r} (value={val!r})")
    return passes == len(EXPECTED_FIELDS), passes, results


def phase_generate(client: Client, skip: bool) -> tuple[bool, int, list[dict]]:
    """Phase 4 — generate all docs, then list them. Returns (ok, count, docs)."""
    if not skip:
        try:
            # Expect ~400s; pad the timeout.
            r = client.post("/api/documents/regenerate-all", timeout=900)
        except Exception as exc:
            return False, 0, [{"error": f"regenerate-all connect error: {exc}"}]
        if r.status_code != 200:
            return False, 0, [{"error": f"regenerate-all HTTP {r.status_code}: {r.text[:300]}"}]

    # Pull the list after generation.
    try:
        listing = client.get("/api/documents").json()
    except Exception as exc:
        return False, 0, [{"error": f"list docs error: {exc}"}]
    docs = listing.get("documents", [])
    seen_types = {d.get("doc_type") for d in docs}
    missing = EXPECTED_DOC_TYPES - seen_types
    extra = seen_types - EXPECTED_DOC_TYPES
    ok = not missing
    summary: list[dict] = docs
    if missing:
        summary.insert(0, {"error": f"missing doc types: {sorted(missing)}"})
    if extra:
        summary.insert(0, {"note": f"unexpected doc types (ignored): {sorted(extra)}"})
    return ok, len(docs), summary


def _fetch_doc(client: Client, doc_id: str) -> Optional[dict]:
    try:
        r = client.get(f"/api/documents/{doc_id}", timeout=30)
    except Exception:
        return None
    if r.status_code != 200:
        return None
    return r.json()


def phase_hallucination_scan(client: Client, docs: list[dict], verbose: bool) -> tuple[str, list[dict]]:
    """Scan every doc's sections; return (overall_status, per_doc_findings)."""
    per_doc: list[dict] = []
    total_fails = 0
    total_warns = 0
    total_org_terms = 0

    for d in docs:
        if "error" in d or "note" in d:
            continue
        doc_id = d.get("id")
        doc_type = d.get("doc_type") or "<unknown>"
        full = _fetch_doc(client, doc_id) if doc_id else None
        if not full:
            per_doc.append({
                "doc_type": doc_type, "error": "could not fetch document content"
            })
            continue

        # Collect text from every section body.
        body_parts = []
        for s in full.get("sections", []) or []:
            body_parts.append(str(s.get("title", "")))
            body_parts.append(str(s.get("content", "")))
        text_blob = "\n".join(body_parts)
        word_count = len(text_blob.split())

        fails: list[dict] = []
        for label, pat in FAIL_PATTERNS:
            for m in re.finditer(pat, text_blob, flags=re.IGNORECASE):
                fails.append({"type": label, "match": m.group(0),
                              "excerpt": _excerpt(text_blob, m)})
        warns: list[dict] = []
        for label, pat in WARN_PATTERNS:
            for m in re.finditer(pat, text_blob):
                warns.append({"type": label, "match": m.group(0),
                              "excerpt": _excerpt(text_blob, m)})

        org_hits = {term: text_blob.lower().count(term.lower()) for term in ORG_TERMS_EXPECTED}
        org_hit_count = sum(1 for v in org_hits.values() if v > 0)

        total_fails += len(fails)
        total_warns += len(warns)
        total_org_terms += org_hit_count

        per_doc.append({
            "doc_type": doc_type,
            "doc_id": doc_id,
            "word_count": word_count,
            "fails": fails,
            "warns": warns,
            "org_hits": org_hits,
            "org_hit_count": org_hit_count,
        })

        label = _c(Fore.CYAN, f"  {doc_type:<33}")
        status = (
            _c(Fore.RED, "FAIL") if fails
            else _c(Fore.YELLOW, "WARN") if warns
            else _c(Fore.GREEN, "OK  ")
        )
        print(f"{label} {status}  words={word_count:>5}  "
              f"org_terms={org_hit_count}/{len(ORG_TERMS_EXPECTED)}  "
              f"fails={len(fails)} warns={len(warns)}")

        if verbose or fails or warns:
            for f in fails[:3]:
                print(_c(Fore.RED, f"      FAIL {f['type']}: …{f['excerpt']}…"))
            for w in warns[:3]:
                print(_c(Fore.YELLOW, f"      WARN {w['type']}: …{w['excerpt']}…"))
            if fails and len(fails) > 3:
                print(_c(Fore.RED, f"      …and {len(fails) - 3} more FAILs"))

    if total_fails > 0:
        status = "FAIL"
    elif total_warns > 0:
        status = "WARN"
    else:
        status = "PASS"
    print()
    print(_c(Fore.CYAN,
             f"  total fails={total_fails} warns={total_warns} "
             f"org_terms_total={total_org_terms}"))
    return status, per_doc


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8001")
    parser.add_argument("--skip-reset", action="store_true",
                        help="Don't wipe the demo org first.")
    parser.add_argument("--skip-gen", action="store_true",
                        help="Skip regenerate-all — inspect existing docs only.")
    parser.add_argument("--verbose", action="store_true",
                        help="Dump doc content excerpts around every flag.")
    args = parser.parse_args()

    client = Client(args.base_url)

    results: dict[str, dict] = {}

    # Phase 0
    hr("Phase 0 — Reset demo data", Fore.CYAN)
    if args.skip_reset:
        results["reset"] = {"status": "SKIP", "detail": "--skip-reset"}
        print(_c(Fore.YELLOW, "  SKIPPED (--skip-reset)"))
    else:
        ok, msg = phase_reset()
        results["reset"] = {"status": "PASS" if ok else "FAIL", "detail": msg}
        print(_c(Fore.GREEN if ok else Fore.RED, f"  {'PASS' if ok else 'FAIL'}: {msg}"))

    print()
    # Phase 1
    hr("Phase 1 — Authenticate", Fore.CYAN)
    ok, msg = phase_login(client)
    results["auth"] = {"status": "PASS" if ok else "FAIL", "detail": msg}
    print(_c(Fore.GREEN if ok else Fore.RED, f"  {'PASS' if ok else 'FAIL'}: {msg}"))
    if not ok:
        _summary(results); return 1

    print()
    # Phase 2
    hr("Phase 2 — Onboarding", Fore.CYAN)
    ok, msg = phase_onboarding(client)
    results["onboarding"] = {"status": "PASS" if ok else "FAIL", "detail": msg}
    print(_c(Fore.GREEN if ok else Fore.RED, f"  {'PASS' if ok else 'FAIL'}: {msg}"))
    if not ok:
        _summary(results); return 1

    print()
    # Phase 3
    hr("Phase 3 — Intake context", Fore.CYAN)
    ok, passes, lines = phase_context()
    results["context"] = {"status": "PASS" if ok else "FAIL",
                          "detail": f"{passes}/{len(EXPECTED_FIELDS)} fields"}
    for line in lines:
        print(line)
    print()
    print(_c(Fore.GREEN if ok else Fore.RED,
             f"  {'PASS' if ok else 'FAIL'}: {passes}/{len(EXPECTED_FIELDS)} fields verified"))

    print()
    # Phase 4
    hr("Phase 4 — Generate all documents" + (" (SKIPPED)" if args.skip_gen else ""), Fore.CYAN)
    ok, count, docs = phase_generate(client, args.skip_gen)
    results["generate"] = {"status": "PASS" if ok else "FAIL",
                           "detail": f"{count}/7 docs"}
    print(_c(Fore.GREEN if ok else Fore.RED,
             f"  {'PASS' if ok else 'FAIL'}: {count}/7 documents"))

    print()
    # Phase 5
    hr("Phase 5 — Hallucination scan", Fore.CYAN)
    status, per_doc = phase_hallucination_scan(client, docs, args.verbose)
    results["scan"] = {"status": status, "detail": f"{len(per_doc)} docs scanned"}

    # Summary matrix
    print()
    return _summary(results)


def _summary(results: dict) -> int:
    hr("Final summary", Fore.MAGENTA)
    overall_ok = True
    order = ["reset", "auth", "onboarding", "context", "generate", "scan"]
    labels = {
        "reset": "Reset         ",
        "auth":  "Auth          ",
        "onboarding": "Onboarding    ",
        "context": "Intake Context",
        "generate": "Doc Generation",
        "scan":   "Halluc. Scan  ",
    }
    for key in order:
        entry = results.get(key, {"status": "N/A", "detail": "(phase did not run)"})
        st = entry["status"]
        colour = {
            "PASS": Fore.GREEN, "FAIL": Fore.RED,
            "WARN": Fore.YELLOW, "SKIP": Fore.YELLOW, "N/A": Fore.YELLOW,
        }.get(st, "")
        print(f"  {labels[key]}  {_c(colour, st):<22} {entry['detail']}")
        if st == "FAIL":
            overall_ok = False

    print()
    if overall_ok and all(r.get("status") in ("PASS", "SKIP") for r in results.values()):
        print(_c(Fore.GREEN, "OVERALL: PASS"))
        return 0
    if any(r.get("status") == "FAIL" for r in results.values()):
        print(_c(Fore.RED, "OVERALL: FAIL"))
        return 1
    print(_c(Fore.YELLOW, "OVERALL: NEEDS REVIEW"))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(_c(Fore.RED, "\nInterrupted."))
        sys.exit(130)
