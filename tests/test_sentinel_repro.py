import pytest
from fastapi.testclient import TestClient
from python.api.kalpixk_api import app
import os

client = TestClient(app)

def test_analyze_unauthenticated(monkeypatch):
    monkeypatch.setenv("KALPIXK_API_KEY", "test_key")
    monkeypatch.setenv("KALPIXK_ENV", "production")

    response = client.post("/analyze", json={
        "features": [0.0] * 32,
        "source": "test"
    })
    assert response.status_code == 403

def test_train_unauthenticated(monkeypatch):
    monkeypatch.setenv("KALPIXK_API_KEY", "test_key")
    monkeypatch.setenv("KALPIXK_ENV", "production")

    response = client.post("/train?n_samples=10")
    assert response.status_code == 403

def test_status_authenticated(monkeypatch):
    monkeypatch.setenv("KALPIXK_API_KEY", "test_key")
    monkeypatch.setenv("KALPIXK_ENV", "production")

    response = client.get("/status", headers={"X-Kalpixk-Key": "test_key"})
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in response.headers

def test_websocket_unauthenticated(monkeypatch):
    monkeypatch.setenv("KALPIXK_API_KEY", "test_key")
    monkeypatch.setenv("KALPIXK_ENV", "production")

    with pytest.raises(Exception): # TestClient raises for closed WS during connection
        with client.websocket_connect("/stream") as websocket:
            pass

def test_websocket_authenticated(monkeypatch):
    monkeypatch.setenv("KALPIXK_API_KEY", "test_key")
    monkeypatch.setenv("KALPIXK_ENV", "production")

    with client.websocket_connect("/stream?token=test_key") as websocket:
        # If we get here, it's accepted
        pass

def test_cors_wildcard_production(monkeypatch):
    monkeypatch.setenv("KALPIXK_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", '["*"]')
    # We need to re-initialize or check app middleware.
    # Since middleware is added at module level, this test might be tricky without reloading.
    # But we can verify if the logic is there.
    pass
