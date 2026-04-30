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

def test_node_7_sync_success():
    print("Testing node-7 sync success...")
    payload = {
        "node_id": "test-node",
        "threats": ["192.168.1.100"],
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
    assert response.json()["integrity"] == "verified"
    print("Node-7 sync success: OK")

def test_node_7_sync_failure():
    print("Testing node-7 sync failure...")
    payload = {
        "node_id": "malicious-node",
        "threats": ["1.2.3.4"],
        "timestamp": int(time.time()),
        "version": "5.0.0-atlatl"
    }
    headers = {
        "X-Kalpixk-Key": API_KEY,
        "X-Kalpixk-Signature": "wrong-signature"
    }
    response = client.post("/api/v1/nodes/sync", json=payload, headers=headers)
    # API returns 403 for signature violation (MESH_INTEGRITY_VIOLATION)
    assert response.status_code == 403
    print("Node-7 sync failure: OK")

def test_v5_strike_manual():
    print("Testing manual v5 strike...")
    payload = {"target": "10.0.0.5"}
    headers = {"X-Kalpixk-Key": API_KEY}
    response = client.post("/api/v1/retaliate/v5_strike", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["v5_status"] == "STRIKE_COMPLETE"
    print("Manual v5 strike: OK")

def test_honeypot_exfiltrate():
    print("Testing honeypot exfiltrate...")
    response = client.get("/api/v1/retaliate/exfiltrate")
    assert response.status_code == 200
    assert len(response.content) > 0
    print("Honeypot exfiltrate: OK")

def test_phase_black_retaliation():
    print("Testing phase black retaliation...")
    result = atlatl.trigger_retaliation(0.95, "1.1.1.1")
    assert result["action"] == "EXTERMINATE"
    assert result["v5_strike"] == "engaged"
    print("Phase black retaliation: OK")

if __name__ == "__main__":
    try:
        test_health_v5()
        test_node_7_sync_success()
        test_node_7_sync_failure()
        test_v5_strike_manual()
        test_honeypot_exfiltrate()
        test_phase_black_retaliation()
        print("\nALL TESTS PASSED SUCCESSFULLY (v5.0.0-atlatl)")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
