import os
import pytest
from fastapi.testclient import TestClient
from main import app

def test_metrics_authenticated_when_key_set():
    os.environ["KALPIXK_API_KEY"] = "secret123"
    client = TestClient(app)
    response = client.get("/metrics", headers={"X-Kalpixk-Key": "secret123"})
    assert response.status_code == 200
    assert "metrics" in response.json()

def test_metrics_forbidden_with_wrong_key():
    os.environ["KALPIXK_API_KEY"] = "secret123"
    client = TestClient(app)
    response = client.get("/metrics", headers={"X-Kalpixk-Key": "wrong"})
    assert response.status_code == 403

def test_train_validation_error():
    os.environ["KALPIXK_API_KEY"] = "secret123"
    client = TestClient(app)
    # n_samples too large
    response = client.post("/train", json={"n_samples": 100000, "epochs": 1}, headers={"X-Kalpixk-Key": "secret123"})
    assert response.status_code == 422

def test_production_fail_closed():
    os.environ["ENV"] = "production"
    if "KALPIXK_API_KEY" in os.environ:
        del os.environ["KALPIXK_API_KEY"]

    client = TestClient(app)
    response = client.get("/metrics", headers={"X-Kalpixk-Key": "any"})
    assert response.status_code == 500

    os.environ["ENV"] = "development" # Reset
