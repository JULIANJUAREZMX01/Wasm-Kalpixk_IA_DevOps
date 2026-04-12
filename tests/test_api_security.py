
import pytest
from fastapi.testclient import TestClient
import os
import sys
import numpy as np

# Add the root directory to sys.path to allow importing from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.main import app, detector

client = TestClient(app)

@pytest.fixture(autouse=True, scope="module")
def train_detector():
    # Force train the detector for API tests so it doesn't fail on predict
    if not detector.is_trained:
        data = np.random.randn(100, 32).astype(np.float32)
        detector.train(data, epochs=5)

@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    monkeypatch.setenv("KALPIXK_API_KEY", "testkey")

def test_metrics_unauthenticated():
    response = client.get("/api/v1/metrics")
    assert response.status_code == 403

def test_metrics_authenticated():
    response = client.get("/api/v1/metrics", headers={"X-Kalpixk-Key": "testkey"})
    assert response.status_code == 200

def test_detect_unauthenticated():
    payload = {"features": [0.0]*32}
    response = client.post("/api/v1/detect", json=payload)
    assert response.status_code == 403

def test_detect_authenticated_valid():
    payload = {"features": [0.0]*32}
    response = client.post("/api/v1/detect", json=payload, headers={"X-Kalpixk-Key": "testkey"})
    assert response.status_code == 200

def test_detect_invalid_length():
    payload = {"features": [0.0]*10} # Invalid length (not 32)
    response = client.post("/api/v1/detect", json=payload, headers={"X-Kalpixk-Key": "testkey"})
    assert response.status_code == 422 # Pydantic validation error

def test_simulate_unauthenticated():
    # Simulate endpoint was removed in v2
    response = client.get("/api/v1/simulate/cpu_spike")
    assert response.status_code == 404

def test_simulate_authenticated():
    # Simulate endpoint was removed in v2
    response = client.get("/api/v1/simulate/cpu_spike", headers={"X-Kalpixk-Key": "testkey"})
    assert response.status_code == 404

def test_health_public():
    # Health should be public
    response = client.get("/health")
    assert response.status_code == 200

def test_production_fails_if_no_key(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("KALPIXK_API_KEY", raising=False)

    response = client.get("/api/v1/metrics")
    assert response.status_code == 500
    assert response.json()["detail"] == "API Key not configured"
