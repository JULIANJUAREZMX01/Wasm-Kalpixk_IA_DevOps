import pytest
from fastapi.testclient import TestClient
from src.api.main import app
import hmac
import hashlib
import json
import time
import os

client = TestClient(app)

def test_health_v5():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "5.0.0-atlatl"
    assert data["vram_isolation"] == "ACTIVE"

def test_v5_strike_unauthorized():
    response = client.post("/api/v1/retaliate/v5_strike")
    # API key required
    assert response.status_code == 403

def test_v5_strike_authorized():
    key = os.getenv("KALPIXK_API_KEY", "development_secret")
    response = client.post("/api/v1/retaliate/v5_strike", headers={"X-Kalpixk-Key": key})
    assert response.status_code == 200
    data = response.json()
    assert data["v5_status"] == "STRIKE_COMPLETE"
    assert data["v5_strike"] == "engaged"

def test_node_sync_v5_integrity():
    key = os.getenv("KALPIXK_API_KEY", "development_secret")
    report = {
        "node_id": "test-node",
        "threats": ["T1003"],
        "timestamp": int(time.time()),
        "version": "5.0.0-atlatl"
    }
    payload = json.dumps(report, sort_keys=True, separators=(",", ":")).encode()
    signature = hmac.new(key.encode(), payload, hashlib.sha256).hexdigest()

    response = client.post(
        "/api/v1/nodes/sync",
        json=report,
        headers={
            "X-Kalpixk-Key": key,
            "X-Kalpixk-Signature": signature
        }
    )
    assert response.status_code == 200
    assert response.json()["mesh_update"] == "v4.0-atlatl" # API returns v4.0 update message but version in report is 5.0
