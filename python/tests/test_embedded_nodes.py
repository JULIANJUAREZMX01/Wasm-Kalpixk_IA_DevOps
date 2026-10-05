from fastapi.testclient import TestClient

from python.api.kalpixk_api import app

client = TestClient(app)
client.headers = {"X-Kalpixk-Key": "development_secret"}


def test_embedded_node_sync_normal():
    payload = {
        "node_id": "NODE-EMBEDDED-01",
        "firmware_hash": "a1b2c3d4e5f67890",
        "tamper_flag": False,
        "raw_telemetry": "GPIO_OK voltage_normal",
        "features": [0.3] * 32,
    }
    response = client.post("/api/v1/guerrilla/embedded_node/sync", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "synchronized"
    assert data["node_id"] == "NODE-EMBEDDED-01"
    assert data["tamper_detected"] is False


def test_embedded_node_sync_tampered():
    payload = {
        "node_id": "NODE-EMBEDDED-02",
        "firmware_hash": "badhash123",
        "tamper_flag": True,
        "raw_telemetry": "firmware_tamper detected on SPI flash",
    }
    response = client.post("/api/v1/guerrilla/embedded_node/sync", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "synchronized"
    assert data["tamper_detected"] is True
    assert data["anomaly_score"] == 1.0
    assert data["severity"] == "CRITICAL"


def test_embedded_node_invalid_features():
    payload = {
        "node_id": "NODE-EMBEDDED-03",
        "features": [0.1] * 10,  # Invalid dimension
    }
    response = client.post("/api/v1/guerrilla/embedded_node/sync", json=payload)
    assert response.status_code == 422
