from fastapi.testclient import TestClient

from python.api.kalpixk_api import app

client = TestClient(app)
AUTH_HEADERS = {"X-Kalpixk-Key": "development_secret"}

def test_embedded_node_sync_clean():
    payload = {
        "node_id": "esp32-node-01",
        "firmware_version": "1.0.0-v10",
        "cpu_usage_pct": 12.5,
        "memory_usage_pct": 45.0,
        "tamper_detected": False,
        "bus_anomaly": False
    }
    response = client.post("/api/v1/guerrilla/embedded_node/sync", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "synchronized"
    assert data["node_id"] == "esp32-node-01"
    assert data["threat_status"] == "CLEAN"
    assert data["shield_active"] is True

def test_embedded_node_sync_tamper_alert():
    payload = {
        "node_id": "embedded-rpi-09",
        "firmware_version": "1.0.0-v10",
        "cpu_usage_pct": 98.2,
        "memory_usage_pct": 91.0,
        "tamper_detected": True,
        "bus_anomaly": True,
        "raw_event": "JTAG_probe_attached_bus_tamper"
    }
    response = client.post("/api/v1/guerrilla/embedded_node/sync", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "synchronized"
    assert data["threat_status"] == "CRITICAL"
