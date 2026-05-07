import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock dependencies before importing app
mock_detector = MagicMock()
mock_wasm = MagicMock()
sys.modules["src.detector"] = mock_detector
sys.modules["src.detector.anomaly_detector"] = mock_detector
sys.modules["src.runtime"] = mock_wasm
sys.modules["src.runtime.wasm_monitor"] = mock_wasm

from fastapi.testclient import TestClient
from src.api.main import app
import os
import json
import hmac
import hashlib
import time

client = TestClient(app)

def test_v5_strike_unauthorized():
    response = client.post("/api/v1/retaliate/v5_strike")
    assert response.status_code == 403

def test_v5_strike_authorized():
    headers = {"X-Kalpixk-Key": os.getenv("KALPIXK_API_KEY", "development_secret")}
    response = client.post("/api/v1/retaliate/v5_strike", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["v5_status"] == "STRIKE_COMPLETE"
    assert "v5_strike" in data

def test_v5_honeypot_exfiltrate():
    response = client.get("/api/v1/retaliate/exfiltrate")
    assert response.status_code == 200
    # Test streaming behavior (just first chunk)
    chunks = []
    for chunk in response.iter_bytes(chunk_size=1024):
        chunks.append(chunk)
        if len(chunks) > 5:
            break
    assert len(chunks) > 0

def test_v5_node_sync_version_validation():
    api_key = os.getenv("KALPIXK_API_KEY", "development_secret")

    payload = {
        "node_id": "test-node",
        "threats": ["T1110"],
        "timestamp": int(time.time()),
        "version": "5.0.0-atlatl"
    }

    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    signature = hmac.new(api_key.encode(), data, hashlib.sha256).hexdigest()

    headers = {
        "X-Kalpixk-Key": api_key,
        "X-Kalpixk-Signature": signature
    }

    response = client.post("/api/v1/nodes/sync", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["mesh_update"] == "v5.0.0-atlatl"

def test_v5_node_sync_backward_compatibility():
    api_key = os.getenv("KALPIXK_API_KEY", "development_secret")

    payload = {
        "node_id": "v4-node",
        "threats": ["T1003"],
        "timestamp": int(time.time()),
        "version": "4.0.0-atlatl"
    }

    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    signature = hmac.new(api_key.encode(), data, hashlib.sha256).hexdigest()

    headers = {
        "X-Kalpixk-Key": api_key,
        "X-Kalpixk-Signature": signature
    }

    response = client.post("/api/v1/nodes/sync", json=payload, headers=headers)
    assert response.status_code == 200
