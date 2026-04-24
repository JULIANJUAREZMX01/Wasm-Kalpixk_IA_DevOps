import pytest
import time
import json
import hmac
import hashlib
import os
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def sign_payload(payload: dict, key: str):
    data = json.dumps(payload, sort_keys=True)
    return hmac.new(key.encode(), data.encode(), hashlib.sha256).hexdigest()

def test_health_v4():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == "4.0.0-atlatl"
    assert response.json()["atlatl_ordnance"] == "v4.0-guerrilla"
    assert response.json()["node_7_active"] is True

def test_metrics_auth_v4():
    response = client.get("/api/v1/metrics")
    # Should fail without key if KALPIXK_ENV is production,
    # but in dev it depends on if KALPIXK_API_KEY is set.
    # In tests, verify_api_key uses os.getenv
    pass

def test_node_sync_v4_valid():
    payload = {
        "node_id": "TEST_GUERRILLA_V4",
        "threats": ["10.0.0.5"],
        "timestamp": int(time.time()),
        "version": "4.0.0-atlatl"
    }
    sig = sign_payload(payload, "development")
    payload["mesh_sig"] = sig

    response = client.post("/api/v1/nodes/sync", json=payload, headers={"X-Kalpixk-Key": "development"})
    assert response.status_code == 200
    assert response.json()["integrity"] == "verified"
    assert response.json()["active_mesh_nodes"] == 7

def test_node_sync_v4_invalid_sig():
    payload = {
        "node_id": "SPOOFED_NODE",
        "threats": ["evil.com"],
        "timestamp": int(time.time()),
        "version": "4.0.0-atlatl",
        "mesh_sig": "a" * 64
    }
    response = client.post("/api/v1/nodes/sync", json=payload, headers={"X-Kalpixk-Key": "development"})
    assert response.status_code == 403
    assert "Invalid Mesh Signature" in response.json()["detail"]

def test_honeypot_exfiltrate_v4():
    response = client.get("/api/v1/retaliate/exfiltrate")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"

def test_honeypot_core_dump_v4():
    response = client.get("/api/v1/retaliate/debug/core_dump")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert response.content.startswith(b'PK\x03\x04')
