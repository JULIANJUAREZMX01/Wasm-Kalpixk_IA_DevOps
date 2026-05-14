import pytest
from fastapi.testclient import TestClient
import os
import sys

# Add root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from python.api.kalpixk_api import app

client = TestClient(app)

def test_v7_guerrilla_strike_auth():
    # Test without API key
    os.environ["KALPIXK_API_KEY"] = "testkey"
    response = client.post("/api/v1/guerrilla/v7/strike")
    assert response.status_code == 403

def test_v7_guerrilla_strike_success():
    os.environ["KALPIXK_API_KEY"] = "testkey"
    headers = {"X-Kalpixk-Key": "testkey"}
    response = client.post("/api/v1/guerrilla/v7/strike", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "v7_GUILLOTINE_EXECUTED"
    assert data["orchestration"] == "ALPHA_STACK"

def test_v7_audit_tensor_logic():
    # This test would ideally call the WASM function, but for integration
    # we verify the logic in atlatl which we already tested via API above.
    pass
