import pytest
import os
import json
import time
import hmac
import hashlib
from fastapi.testclient import TestClient
from src.api.main import app
from src.retaliation.atlatl import atlatl

client = TestClient(app)
API_KEY = os.getenv("KALPIXK_API_KEY", "development_secret")
HEADERS = {"X-Kalpixk-Key": API_KEY}

def test_v5_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == "5.0.0-atlatl"
    assert response.json()["atlatl_ordnance"] == "v5.0-atlatl"

def test_v5_status():
    response = client.get("/api/v1/status", headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["atlatl_version"] == "5.0.0-atlatl"

def test_v5_strike_trigger():
    # Mocking atlatl strike for integration test
    response = client.post("/api/v1/retaliate/v5_strike", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["v5_status"] == "STRIKE_COMPLETE"
    assert data["v5_strike"] == "engaged"

def test_node_sync_v5():
    payload = {
        "node_id": "test-node-v5",
        "threats": ["192.168.1.100"],
        "timestamp": int(time.time()),
        "version": "5.0.0-atlatl"
    }

    # Sign payload
    import hmac
    import hashlib
    payload_data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    signature = hmac.new(API_KEY.encode(), payload_data, hashlib.sha256).hexdigest()

    sync_headers = {**HEADERS, "X-Kalpixk-Signature": signature}
    response = client.post("/api/v1/nodes/sync", json=payload, headers=sync_headers)

    assert response.status_code == 200
    assert response.json()["mesh_update"] == "v5.0-atlatl"

def test_node_sync_legacy_v4():
    payload = {
        "node_id": "test-node-v4",
        "threats": ["192.168.1.101"],
        "timestamp": int(time.time()),
        "version": "4.0.0-atlatl"
    }

    payload_data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    signature = hmac.new(API_KEY.encode(), payload_data, hashlib.sha256).hexdigest()

    sync_headers = {**HEADERS, "X-Kalpixk-Signature": signature}
    response = client.post("/api/v1/nodes/sync", json=payload, headers=sync_headers)

    assert response.status_code == 200
    assert response.json()["mesh_update"] == "v5.0-atlatl"

def test_node_sync_invalid_version():
    payload = {
        "node_id": "test-node-v3",
        "threats": ["192.168.1.102"],
        "timestamp": int(time.time()),
        "version": "3.1.0-atlatl"
    }

    payload_data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    signature = hmac.new(API_KEY.encode(), payload_data, hashlib.sha256).hexdigest()

    sync_headers = {**HEADERS, "X-Kalpixk-Signature": signature}
    response = client.post("/api/v1/nodes/sync", json=payload, headers=sync_headers)

    # Should fail pydantic validation for version pattern
    assert response.status_code == 422
