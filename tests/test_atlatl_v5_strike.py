import pytest
from fastapi.testclient import TestClient
from src.api.main import app
import hmac
import hashlib
import json
import time
import os

client = TestClient(app)
API_KEY = os.getenv("KALPIXK_API_KEY", "development_secret")

def test_v5_strike_endpoint():
    headers = {"X-Kalpixk-Key": API_KEY}
    response = client.post("/api/v1/retaliate/v5_strike", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["v5_strike"] == "engaged"
    assert data["v5_status"] == "STRIKE_COMPLETE"

def test_node_7_v5_atlatl_sync():
    # Test valid sync with v5.0-atlatl versioning
    payload = {
        "node_id": "v5-node",
        "threats": ["10.0.0.1"],
        "timestamp": int(time.time()),
        "version": "5.0.0-atlatl"
    }

    # Standard deterministic serialization for HMAC
    payload_data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    signature = hmac.new(API_KEY.encode(), payload_data, hashlib.sha256).hexdigest()

    headers = {
        "X-Kalpixk-Key": API_KEY,
        "X-Kalpixk-Signature": signature
    }

    response = client.post("/api/v1/nodes/sync", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["mesh_update"] == "v5.0-atlatl"

def test_atlatl_v5_logic():
    from src.retaliation.atlatl import atlatl
    # Trigger score > 0.95 for v5 strike
    result = atlatl.trigger_retaliation(0.98, "8.8.8.8")
    assert result["v5_strike"] == "engaged"
    assert result["v5_status"] == "STRIKE_COMPLETE"

    # Trigger score > 0.85 for phase black
    result = atlatl.trigger_retaliation(0.88, "9.9.9.9")
    assert result["action"] == "EXTERMINATE"
    assert "v5_strike" not in result
