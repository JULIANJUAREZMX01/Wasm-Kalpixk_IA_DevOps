import pytest
from fastapi.testclient import TestClient

from python.api.kalpixk_api import app

client = TestClient(app)
client.headers = {"X-Kalpixk-Key": "development_secret"}


@pytest.mark.asyncio
async def test_get_alerts_pagination_hardening():
    # Test negative limit
    response = client.get("/api/alerts?limit=-1")
    assert response.status_code == 200

    # Test zero limit
    response = client.get("/api/alerts?limit=0")
    assert response.status_code == 200

    # Test excessive limit
    response = client.get("/api/alerts?limit=1000")
    assert response.status_code == 200
    # Should be clamped to 500

    # Test invalid limit (non-integer) - FastAPI handles this and returns 422
    response = client.get("/api/alerts?limit=abc")
    assert response.status_code == 422
