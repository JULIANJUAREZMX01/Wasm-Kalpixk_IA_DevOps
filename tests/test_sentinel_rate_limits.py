
import pytest
from fastapi.testclient import TestClient
import os
import sys
import time

# Add the root directory to sys.path to allow importing from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    monkeypatch.setenv("KALPIXK_API_KEY", "testkey")
    monkeypatch.setenv("ENV", "development")

def test_rate_limiting_report():
    # We need a mock for Request if we were calling the function directly,
    # but TestClient handles the FastAPI request context.

    # First 5 requests should pass (returning 404 or 200 depending on file existence, but not 429)
    for _ in range(5):
        response = client.get("/api/v1/report", headers={"X-Kalpixk-Key": "testkey"})
        assert response.status_code != 429

    # 6th request should be rate limited
    response = client.get("/api/v1/report", headers={"X-Kalpixk-Key": "testkey"})
    assert response.status_code == 429

def test_rate_limiting_status():
    for _ in range(10):
        response = client.get("/api/v1/status", headers={"X-Kalpixk-Key": "testkey"})
        assert response.status_code != 429

    response = client.get("/api/v1/status", headers={"X-Kalpixk-Key": "testkey"})
    assert response.status_code == 429

def test_rate_limiting_honeypot():
    # First request should pass
    response = client.get("/api/v1/retaliate/exfiltrate")
    assert response.status_code == 200

    # 2nd request should be rate limited (1/minute)
    response = client.get("/api/v1/retaliate/exfiltrate")
    assert response.status_code == 429
