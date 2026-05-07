import os

import pytest
from fastapi.testclient import TestClient

from python.api.kalpixk_api import app


@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def manage_env():
    # Save current env
    old_key = os.environ.get("KALPIXK_API_KEY")
    old_env = os.environ.get("KALPIXK_ENV")

    yield

    # Restore env
    if old_key is not None:
        os.environ["KALPIXK_API_KEY"] = old_key
    else:
        os.environ.pop("KALPIXK_API_KEY", None)

    if old_env is not None:
        os.environ["KALPIXK_ENV"] = old_env
    else:
        os.environ.pop("KALPIXK_ENV", None)

def test_rate_limiting_health(client):
    # The limit is 30/minute
    # We might need to handle the case where multiple tests run and hit the limit
    # But since this is a new client and the limiter is global, it's tricky.
    # However, for this single test it should be fine.
    for _ in range(30):
        response = client.get("/api/health")
        assert response.status_code == 200

    response = client.get("/api/health")
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.text

def test_unauthenticated_access_to_status():
    # Force production mode and a secret key
    os.environ["KALPIXK_API_KEY"] = "test_secret"
    os.environ["KALPIXK_ENV"] = "production"

    client = TestClient(app)
    response = client.get("/status")
    assert response.status_code == 403

    response = client.get("/status", headers={"X-Kalpixk-Key": "test_secret"})
    assert response.status_code == 200
