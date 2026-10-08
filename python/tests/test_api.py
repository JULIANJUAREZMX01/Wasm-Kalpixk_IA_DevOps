import sys
from pathlib import Path

from fastapi.testclient import TestClient

# Add python dir to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.kalpixk_api import app

client = TestClient(app)
client.headers = {"X-Kalpixk-Key": "development_secret"}

def test_status_endpoint():
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "device" in data

def test_features_endpoint():
    response = client.get("/features")
    assert response.status_code == 200
    data = response.json()
    assert data["feature_dim"] == 32
    assert len(data["features"]) == 32

def test_security_headers():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "object-src 'none'" in response.headers["Content-Security-Policy"]

def test_simulate_start_url_validation(monkeypatch):
    monkeypatch.setenv("KALPIXK_BACKEND_URL", "ftp://evil.com/path")
    response = client.post("/api/simulate/start")
    assert response.status_code == 400
    assert "Invalid KALPIXK_BACKEND_URL" in response.json()["detail"]

    monkeypatch.setenv("KALPIXK_BACKEND_URL", "http://localhost:8000; rm -rf /")
    response = client.post("/api/simulate/start")
    assert response.status_code == 400
    assert "Invalid KALPIXK_BACKEND_URL" in response.json()["detail"]
