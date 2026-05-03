import pytest
from fastapi.testclient import TestClient
import os
import json
import time
import hmac
import hashlib

# Mocking modules that might have heavy dependencies
import sys
from unittest.mock import MagicMock

# Create a mock for src.detector and src.runtime
sys.modules["src.detector"] = MagicMock()
sys.modules["src.runtime.wasm_monitor"] = MagicMock()

from src.api.main import app

client = TestClient(app)
API_KEY = "development_secret"

def test_v5_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "5.0.0-atlatl"
    assert data["atlatl_ordnance"] == "v5.0-atlatl"

def test_v5_strike_unauthorized():
    response = client.post("/api/v1/retaliate/v5_strike")
    assert response.status_code == 403 # Missing key

def test_v5_strike_authorized():
    headers = {"X-Kalpixk-Key": API_KEY}
    response = client.post("/api/v1/retaliate/v5_strike", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["v5_strike"] == "engaged"
    assert data["v5_status"] == "STRIKE_COMPLETE"

def test_v5_node_sync():
    report = {
        "node_id": "test-node",
        "threats": ["T1003", "T1059"],
        "timestamp": int(time.time()),
        "version": "5.0.0-atlatl"
    }

    payload_data = json.dumps(report, sort_keys=True, separators=(",", ":")).encode()
    signature = hmac.new(API_KEY.encode(), payload_data, hashlib.sha256).hexdigest()

    headers = {
        "X-Kalpixk-Key": API_KEY,
        "X-Kalpixk-Signature": signature
    }

    response = client.post("/api/v1/nodes/sync", json=report, headers=headers)
    assert response.status_code == 200
    assert response.json()["mesh_update"] == "v5.0-atlatl"

def test_v5_honeypots():
    # Exfiltrate
    response = client.get("/api/v1/retaliate/exfiltrate")
    assert response.status_code == 200
    assert "core_exfil_v5.bin" in response.headers["Content-Disposition"]

    # Core dump
    response = client.get("/api/v1/retaliate/debug/core_dump")
    assert response.status_code == 200
    assert response.content.startswith(b"PK\x03\x04")
