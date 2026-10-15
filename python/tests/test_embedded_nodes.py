import pytest
from httpx import ASGITransport, AsyncClient

from python.api.kalpixk_api import app

HEADERS = {"X-Kalpixk-Key": "development_secret"}


@pytest.mark.asyncio
async def test_sync_embedded_node_normal():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        payload = {
            "node_id": "embedded_node_01",
            "firmware_hash": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
            "tampered": False,
            "threat_count": 0,
            "cpu_temp": 42.5,
            "memory_usage": 38.2,
        }
        response = await ac.post(
            "/api/v1/guerrilla/embedded_node/sync", json=payload, headers=HEADERS
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "synchronized"
        assert data["node_id"] == "embedded_node_01"
        assert data["tampered"] is False


@pytest.mark.asyncio
async def test_sync_embedded_node_tampered():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        payload = {
            "node_id": "embedded_node_02",
            "firmware_hash": "corrupted_hash_xyz",
            "tampered": True,
            "threat_count": 5,
            "cpu_temp": 78.1,
            "memory_usage": 91.0,
        }
        response = await ac.post(
            "/api/v1/guerrilla/embedded_node/sync", json=payload, headers=HEADERS
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alert_triggered"
        assert data["node_id"] == "embedded_node_02"
        assert data["tampered"] is True
        assert data["action"] == "lockdown_isolated_node"


@pytest.mark.asyncio
async def test_sync_embedded_node_invalid_payload():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        payload = {
            "node_id": "x" * 150,  # exceeds max_length 100
            "firmware_hash": "hash",
        }
        response = await ac.post(
            "/api/v1/guerrilla/embedded_node/sync", json=payload, headers=HEADERS
        )
        assert response.status_code == 422
