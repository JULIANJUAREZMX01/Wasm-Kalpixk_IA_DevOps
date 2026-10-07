import pytest
from httpx import ASGITransport, AsyncClient
from python.api.kalpixk_api import app

HEADERS = {"X-Kalpixk-Key": "development_secret"}

@pytest.mark.asyncio
async def test_embedded_node_sync_healthy():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "node_id": "NODE-10-EMBEDDED-01",
            "firmware_version": "v1.0.0",
            "firmware_hash": "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890",
            "hardware_tampered": False,
            "cpu_load_pct": 12.5,
            "battery_pct": 98.0,
            "active_threats_detected": 0,
        }
        res = await ac.post("/api/v1/guerrilla/embedded_node/sync", json=payload, headers=HEADERS)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "HEALTHY"
        assert data["mesh_node_type"] == "NODE-10: EMBEDDED_NODE_DEFENDER"
        assert data["tamper_alert"] is False

@pytest.mark.asyncio
async def test_embedded_node_sync_tampered():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "node_id": "NODE-10-EMBEDDED-02",
            "firmware_version": "v1.0.0",
            "firmware_hash": "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890",
            "hardware_tampered": True,
            "cpu_load_pct": 99.0,
            "battery_pct": 45.0,
            "active_threats_detected": 3,
        }
        res = await ac.post("/api/v1/guerrilla/embedded_node/sync", json=payload, headers=HEADERS)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "COMPROMISED"
        assert data["tamper_alert"] is True
