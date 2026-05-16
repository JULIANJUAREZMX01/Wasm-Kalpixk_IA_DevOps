import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add python dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.kalpixk_api import app

client = TestClient(app)

@pytest.fixture
def production_env(monkeypatch):
    monkeypatch.setenv("KALPIXK_ENV", "production")
    monkeypatch.setenv("KALPIXK_API_KEY", "supersecret")

def test_simulate_start_no_auth(production_env):
    response = client.post("/api/simulate/start")
    # Should be 403 or 401 depending on how APIKeyHeader is configured without key
    # Current implementation of verify_api_key raises 403 for invalid/missing keys
    assert response.status_code == 403

def test_simulate_stop_no_auth(production_env):
    response = client.post("/api/simulate/stop")
    assert response.status_code == 403

def test_simulate_status_no_auth(production_env):
    response = client.get("/api/simulate/status")
    assert response.status_code == 403

def test_simulate_start_with_auth(production_env):
    response = client.post("/api/simulate/start", headers={"X-Kalpixk-Key": "supersecret"})
    # It might return 200 or some other status depending on if it actually starts
    # but it shouldn't be 403.
    assert response.status_code != 403
