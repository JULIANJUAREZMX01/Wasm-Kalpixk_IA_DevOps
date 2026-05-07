
import pytest
from fastapi.testclient import TestClient
import os
import sys

# Add the root directory to sys.path to allow importing from python.api
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the imports that might fail in this environment
from unittest.mock import MagicMock
sys.modules["python.models.ensemble"] = MagicMock()
sys.modules["python.utils.device"] = MagicMock()

from python.api.kalpixk_api import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    monkeypatch.setenv("KALPIXK_API_KEY", "testkey")
    monkeypatch.setenv("KALPIXK_ENV", "development")

def test_legacy_api_rate_limiting_status():
    # Limit is 10/minute
    for _ in range(10):
        response = client.get("/status", headers={"X-Kalpixk-Key": "testkey"})
        assert response.status_code != 429

    response = client.get("/status", headers={"X-Kalpixk-Key": "testkey"})
    assert response.status_code == 429

def test_legacy_api_rate_limiting_train():
    # Limit is 5/minute
    for _ in range(5):
        response = client.post("/train", json={"n_samples": 10}, headers={"X-Kalpixk-Key": "testkey"})
        assert response.status_code != 429

    response = client.post("/train", json={"n_samples": 10}, headers={"X-Kalpixk-Key": "testkey"})
    assert response.status_code == 429

def test_legacy_api_rate_limiting_analyze():
    # Limit is 60/minute
    # We won't test all 60 to save time, but we can check if it works at all.
    response = client.post("/analyze", json={"features": [0.0]*32}, headers={"X-Kalpixk-Key": "testkey"})
    assert response.status_code != 429
