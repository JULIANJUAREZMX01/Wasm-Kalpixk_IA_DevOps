import pytest
import time
from fastapi.testclient import TestClient
from src.api.main import app
from src.retaliation.atlatl import atlatl

client = TestClient(app)

def test_health_v4():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == "4.0.0-atlatl"
    assert response.json()["atlatl_ordnance"] == "v4.0-macuahuitl"
    assert response.json()["node_7_integrity"] == "verified"

def test_metrics_retaliation_trigger():
    response = client.get("/api/v1/metrics", headers={"X-Kalpixk-Key": "development"})
    assert response.status_code == 200
    data = response.json()
    assert "features" in data
    assert "detection" in data

def test_node_sync_v4():
    payload = {
        "node_id": "TEST_GUERRILLA_V4",
        "threats": ["192.168.1.100"],
        "timestamp": int(time.time()),
        "signature": "VALID_SIG_V4"
    }
    response = client.post("/api/v1/nodes/sync", json=payload, headers={"X-Kalpixk-Key": "development"})
    assert response.status_code == 200
    assert response.json()["status"] == "synced"
    assert response.json()["mesh_update"] == "v4.0-guerrilla"

def test_honeypot_exfiltrate_v4():
    response = client.get("/api/v1/retaliate/exfiltrate")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    chunk = next(response.iter_bytes(1024))
    assert len(chunk) == 1024

def test_atlatl_phase_black():
    res = atlatl.trigger_retaliation(0.95, "1.1.1.1")
    assert res["action"] == "ANNIHILATE"
    assert res["vector"] == "v5_stealth_poisoning"
    assert res["ghost_block"] is True

def test_atlatl_phase_red():
    res = atlatl.trigger_retaliation(0.75, "2.2.2.2")
    assert res["action"] == "ANNIHILATE"
    assert "payload" in res
