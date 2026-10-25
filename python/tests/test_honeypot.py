"""
Unit tests for honeypot module inclusion and rate limiting.
"""
from fastapi.testclient import TestClient

from python.api.kalpixk_api import app


def test_honeypot_exfiltrate_endpoint():
    client = TestClient(app)
    response = client.get("/api/v1/honeypot/exfiltrate")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "access_denied"
    assert data.get("error") == "ATLATL_CORE_LOCKED"

def test_honeypot_auth_endpoint():
    client = TestClient(app)
    response = client.post("/api/v1/honeypot/auth")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "success"
