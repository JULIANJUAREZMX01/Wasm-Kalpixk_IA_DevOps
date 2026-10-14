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

def test_embedded_node_sync_endpoint():
    payload = {
        "node_id": "NODE-10-ARM64-EMBEDDED",
        "arch": "arm64",
        "firmware_hash": "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
        "tamper_flag": True,
        "cpu_temp": 42.5,
        "memory_usage_pct": 35.0,
        "active_traps": 3
    }
    response = client.post("/api/v1/guerrilla/embedded_node/sync", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "synchronized"
    assert data["node_id"] == "NODE-10-ARM64-EMBEDDED"
    assert data["tamper_detected"] is True
    assert data["active_traps"] == 3
