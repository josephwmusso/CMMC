"""Stage 7: SSP narrative generation + per-control hallucination detection."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from scripts.simulation.agents.api_client import ApiClient
from scripts.simulation.agents.assertions import AssertionRecorder
from scripts.simulation.loader.schemas import Fixture

DEFAULT_CONTROLS = [
    "IA.L2-3.5.3",    # contradiction seed: MFA claim
    "SC.L2-3.13.11",  # contradiction seed: FIPS
    "AC.L2-3.1.5",    # contradiction seed: access reviews
    "SI.L2-3.14.1",   # contradiction seed: patching
    "AC.L2-3.1.1",    # clean baseline
]


def _build_org_profile(fixture: Fixture) -> dict:
    cp = fixture.company_profile
    tools = ", ".join(filter(None, [
        cp.identity_provider, cp.email_platform, cp.edr_product,
        cp.firewall_product, cp.siem_product, cp.backup_solution,
    ]))
    # OrgProfileInput is narrow — unknown keys are dropped by Pydantic.
    # use_demo_profile=True fills gaps from Apex's DEMO_ORG_PROFILE, but
    # we override org_name + tools_description + employee_count to ensure
    # the LLM prompt sees Meridian's identity and tool stack prominently.
    return {
        "org_name": cp.company_name,
        "system_name": cp.system_name or "CUI Network",
        "system_description": (
            f"{cp.company_name} is a {cp.employee_count}-employee defense subcontractor "
            f"located in {cp.primary_location}. "
            f"CUI types: {', '.join(cp.cui_types) if cp.cui_types else 'CTI'}."
        ),
        "employee_count": cp.employee_count,
        "facility_type": f"Single facility in {cp.primary_location}",
        "tools_description": (
            f"Identity: {cp.identity_provider or 'None'}. "
            f"Email: {cp.email_platform or 'None'}. "
            f"Endpoint protection: {cp.edr_product or 'None'}. "
            f"Firewall: {cp.firewall_product or 'None'}. "
            f"SIEM: {cp.siem_product or 'None'}. "
            f"Backup: {cp.backup_solution or 'None'}. "
            f"Training: {cp.training_tool or 'None'}."
        ),
        "network_description": (
            f"{cp.firewall_product or 'Firewall'} perimeter, "
            f"flat LAN 192.168.10.0/24, "
            f"{'wireless enabled' if cp.has_wireless else 'no wireless'}"
        ),
        "use_demo_profile": True,  # fills DEMO_ORG_PROFILE for keys not in OrgProfileInput
    }


def run_ssp(
    api: ApiClient, fixture: Fixture, recorder: AssertionRecorder,
    run_dir: Path, control_ids: Optional[list[str]] = None,
    skip_detector: bool = False, detector_strict: bool = False,
) -> dict:
    """Generate SSP for scoped controls, run detector on each. Returns {narratives}."""
    controls = control_ids or DEFAULT_CONTROLS
    org_profile = _build_org_profile(fixture)
    narratives: dict[str, str] = {}
    detector_reports: list[dict] = []

    ssp_dir = run_dir / "ssp" / "narratives"
    ssp_dir.mkdir(parents=True, exist_ok=True)
    det_dir = run_dir / "detector" / "ssp"
    det_dir.mkdir(parents=True, exist_ok=True)

    for cid in controls:
        # Generate
        r = api.post("/api/ssp/generate", json={
            "control_id": cid,
            "org_profile": org_profile,
        })
        if not r.ok:
            recorder.expect(f"ssp.{cid}.generated", False,
                            detail=f"Generation failed: {r.status_code} {r.text[:200]}")
            continue

        result = r.json()
        narrative = result.get("narrative", "")
        narratives[cid] = narrative

        (ssp_dir / f"{cid}.txt").write_text(narrative, encoding="utf-8")

        recorder.expect(f"ssp.{cid}.generated",
                        len(narrative) >= 200,
                        actual=len(narrative), expected=">=200 chars")

        if skip_detector or not narrative:
            continue

        # Grounding context
        gr = api.get(f"/api/truth/grounding-context/{cid}")
        grounding = gr.json().get("grounding_universe", {}) if gr.ok else {}

        # Detector
        from scripts.simulation.detectors.hallucination_detector import detect
        forbidden = _build_forbidden_dict(fixture)
        report = detect(
            text=narrative,
            artifact_id=f"ssp_section_{cid}",
            artifact_type="ssp_narrative",
            control_ids=[cid],
            grounding_universe=grounding,
            forbidden=forbidden,
        )

        det_path = det_dir / f"{cid}.json"
        with open(det_path, "w", encoding="utf-8") as f:
            json.dump({
                "artifact_id": report.artifact_id,
                "severity": report.severity,
                "summary": report.summary,
                "hits": [{"category": h.category, "severity": h.severity,
                          "entity": h.entity, "reason": h.reason}
                         for h in report.hits],
            }, f, indent=2)

        violations = [h for h in report.hits if h.severity == "violation"]
        forbidden_hits = [h for h in report.hits if h.category == "FORBIDDEN_TOOL"]
        bad_ips = [h for h in report.hits if h.category == "BAD_IP"]
        fab_cites = [h for h in report.hits if h.category == "FABRICATED_CITATION" and h.severity == "violation"]
        wrong_emp = [h for h in report.hits if h.category == "EMPLOYEE_COUNT_WRONG"]
        bad_dates = [h for h in report.hits if h.category == "DATE_OUT_OF_RANGE"]

        recorder.expect(f"ssp.{cid}.no_forbidden_tools", len(forbidden_hits) == 0,
                        actual=[h.entity for h in forbidden_hits])
        recorder.expect(f"ssp.{cid}.no_bad_ips", len(bad_ips) == 0,
                        actual=[h.entity for h in bad_ips])
        recorder.expect(f"ssp.{cid}.no_fabricated_citations", len(fab_cites) == 0,
                        actual=[h.entity for h in fab_cites])
        recorder.expect(f"ssp.{cid}.no_wrong_employee_count", len(wrong_emp) == 0,
                        actual=[h.entity for h in wrong_emp])
        recorder.expect(f"ssp.{cid}.no_out_of_range_dates", len(bad_dates) == 0,
                        actual=[h.entity for h in bad_dates])

        detector_reports.append({"control_id": cid, "severity": report.severity,
                                 "violations": len(violations)})

    # Aggregate
    all_violations = sum(r["violations"] for r in detector_reports)
    recorder.expect("ssp.all_clean", all_violations == 0,
                    actual=all_violations, detail="Total violations across all SSP narratives")

    return {"narratives": narratives, "detector_reports": detector_reports}


def _build_forbidden_dict(fixture: Fixture) -> dict:
    f = fixture.forbidden
    scan_plugin_ids = []
    scan_cves = []
    # Parse known plugin IDs from the Nessus fixture
    scan_dir = Path(__file__).resolve().parents[1] / "fixtures" / "meridian_aerospace" / "scans"
    nessus = scan_dir / "sample_scan.nessus"
    if nessus.exists():
        import re
        content = nessus.read_text(encoding="utf-8")
        scan_plugin_ids = re.findall(r'pluginID="(\d+)"', content)
        scan_cves = re.findall(r"<cve>(CVE-[\d-]+)</cve>", content)

    return {
        "forbidden_tools": f.forbidden_tools,
        "forbidden_ip_ranges": {
            "allowed_cidr": f.forbidden_ip_ranges.get("allowed_cidr", "192.168.10.0/24")
                            if f.forbidden_ip_ranges else "192.168.10.0/24",
        },
        "allowed_hostnames": f.allowed_hostnames,
        "allowed_evidence_titles": f.allowed_evidence_titles,
        "forbidden_facts": {
            "employee_count_other_than": f.forbidden_facts.employee_count_other_than
                                         if f.forbidden_facts else None,
        },
        "date_constraints": {
            "earliest_allowed": f.date_constraints.earliest_allowed if f.date_constraints else None,
            "latest_allowed": f.date_constraints.latest_allowed if f.date_constraints else None,
        },
        "_known_plugin_ids": scan_plugin_ids,
        "_known_cves": scan_cves,
    }
