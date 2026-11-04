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


def test_honeypot_endpoints_without_client_host():
    """Verify honeypot endpoints do not crash when request.client is None."""
    client = TestClient(app, client=None)
    res_exfil = client.get("/api/v1/honeypot/exfiltrate")
    assert res_exfil.status_code == 200
    assert res_exfil.json().get("status") == "access_denied"

    res_auth = client.post("/api/v1/honeypot/auth")
    assert res_auth.status_code == 200
    assert res_auth.json().get("status") == "success"
