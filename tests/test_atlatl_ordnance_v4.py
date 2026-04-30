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

def test_health_v4():
    print("Testing health v4...")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == "5.0.0-atlatl"
    print("Health v4: OK")

def test_node_7_sync_success():
    print("Testing node-7 sync success...")
    payload = {
        "node_id": "test-node",
        "threats": ["192.168.1.100"],
        "timestamp": int(time.time()),
        "version": "4.0.0-atlatl"
    }
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    signature = hmac.new(API_KEY.encode(), data, hashlib.sha256).hexdigest()

    headers = {
        "X-Kalpixk-Key": API_KEY,
        "X-Kalpixk-Signature": signature
    }

    response = client.post("/api/v1/nodes/sync", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["mesh_update"] == "v4.0-atlatl"
    print("Node-7 sync success: OK")

def test_node_7_sync_failure():
    print("Testing node-7 sync failure...")
    payload = {
        "node_id": "malicious-node",
        "threats": ["1.2.3.4"],
        "timestamp": int(time.time()),
        "version": "4.0.0-atlatl"
    }
    headers = {
        "X-Kalpixk-Key": API_KEY,
        "X-Kalpixk-Signature": "wrong-signature"
    }
    response = client.post("/api/v1/nodes/sync", json=payload, headers=headers)
    assert response.status_code in [401, 403]
    print("Node-7 sync failure: OK")

def test_honeypot_exfiltrate():
    print("Testing honeypot exfiltrate...")
    response = client.get("/api/v1/retaliate/exfiltrate")
    assert response.status_code in [200, 429]
    print("Honeypot exfiltrate: OK")

def test_phase_black_retaliation():
    print("Testing phase black retaliation...")
    result = atlatl.trigger_retaliation(0.96, "1.1.1.1")
    assert result["v5_status"] == "STRIKE_COMPLETE"
    print("Phase black retaliation: OK")

if __name__ == "__main__":
    try:
        test_health_v4()
        test_node_7_sync_success()
        test_node_7_sync_failure()
        test_honeypot_exfiltrate()
        test_phase_black_retaliation()
        print("\nALL TESTS PASSED SUCCESSFULLY (v4.0.0-atlatl)")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
