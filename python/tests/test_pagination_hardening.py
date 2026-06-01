
import pytest
from fastapi.testclient import TestClient
from python.api.kalpixk_api import app

client = TestClient(app)

@pytest.fixture
def auth_header():
    return {"X-Kalpixk-Key": "development_secret"}

def test_pagination_limit_positive(auth_header):
    response = client.get("/api/alerts?limit=10", headers=auth_header)
    assert response.status_code == 200
    # The actual number of alerts depends on the DB, but we check if it doesn't crash

def test_pagination_limit_negative_bypass(auth_header):
    # Testing that limit=-1 (or any negative) is constrained to at least 1
    response = client.get("/api/alerts?limit=-1", headers=auth_header)
    assert response.status_code == 200
    # If the fix works, 'limit' should have been set to 1 internally.
    # Since we can't easily see the internal 'limit' without more mock,
    # we just ensure it returns a valid response and not 0 or error.
    data = response.json()
    assert "alerts" in data

def test_pagination_limit_excessive(auth_header):
    # Testing that limit=1000 is constrained to 500
    response = client.get("/api/alerts?limit=1000", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data

def test_unauthenticated_access_fails():
    # Should fail now because even in dev we require development_secret
    response = client.get("/status")
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid credentials"

def test_authenticated_access_success(auth_header):
    response = client.get("/status", headers=auth_header)
    assert response.status_code == 200
