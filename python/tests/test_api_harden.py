import os
import pytest
from fastapi.testclient import TestClient
from python.api.kalpixk_api import app

@pytest.fixture
def client():
    # Clear rate limits for each test if possible, or use a new client
    return TestClient(app)

def test_rate_limiting_health(client):
    # The limit is 30/minute
    for _ in range(30):
        response = client.get("/api/health")
        assert response.status_code == 200

    response = client.get("/api/health")
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.text

def test_unauthenticated_access_to_status():
    # If KALPIXK_API_KEY is not set and ENV is not production, it might allow access or not
    # Based on our change, if expected_key is None and env is development, it allows.
    # Let's force it to require auth
    os.environ["KALPIXK_API_KEY"] = "test_secret"
    os.environ["KALPIXK_ENV"] = "production"

    client = TestClient(app)
    response = client.get("/status")
    assert response.status_code == 403

    response = client.get("/status", headers={"X-Kalpixk-Key": "test_secret"})
    assert response.status_code == 200
