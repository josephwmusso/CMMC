"""Stage 11: Freshness check (deterministic)."""
from __future__ import annotations

from scripts.simulation.agents.api_client import ApiClient
from scripts.simulation.agents.assertions import AssertionRecorder


def run_freshness(api: ApiClient, recorder: AssertionRecorder) -> dict:
    r = api.post("/api/freshness/refresh-claims")
    recorder.expect("freshness.refresh_succeeded", r.ok, actual=r.status_code if r else 0)

    sr = api.get("/api/freshness/summary")
    if sr.ok:
        data = sr.json()
        ev = data.get("evidence", {})
        recorder.expect("freshness.no_unexpected_stale",
                        ev.get("stale", 0) == 0,
                        actual=ev.get("stale", 0),
                        detail="Freshly-seeded org should have 0 stale items")
        return data

    return {}
