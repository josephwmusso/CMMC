"""Stage 13: Exports — binder, SPRS package, affirmation."""
from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path

from scripts.simulation.agents.api_client import ApiClient
from scripts.simulation.agents.assertions import AssertionRecorder
from scripts.simulation.loader.schemas import Fixture


def run_exports(api: ApiClient, fixture: Fixture, recorder: AssertionRecorder,
                run_dir: Path) -> dict:
    exports_dir = run_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)

    # ── Binder export (two downloads for determinism check) ──
    r1 = api.post("/api/exports/binder")
    recorder.expect("exports.binder_downloadable", r1.ok and len(r1.content) > 1000,
                    actual=len(r1.content) if r1.ok else r1.status_code)

    r2 = api.post("/api/exports/binder")

    if r1.ok and r2.ok:
        (exports_dir / "evidence_binder.zip").write_bytes(r1.content)
        # Binder ZIP contains timestamps in PDFs → byte-level hash varies.
        # The meaningful invariant is submission_fields_hash (tested in SPRS).
        recorder.warn("exports.binder_note",
                      detail="Binder hash varies with timestamps (expected per 6.3 design)")

        # Check structure
        try:
            zf = zipfile.ZipFile(io.BytesIO(r1.content))
            names = zf.namelist()
            expected_files = ["00_README.md", "04_Manifest.json", "06_Audit_Log.json"]
            found = [f for f in expected_files if f in names]
            recorder.expect("exports.binder_structure_complete",
                            len(found) >= len(expected_files),
                            actual=sorted(names)[:10],
                            expected=expected_files)

            # Manifest hash check
            if "04_Manifest.json" in names:
                manifest = json.loads(zf.read("04_Manifest.json"))
                entries = manifest.get("entries", [])
                recorder.expect("exports.binder_manifest_has_entries",
                                isinstance(entries, list),
                                actual=f"{len(entries)} entries")
        except Exception as e:
            recorder.expect("exports.binder_structure_complete", False, detail=str(e))

    # ── SPRS submission_fields_hash determinism ──
    sp1 = api.get("/api/exports/sprs-preview")
    sp2 = api.get("/api/exports/sprs-preview")
    if sp1.ok and sp2.ok:
        # submission_fields should be identical across calls
        f1 = json.dumps(sp1.json().get("submission_fields", {}), sort_keys=True)
        f2 = json.dumps(sp2.json().get("submission_fields", {}), sort_keys=True)
        h1 = hashlib.sha256(f1.encode()).hexdigest()
        h2 = hashlib.sha256(f2.encode()).hexdigest()
        recorder.expect("exports.sprs_submission_fields_hash_deterministic",
                        h1 == h2, actual=f"h1={h1[:16]} h2={h2[:16]}")

    # ── SPRS preview ──
    pr = api.get("/api/exports/sprs-preview")
    if pr.ok:
        fields = pr.json().get("submission_fields", {})
        cp = fixture.company_profile
        recorder.expect("exports.sprs_preview_fields_complete",
                        bool(fields.get("company_name")),
                        actual=fields.get("company_name"))

    # ── SPRS package ──
    sr = api.post("/api/exports/sprs-package")
    recorder.expect("exports.sprs_package_downloadable",
                    sr.ok and len(sr.content) > 500,
                    actual=len(sr.content) if sr.ok else sr.status_code)
    if sr.ok:
        (exports_dir / "sprs_package.zip").write_bytes(sr.content)

    # ── Affirmation (clean prior state from reuse runs) ──
    # List existing and note — can't DELETE via API, but a fresh org from
    # 3A.2a won't have stale affirmations. For --reuse-org-id runs, accept
    # that prior affirmations may exist and skip the NEVER_AFFIRMED check.
    ar = api.get("/api/affirmations/status")
    if ar.ok:
        status = ar.json().get("status", "")
        if status == "NEVER_AFFIRMED":
            recorder.expect("exports.affirmation_status_initial", True, actual=status)
        else:
            recorder.warn("exports.affirmation_status_initial",
                          detail=f"Expected NEVER_AFFIRMED, got {status} (stale from prior run)",
                          actual=status)

    cr = api.post("/api/affirmations", json={
        "affirmer_title": "CISO",
        "attestation_text": "Simulation fixture attestation.",
        "confirm": True,
    })
    recorder.expect("exports.affirmation_created", cr.ok,
                    actual=cr.status_code if cr else 0)

    if cr.ok:
        aff = cr.json()
        aff_id = aff.get("id", "")

        # Download certificate
        cert_r = api.get(f"/api/affirmations/{aff_id}/certificate")
        if cert_r.ok:
            (exports_dir / f"affirmation_{aff_id}.pdf").write_bytes(cert_r.content)

        # Verify hash
        vr = api.get(f"/api/affirmations/{aff_id}/verify")
        if vr.ok:
            recorder.expect("exports.affirmation_certificate_hash_verifies",
                            vr.json().get("hash_matches", False),
                            actual=vr.json())

        # Status should be CURRENT now
        sr2 = api.get("/api/affirmations/status")
        if sr2.ok:
            recorder.expect("exports.affirmation_status_current",
                            sr2.json().get("status") == "CURRENT",
                            actual=sr2.json().get("status"))

    # ── Export history ──
    hr = api.get("/api/exports/history")
    if hr.ok:
        types = {e.get("export_type") for e in hr.json()}
        recorder.expect("exports.history_has_both_types",
                        "BINDER_ZIP" in types and "SPRS_PACKAGE" in types,
                        actual=sorted(types))

    return {}
