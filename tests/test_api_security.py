import pytest
from fastapi.testclient import TestClient
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.main import app, detector, monitor

@pytest.fixture(scope="module", autouse=True)
def train_detector_for_tests():
    """Ensure detector is trained before running API tests."""
    if not detector.is_trained:
        data = monitor.generate_normal_baseline(n_samples=100)
        detector.train(data, epochs=10)

client = TestClient(app)

def test_health_no_key_needed():
    """Health check should be public."""
    response = client.get("/health")
    assert response.status_code == 200

def test_metrics_requires_key():
    """Metrics should require API key."""
    os.environ["KALPIXK_API_KEY"] = "secret-key"
    response = client.get("/metrics")
    assert response.status_code == 403

    response = client.get("/metrics", headers={"X-Kalpixk-Key": "wrong-key"})
    assert response.status_code == 403

    response = client.get("/metrics", headers={"X-Kalpixk-Key": "secret-key"})
    assert response.status_code == 200

def test_detect_requires_key_and_valid_input():
    """Detect endpoint should require key and strict input validation."""
    os.environ["KALPIXK_API_KEY"] = "secret-key"

    # 1. No key
    response = client.post("/detect", json={"features": [0.0]*32})
    assert response.status_code == 403

    # 2. Valid key, invalid input (wrong length)
    response = client.post("/detect",
                           headers={"X-Kalpixk-Key": "secret-key"},
                           json={"features": [0.0]*31})
    assert response.status_code == 422 # Pydantic validation error

    # 3. Valid key, valid input
    response = client.post("/detect",
                           headers={"X-Kalpixk-Key": "secret-key"},
                           json={"features": [0.0]*32})
    assert response.status_code == 200
    assert "anomalies" in response.json()

def test_simulate_requires_key():
    """Simulate endpoint should require API key."""
    os.environ["KALPIXK_API_KEY"] = "secret-key"
    response = client.get("/simulate/cpu_spike")
    assert response.status_code == 403

    response = client.get("/simulate/cpu_spike", headers={"X-Kalpixk-Key": "secret-key"})
    assert response.status_code == 200

def test_production_fails_if_no_key_set():
    """In production, API should fail with 500 if KALPIXK_API_KEY is missing."""
    os.environ["ENV"] = "production"
    if "KALPIXK_API_KEY" in os.environ:
        del os.environ["KALPIXK_API_KEY"]

    response = client.get("/metrics")
    assert response.status_code == 500
    assert "API Key not configured" in response.json()["detail"]

    # Reset for other tests
    os.environ["ENV"] = "development"
