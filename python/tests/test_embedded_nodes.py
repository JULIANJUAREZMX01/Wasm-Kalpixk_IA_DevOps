from fastapi.testclient import TestClient

from python.api.kalpixk_api import app

client = TestClient(app)
HEADERS = {"X-Kalpixk-Key": "development_secret"}

def test_embedded_node_sync_valid():
    payload = {
        "node_id": "NODE-10-EMBEDDED-01",
        "firmware_version": "v10.0-EMBEDDED",
        "tamper_flag": False,
        "hardware_temp_c": 42.5,
        "cpu_usage_pct": 18.2,
        "features": [0.1] * 32,
        "source_ip": "192.168.1.100"
    }
    response = client.post("/api/v1/guerrilla/embedded_node/sync", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "synchronized"
    assert data["node_id"] == "NODE-10-EMBEDDED-01"
    assert data["tamper_flag"] is False

def test_embedded_node_sync_tamper_alert():
    payload = {
        "node_id": "NODE-10-EMBEDDED-02",
        "firmware_version": "v10.0-EMBEDDED",
        "tamper_flag": True,
        "hardware_temp_c": 78.0,
        "cpu_usage_pct": 99.1,
        "features": None,
        "source_ip": "10.0.0.50"
    }
    response = client.post("/api/v1/guerrilla/embedded_node/sync", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "synchronized"
    assert data["tamper_flag"] is True

def test_embedded_node_sync_invalid_dimension():
    payload = {
        "node_id": "NODE-10-EMBEDDED-03",
        "firmware_version": "v10.0-EMBEDDED",
        "tamper_flag": False,
        "hardware_temp_c": 35.0,
        "cpu_usage_pct": 10.0,
        "features": [0.1] * 10,
        "source_ip": "10.0.0.51"
    }
    response = client.post("/api/v1/guerrilla/embedded_node/sync", json=payload, headers=HEADERS)
    assert response.status_code == 422
