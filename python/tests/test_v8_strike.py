import os

import pytest
from fastapi.testclient import TestClient

from python.api.kalpixk_api import app


@pytest.fixture
def client():
    os.environ["KALPIXK_ENV"] = "development"
    os.environ["KALPIXK_API_KEY"] = "test_key"
    with TestClient(app) as c:
        yield c

def test_v8_strike_endpoint(client):
    headers = {"X-Kalpixk-Key": "test_key"}
    response = client.post("/api/v1/guerrilla/v8/strike", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "GUILLOTINE_EXECUTED_V8"
    assert data["impact"] == "DESTRUCTIVE_STAGE_8"
    assert data["bandwidth_saturation"] == "25GB/s"
    assert "v8_corrupt_remote_pointers" in data["collapse_results"]
    assert data["collapse_results"]["v8_corrupt_remote_pointers"] == "SUCCESS"

def test_v8_health_version(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "8.0.0-guerrilla"
    assert data["ensemble_version"] == "8.0.0-guerrilla"
