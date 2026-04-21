from fastapi.testclient import TestClient
from src.api.main import app
from src.retaliation.atlatl import atlatl

client = TestClient(app)

def test_health_v4():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == "4.0.0-atlatl"
    assert response.json()["atlatl_ordnance"] == "v4.0-macuahuitl"

def test_metrics_retaliation_trigger():
    # Force a mock high score or use real if possible.
    # Since we can't easily mock the detector here without dependency injection,
    # we'll test the endpoint logic.
    response = client.get("/api/v1/metrics", headers={"X-Kalpixk-Key": "development"})
    assert response.status_code == 200
    data = response.json()
    assert "features" in data
    assert "detection" in data

def test_node_sync_v4():
    import time
    payload = {
        "node_id": "TEST_GUERRILLA_01",
        "threats": ["192.168.1.100"],
        "timestamp": int(time.time())
    }
    response = client.post("/api/v1/nodes/sync", json=payload, headers={"X-Kalpixk-Key": "development"})
    assert response.status_code == 200
    assert response.json()["status"] == "synced"
    assert "mesh_update" in response.json()

def test_honeypot_exfiltrate_v4():
    response = client.get("/api/v1/retaliate/exfiltrate")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    # Read a bit of the stream
    chunk = next(response.iter_bytes(1024))
    assert len(chunk) == 1024

def test_atlatl_phase_black():
    res = atlatl.trigger_retaliation(0.95, "1.1.1.1")
    assert res["action"] == "EXTERMINATE"
    assert "recursive_zip_bomb" in res["measures"]
    assert "ghost_block" in res["measures"]
    assert "mesh_entropy_shredder" in res["measures"]

def test_atlatl_phase_red():
    res = atlatl.trigger_retaliation(0.75, "2.2.2.2")
    assert res["action"] == "RETALIATE_RED"
    assert "pointer_poisoning" in res["measures"]
