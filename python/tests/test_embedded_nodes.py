import pytest
from fastapi.testclient import TestClient
from python.api.kalpixk_api import app

client = TestClient(app)

def test_embedded_node_sync_success():
    payload = {
        "node_id": "embedded-node-01",
        "arch": "armv7",
        "firmware_hash": "a1b2c3d4e5f678901234567890abcdefa1b2c3d4e5f678901234567890abcdef",
        "tampered": False,
        "hardware_alerts": [],
        "telemetry_data": {"cpu_temp": 42.5, "voltage": 3.3}
    }
    headers = {"X-Kalpixk-Key": "development_secret"}
    response = client.post("/api/v1/guerrilla/embedded_node/sync", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "synchronized"
    assert data["node_id"] == "embedded-node-01"
    assert data["tampered"] is False
    assert data["threat_score"] == 0.1
    assert data["action_required"] is False

def test_embedded_node_sync_tampered():
    payload = {
        "node_id": "embedded-node-02",
        "arch": "aarch64",
        "firmware_hash": "deadbeef1234567890abcdef1234567890abcdef1234567890abcdef12345678",
        "tampered": True,
        "hardware_alerts": ["JTAG_PROBE_DETECTED"],
        "telemetry_data": {"cpu_temp": 65.0, "voltage": 2.9}
    }
    headers = {"X-Kalpixk-Key": "development_secret"}
    response = client.post("/api/v1/guerrilla/embedded_node/sync", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "synchronized"
    assert data["node_id"] == "embedded-node-02"
    assert data["tampered"] is True
    assert data["threat_score"] == 1.0
    assert data["action_required"] is True
