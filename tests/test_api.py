"""
tests/test_api.py

FastAPI endpoint smoke tests using TestClient (no live services needed).

Run: pytest tests/test_api.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """TestClient with DB and LLM dependencies mocked out."""
    from src.api.main import app

    mock_db = MagicMock()

    def override_get_db():
        yield mock_db

    from src.db.session import get_db
    from src.api.auth import get_current_user
    from tests.conftest import TEST_USER

    app.dependency_overrides[get_db] = override_get_db
    # Bypass JWT decode + DB lookup so protected routes work with any valid header
    app.dependency_overrides[get_current_user] = lambda: TEST_USER

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestScoringRoutes:
    def test_sprs_endpoint_exists(self, client, auth_headers):
        with patch("src.api.scoring_routes.SPRSCalculator") as mock_calc:
            mock_calc.return_value.get_score_summary.return_value = {
                "score": 82,
                "deductions": 28,
                "controls_total": 110,
                "controls_implemented": 85,
                "poam_eligible": True,
            }
            resp = client.get("/api/scoring/sprs", headers=auth_headers)
        assert resp.status_code == 200
        assert "score" in resp.json()

    def test_gaps_endpoint_exists(self, client, auth_headers):
        with patch("src.api.scoring_routes.GapAssessmentEngine") as mock_engine:
            mock_engine.return_value.get_summary.return_value = {
                "total_gaps": 5,
                "gap_details": [],
                "critical_gaps": 0,
            }
            resp = client.get("/api/scoring/gaps", headers=auth_headers)
        assert resp.status_code == 200

    def test_overview_endpoint_returns_all_sections(self, client, auth_headers):
        with patch("src.api.scoring_routes.SPRSCalculator") as mock_sprs, \
             patch("src.api.scoring_routes.GapAssessmentEngine") as mock_gaps, \
             patch("src.api.scoring_routes.POAMGenerator") as mock_poam:
            mock_sprs.return_value.get_score_summary.return_value = {"score": 95}
            mock_gaps.return_value.get_summary.return_value = {"total_gaps": 2}
            mock_poam.return_value.get_poam_summary.return_value = {"total": 1}
            resp = client.get("/api/scoring/overview", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "sprs" in data
        assert "gaps" in data
        assert "poam" in data


class TestSSPRoutes:
    def test_generate_single_control(self, client):
        from src.agents.ssp_generator_v2 import SSPControlResult

        mock_result = SSPControlResult(
            control_id="AC.L2-3.1.1",
            status="Implemented",
            narrative="Access control is enforced via Active Directory policies...",
            evidence_artifacts=["AD_Policy.pdf"],
            gaps=[],
            generation_time_sec=2.3,
        )

        with patch("src.api.ssp_routes.SSPGenerator") as mock_gen, \
             patch("src.api.ssp_routes.get_llm"):
            mock_gen.return_value.generate_single_control.return_value = mock_result
            resp = client.post(
                "/api/ssp/generate",
                json={"control_id": "AC.L2-3.1.1"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["control_id"] == "AC.L2-3.1.1"
        assert data["status"] == "Implemented"
        assert "narrative" in data

    def test_generate_full_ssp_returns_job_id(self, client):
        # Patch the background runner so it doesn't try to connect to LLM/DB
        with patch("src.api.ssp_routes._run_full_ssp"):
            resp = client.post("/api/ssp/generate-full", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert data["status"] in ("pending", "running")

    def test_status_unknown_job_returns_404(self, client):
        resp = client.get("/api/ssp/status?job_id=nonexistent-job-xyz")
        assert resp.status_code == 404


class TestEvidenceRoutes:
    def test_list_artifacts_returns_count(self, client, auth_headers):
        with patch("src.api.evidence_routes.list_artifacts", return_value=[]):
            resp = client.get("/api/evidence/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "artifacts" in data

    def test_transition_unknown_artifact_returns_404(self, client, auth_headers):
        # get_artifact returns None → route raises 404 before calling transition_evidence
        with patch("src.api.evidence_routes.get_artifact", return_value=None):
            resp = client.post(
                "/api/evidence/EVD-FAKE/transition",
                params={"new_state": "REVIEWED"},
                headers=auth_headers,
            )
        assert resp.status_code == 404

    def test_invalid_state_transition_returns_400(self, client, auth_headers):
        from src.evidence.state_machine import StateTransitionError
        fake_artifact = {"org_id": "9de53b587b23450b87af", "filename": "test.pdf"}
        with patch("src.api.evidence_routes.get_artifact", return_value=fake_artifact), \
             patch("src.api.evidence_routes.transition_evidence",
                   side_effect=StateTransitionError("Cannot transition from PUBLISHED")):
            resp = client.post(
                "/api/evidence/EVD-001/transition",
                params={"new_state": "DRAFT"},
                headers=auth_headers,
            )
        assert resp.status_code == 400
