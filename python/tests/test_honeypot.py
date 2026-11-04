"""
Unit tests for honeypot module inclusion and rate limiting.
"""
import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

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


@pytest.mark.asyncio
async def test_honeypot_endpoints_missing_client_metadata():
    transport = ASGITransport(app=app, client=None)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_exfil = await ac.get("/api/v1/honeypot/exfiltrate")
        assert res_exfil.status_code == 200
        assert res_exfil.json().get("status") == "access_denied"

        res_auth = await ac.post("/api/v1/honeypot/auth")
        assert res_auth.status_code == 200
        assert res_auth.json().get("status") == "success"
