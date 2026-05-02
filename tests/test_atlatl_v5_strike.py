import hmac
import hashlib
import json
import time
import os
import sys
from unittest.mock import MagicMock

# Mock dependencies
sys.modules["src.detector.anomaly_detector"] = MagicMock()
sys.modules["src.detector"] = MagicMock()
sys.modules["src.runtime.wasm_monitor"] = MagicMock()

from fastapi.testclient import TestClient
from src.api.main import app
from src.retaliation.atlatl import atlatl

client = TestClient(app)
API_KEY = "development_secret"

def test_health_v5():
    print("Testing health v5...")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == "5.0.0-atlatl"
    print("Health v5: OK")

def test_v5_strike_unauthorized():
    print("Testing v5 strike unauthorized...")
    response = client.post("/api/v1/retaliate/v5_strike")
    # API key is required
    assert response.status_code == 403
    print("v5 strike unauthorized: OK")

def test_v5_strike_authorized():
    print("Testing v5 strike authorized...")
    headers = {"X-Kalpixk-Key": API_KEY}
    response = client.post("/api/v1/retaliate/v5_strike", headers=headers)
    assert response.status_code == 200
    assert response.json()["v5_status"] == "STRIKE_COMPLETE"
    print("v5 strike authorized: OK")

def test_node_7_sync_v5():
    print("Testing node-7 sync v5...")
    payload = {
        "node_id": "v5-node",
        "threats": ["10.0.0.1"],
        "timestamp": int(time.time()),
        "version": "5.0.0-atlatl"
    }
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    signature = hmac.new(API_KEY.encode(), data, hashlib.sha256).hexdigest()

    headers = {
        "X-Kalpixk-Key": API_KEY,
        "X-Kalpixk-Signature": signature
    }

    response = client.post("/api/v1/nodes/sync", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["mesh_update"] == "v4.0-atlatl" or response.json()["mesh_update"] == "v5.0-atlatl"
    print("Node-7 sync v5: OK")

if __name__ == "__main__":
    try:
        test_health_v5()
        test_v5_strike_unauthorized()
        test_v5_strike_authorized()
        test_node_7_sync_v5()
        print("\nALL V5 TESTS PASSED SUCCESSFULLY (v5.0.0-atlatl)")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
