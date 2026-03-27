"""
tests/conftest.py

Shared pytest fixtures for the CMMC platform test suite.

auth_headers — generates a valid JWT Bearer token for a synthetic test user
               without touching the database. Works alongside the mocked-DB
               client fixture in test_api.py (get_current_user is overridden
               there so the DB lookup is bypassed).
"""

import pytest
from src.api.auth import create_access_token

# Matches the demo org seeded by init_db / load_nist_to_postgres
DEMO_ORG_ID = "9de53b587b23450b87af"

# Synthetic test user — never written to the DB; only used for JWT payload
TEST_USER = {
    "id": "USR-TESTAPEX0001",
    "email": "testuser@apex.com",
    "org_id": DEMO_ORG_ID,
    "full_name": "Test User",
    "is_admin": True,
}


@pytest.fixture(scope="module")
def auth_headers():
    """
    Return Authorization headers with a valid JWT for TEST_USER.

    The token is generated directly via create_access_token (same function
    the /login route uses) — no HTTP round-trip or DB insert needed.
    The get_current_user dependency is overridden in the client fixture so
    the DB lookup is also bypassed.
    """
    token = create_access_token(
        {"sub": TEST_USER["id"], "org_id": TEST_USER["org_id"]}
    )
    return {"Authorization": f"Bearer {token}"}
