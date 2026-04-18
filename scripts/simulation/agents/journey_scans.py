"""Stage 4: Nessus + CIS-CAT uploads, POA&M generation, baseline assertions."""
from __future__ import annotations

import io
from pathlib import Path

from scripts.simulation.agents.api_client import ApiClient
from scripts.simulation.agents.assertions import AssertionRecorder
from scripts.simulation.loader.schemas import Fixture


def _scan_config(fixture: Fixture) -> dict:
    eo = fixture.expected_outputs
    eo_dict = eo.model_dump() if eo else {}
    scans = eo_dict.get("scans", {})
    ness = scans.get("nessus", {})
    cis = scans.get("ciscat", {})
    return {
        "nessus_min_findings": ness.get("min_findings", 3),
        "nessus_max_findings": ness.get("max_findings", 50),
        "nessus_min_criticals": ness.get("min_criticals", 0),
        "nessus_required_plugins": [str(p) for p in ness.get("required_plugin_ids", [])],
        "nessus_min_poam_items": ness.get("min_poam_items", 0),
        "ciscat_pct_min": cis.get("compliance_pct_min", 10),
        "ciscat_pct_max": cis.get("compliance_pct_max", 95),
        "ciscat_min_deviations": cis.get("min_baseline_deviations", 1),
        "ciscat_required_fail_ids": [str(f) for f in cis.get("required_fail_ids", [])],
    }


def run_scans(api: ApiClient, fixture: Fixture, recorder: AssertionRecorder,
              fixture_dir: Path) -> None:
    cfg = _scan_config(fixture)

    # ── Nessus upload ──
    nessus_path = fixture_dir / "scans" / "sample_scan.nessus"
    nessus_scan_id = None
    if nessus_path.exists():
        content = nessus_path.read_bytes()
        files = {"file": ("sample_scan.nessus", io.BytesIO(content), "application/xml")}
        r = api.post_multipart("/api/scans/upload", files=files)
        recorder.expect("scans.nessus.parsed", r.ok,
                        actual=r.status_code, detail=r.text[:300] if not r.ok else "")
        if r.ok:
            scan_data = r.json()
            nessus_scan_id = scan_data.get("scan_id")
            finding_count = scan_data.get("finding_count", 0)
            min_f = cfg["nessus_min_findings"]
            recorder.expect("scans.nessus.finding_count",
                            finding_count >= min_f,
                            actual=finding_count, expected=f">={min_f}")
            crit = scan_data.get("critical_count", 0)
            min_c = cfg["nessus_min_criticals"]
            recorder.expect("scans.nessus.has_criticals", crit >= min_c,
                            actual=crit, expected=f">={min_c}")

    # ── Nessus findings detail ──
    if nessus_scan_id:
        r = api.get(f"/api/scans/{nessus_scan_id}/findings")
        if r.ok:
            findings = r.json().get("findings", [])
            plugin_ids = {f.get("plugin_id") for f in findings}
            for pid in cfg["nessus_required_plugins"]:
                recorder.expect(f"scans.nessus.plugin_{pid}_present",
                                pid in plugin_ids,
                                actual=sorted(plugin_ids),
                                expected=f"plugin {pid} in findings")

    # ── POA&M generation from Nessus ──
    if nessus_scan_id:
        r = api.post(f"/api/scans/{nessus_scan_id}/generate-poam")
        min_poam = cfg["nessus_min_poam_items"]
        poam_created = r.json().get("poam_items_created", 0) if r.ok else 0
        recorder.expect("scans.poam.generated",
                        r.ok and poam_created >= min_poam,
                        actual=r.json() if r.ok else r.status_code)

        # CA.L2-3.12.4 is POA&M-ineligible per CMMC — fixture-independent rule
        pr = api.get("/api/scoring/overview")
        if pr.ok:
            poam_items = pr.json().get("poam", {}).get("items", [])
            ca_items = [p for p in poam_items if p.get("control_id") == "CA.L2-3.12.4"]
            recorder.expect("scans.poam.no_ca_l2_3_12_4",
                            len(ca_items) == 0,
                            actual=len(ca_items),
                            detail="CA.L2-3.12.4 is POA&M-ineligible per CMMC")

    # ── CIS-CAT upload ──
    ciscat_path = fixture_dir / "scans" / "sample_ciscat.json"
    ciscat_scan_id = None
    if ciscat_path.exists():
        content = ciscat_path.read_bytes()
        files = {"file": ("sample_ciscat.json", io.BytesIO(content), "application/json")}
        r = api.post_multipart("/api/scans/upload", files=files)
        recorder.expect("scans.ciscat.parsed", r.ok,
                        actual=r.status_code, detail=r.text[:300] if not r.ok else "")
        if r.ok:
            ciscat_data = r.json()
            ciscat_scan_id = ciscat_data.get("scan_id")
            recorder.expect("scans.ciscat.auto_adopted",
                            ciscat_data.get("auto_adopted", False) or ciscat_data.get("baseline_id"),
                            actual=ciscat_data.get("auto_adopted"))

    # ── Baseline deviations ──
    r = api.get("/api/baselines/org/adopted")
    adopted = r.json() if r.ok else []
    if isinstance(adopted, list) and adopted:
        ob_id = adopted[0].get("org_baseline_id")
        if ob_id:
            dr = api.get(f"/api/baselines/org/{ob_id}/deviations")
            if dr.ok:
                devs = dr.json().get("items", [])
                dev_cis_ids = {d.get("cis_id") for d in devs}
                min_devs = cfg["ciscat_min_deviations"]
                recorder.expect("scans.baseline_deviations.count",
                                len(devs) >= min_devs,
                                actual=len(devs), expected=f">={min_devs}")
                for cid in cfg["ciscat_required_fail_ids"]:
                    recorder.expect(f"scans.ciscat.fail_{cid.replace('.','_')}",
                                    cid in dev_cis_ids,
                                    actual=sorted(dev_cis_ids))

    # ── Baseline summary ──
    sr = api.get("/api/baselines/summary")
    if sr.ok:
        summary = sr.json()
        recorder.expect("scans.baseline_summary_widget",
                        summary.get("baselines_adopted", 0) >= 1,
                        actual=summary)
        pct = summary.get("compliance_pct", 0)
        pct_min = cfg["ciscat_pct_min"]
        pct_max = cfg["ciscat_pct_max"]
        recorder.expect("scans.ciscat.compliance_pct_reasonable",
                        pct_min <= pct <= pct_max,
                        actual=pct, expected=f"{pct_min}-{pct_max}%")
