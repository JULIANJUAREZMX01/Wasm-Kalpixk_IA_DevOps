import pytest
from fastapi.testclient import TestClient
from src.api.main import app
import os

def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

def test_api_auth_required():
    os.environ["ENV"] = "production"
    os.environ["KALPIXK_API_KEY"] = "testsecret"
    with TestClient(app) as client:
        # No key
        response = client.get("/api/v1/metrics")
        assert response.status_code == 403

        # Correct key
        response = client.get("/api/v1/metrics", headers={"X-Kalpixk-Key": "testsecret"})
        assert response.status_code == 200
    os.environ["ENV"] = "development"

def test_api_detect():
    with TestClient(app) as client:
        payload = {"features": [0.5]*32}
        # In development, if KALPIXK_API_KEY is not set, it should allow
        if "KALPIXK_API_KEY" in os.environ:
            del os.environ["KALPIXK_API_KEY"]
        response = client.post("/api/v1/detect", json=payload)
        assert response.status_code == 200
        assert "anomalies" in response.json()
