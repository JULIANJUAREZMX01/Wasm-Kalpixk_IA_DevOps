
import pytest
from fastapi.testclient import TestClient
from python.api.kalpixk_api import app
import os

client = TestClient(app)

def test_simulation_endpoints_should_require_auth():
    """
    This test verifies that simulation endpoints require authentication in production.
    """
    os.environ["KALPIXK_ENV"] = "production"
    os.environ["KALPIXK_API_KEY"] = "testkey"

    # Start simulation - no key
    response = client.post("/api/simulate/start")
    assert response.status_code == 403

    # Stop simulation - no key
    response = client.post("/api/simulate/stop")
    assert response.status_code == 403

    # Status simulation - no key
    response = client.get("/api/simulate/status")
    assert response.status_code == 403

    # Start simulation - with key
    response = client.post("/api/simulate/start", headers={"X-Kalpixk-Key": "testkey"})
    # Should not be 403
    assert response.status_code != 403

    # Cleanup env
    del os.environ["KALPIXK_ENV"]
    del os.environ["KALPIXK_API_KEY"]

def test_simulation_endpoints_dev_auth():
    """
    In development, if KALPIXK_API_KEY is set, it should still be checked.
    """
    os.environ["KALPIXK_ENV"] = "development"
    os.environ["KALPIXK_API_KEY"] = "devkey"

    # No key
    response = client.post("/api/simulate/start")
    assert response.status_code == 403

    # Wrong key
    response = client.post("/api/simulate/start", headers={"X-Kalpixk-Key": "wrong"})
    assert response.status_code == 403

    # Correct key
    response = client.post("/api/simulate/start", headers={"X-Kalpixk-Key": "devkey"})
    assert response.status_code != 403

    # Cleanup
    del os.environ["KALPIXK_API_KEY"]
