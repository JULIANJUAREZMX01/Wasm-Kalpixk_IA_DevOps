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

def test_honeypot_null_client_request():
    import asyncio

    from starlette.requests import Request

    from python.api.honeypot import trap_brute_force, trap_exfiltration

    scope = {"type": "http", "client": None, "headers": [], "path": "/"}
    req = Request(scope)

    res_exfil = asyncio.run(trap_exfiltration(req))
    assert res_exfil["status"] == "access_denied"

    res_auth = asyncio.run(trap_brute_force(req))
    assert res_auth["status"] == "success"
