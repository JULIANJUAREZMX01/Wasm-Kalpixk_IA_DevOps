
import pytest
from fastapi.testclient import TestClient
import os
import json
import importlib
import sys

# Mocking env before import
os.environ["KALPIXK_API_KEY"] = "sentinel_test_key"

from src.api.main import app, detector

client = TestClient(app)

@pytest.fixture(autouse=True, scope="module")
def train_detector():
    if not detector.is_trained:
        # Simple mock training
        detector.is_trained = True
        detector.threshold = 0.7

def test_threat_report_constraints():
    # node_id too long (> 64)
    payload = {
        "node_id": "a" * 65,
        "threats": ["1.1.1.1"],
        "timestamp": 12345
    }
    response = client.post("/api/v1/nodes/sync", json=payload, headers={"X-Kalpixk-Key": "sentinel_test_key"})
    assert response.status_code == 422
    assert "node_id" in response.text

    # threats list too long (> 1000)
    payload = {
        "node_id": "test_node",
        "threats": ["1.1.1.1"] * 1001,
        "timestamp": 12345
    }
    response = client.post("/api/v1/nodes/sync", json=payload, headers={"X-Kalpixk-Key": "sentinel_test_key"})
    assert response.status_code == 422
    assert "threats" in response.text

    # individual threat string too long (> 256)
    payload = {
        "node_id": "test_node",
        "threats": ["b" * 257],
        "timestamp": 12345
    }
    response = client.post("/api/v1/nodes/sync", json=payload, headers={"X-Kalpixk-Key": "sentinel_test_key"})
    assert response.status_code == 422
    assert "threats" in response.text

    # Valid payload
    payload = {
        "node_id": "test_node",
        "threats": ["1.1.1.1"] * 10,
        "timestamp": 12345
    }
    response = client.post("/api/v1/nodes/sync", json=payload, headers={"X-Kalpixk-Key": "sentinel_test_key"})
    assert response.status_code == 200

def test_cors_logic_production(monkeypatch):
    # Mock environment for production with NO CORS_ORIGINS
    monkeypatch.setenv("KALPIXK_ENV", "production")
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    # Reload the module to trigger the logic
    import src.api.main as api_main
    importlib.reload(api_main)

    assert api_main.cors_origins == []

def test_cors_logic_development(monkeypatch):
    # Mock environment for development with NO CORS_ORIGINS
    monkeypatch.setenv("KALPIXK_ENV", "development")
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    # Reload the module to trigger the logic
    import src.api.main as api_main
    importlib.reload(api_main)

    assert api_main.cors_origins == ["*"]

def test_cors_logic_custom(monkeypatch):
    # Mock environment with custom CORS_ORIGINS
    custom_origins = ["https://example.com"]
    monkeypatch.setenv("CORS_ORIGINS", json.dumps(custom_origins))

    # Reload the module to trigger the logic
    import src.api.main as api_main
    importlib.reload(api_main)

    assert api_main.cors_origins == custom_origins
