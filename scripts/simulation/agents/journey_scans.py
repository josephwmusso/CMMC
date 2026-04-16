"""Stage 4: Nessus + CIS-CAT uploads, POA&M generation, baseline assertions."""
from __future__ import annotations

import io
from pathlib import Path

from scripts.simulation.agents.api_client import ApiClient
from scripts.simulation.agents.assertions import AssertionRecorder
from scripts.simulation.loader.schemas import Fixture


def run_scans(api: ApiClient, fixture: Fixture, recorder: AssertionRecorder,
              fixture_dir: Path) -> None:
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
            recorder.expect("scans.nessus.finding_count",
                            finding_count >= 10,
                            actual=finding_count, expected=">=10")
            crit = scan_data.get("critical_count", 0)
            recorder.expect("scans.nessus.has_criticals", crit >= 2,
                            actual=crit, expected=">=2")

    # ── Nessus findings detail ──
    if nessus_scan_id:
        r = api.get(f"/api/scans/{nessus_scan_id}/findings")
        if r.ok:
            findings = r.json().get("findings", [])
            plugin_ids = {f.get("plugin_id") for f in findings}
            # Check the two Tier 1 plugins are present
            for pid in ["96982", "58453"]:
                recorder.expect(f"scans.nessus.plugin_{pid}_present",
                                pid in plugin_ids,
                                actual=sorted(plugin_ids),
                                expected=f"plugin {pid} in findings")
            # Check contradiction-seeded plugins
            recorder.expect("scans.nessus.legacy_auth_153953",
                            "153953" in plugin_ids,
                            actual=sorted(plugin_ids))

    # ── POA&M generation from Nessus ──
    if nessus_scan_id:
        r = api.post(f"/api/scans/{nessus_scan_id}/generate-poam")
        recorder.expect("scans.poam.generated", r.ok and r.json().get("poam_items_created", 0) >= 1,
                        actual=r.json() if r.ok else r.status_code)

        # Verify no CA.L2-3.12.4 in POA&M
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
                recorder.expect("scans.baseline_deviations.count",
                                len(devs) >= 10,
                                actual=len(devs), expected=">=10")
                # Check required failing CIS IDs
                for cid in ["18.4.1", "1.1.4", "2.3.1", "18.9.1"]:
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
        recorder.expect("scans.ciscat.compliance_pct_reasonable",
                        20 <= pct <= 60,
                        actual=pct, expected="20-60%",
                        detail="~36% pass rate expected from fixture")
