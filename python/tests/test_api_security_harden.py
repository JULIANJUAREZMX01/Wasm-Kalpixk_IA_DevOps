
from fastapi.testclient import TestClient

from python.api.kalpixk_api import app

client = TestClient(app)

def test_api_key_hardening_no_key(monkeypatch):
    # Unset environment variable
    monkeypatch.delenv("KALPIXK_API_KEY", raising=False)

    # Request without header should fail
    response = client.get("/status")
    assert response.status_code == 403

    # Request with wrong header should fail
    response = client.get("/status", headers={"X-Kalpixk-Key": "wrong"})
    assert response.status_code == 403

    # Request with 'development_secret' should succeed
    response = client.get("/status", headers={"X-Kalpixk-Key": "development_secret"})
    assert response.status_code == 200

def test_api_key_hardening_with_key(monkeypatch):
    # Set environment variable
    monkeypatch.setenv("KALPIXK_API_KEY", "ultra_secret")

    # Request with 'development_secret' should now fail
    response = client.get("/status", headers={"X-Kalpixk-Key": "development_secret"})
    assert response.status_code == 403

    # Request with 'ultra_secret' should succeed
    response = client.get("/status", headers={"X-Kalpixk-Key": "ultra_secret"})
    assert response.status_code == 200
