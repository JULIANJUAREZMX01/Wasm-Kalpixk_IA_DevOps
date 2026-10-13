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
    payload_tampered = {
        "node_id": "NODE-10-EMBEDDED-01",
        "firmware_hash": "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890",
        "tamper_detected": True,
        "cpu_usage": 85.5,
        "memory_usage": 62.0,
        "threat_level": "CRITICAL"
    }
    res = client.post("/api/v1/guerrilla/embedded_node/sync", json=payload_tampered)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "synchronized"
    assert data["node_id"] == "NODE-10-EMBEDDED-01"
    assert data["tamper_alert"] is True
    assert data["action"] == "LOCKDOWN"

    payload_clean = {
        "node_id": "NODE-10-EMBEDDED-02",
        "firmware_hash": "f6e5d4c3b2a109876543210fe210f6e5d4c3b2a109876543210fe210f6e5d4c3",
        "tamper_detected": False,
        "cpu_usage": 12.0,
        "memory_usage": 25.0,
        "threat_level": "CLEAN"
    }
    res_clean = client.post("/api/v1/guerrilla/embedded_node/sync", json=payload_clean)
    assert res_clean.status_code == 200
    data_clean = res_clean.json()
    assert data_clean["tamper_alert"] is False
    assert data_clean["action"] == "MONITORING"

def test_v9_strike_endpoint():
    response = client.post("/api/v1/guerrilla/v9/strike")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data.get("version") == "9.0.0-XOCHIMILCO"
