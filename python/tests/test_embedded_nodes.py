import pytest
from httpx import ASGITransport, AsyncClient

from python.api.kalpixk_api import app


@pytest.mark.asyncio
async def test_sync_embedded_node_telemetry_healthy():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/guerrilla/embedded_node/sync",
            headers={"X-Kalpixk-Key": "development_secret"},
            json={
                "node_id": "NODE-10-EMBEDDED-01",
                "firmware_version": "v9.0.0-XOCHIMILCO",
                "tamper_flag": False,
                "hardware_probe_detected": False,
                "metrics": {"cpu_temp": 42.5},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "HEALTHY"
        assert data["node_id"] == "NODE-10-EMBEDDED-01"
        assert data["mesh_nodes_active"] == 10
        assert data["action_required"] is False


@pytest.mark.asyncio
async def test_sync_embedded_node_telemetry_tamper_alert():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/guerrilla/embedded_node/sync",
            headers={"X-Kalpixk-Key": "development_secret"},
            json={
                "node_id": "NODE-10-EMBEDDED-02",
                "firmware_version": "v9.0.0-XOCHIMILCO",
                "tamper_flag": True,
                "hardware_probe_detected": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "TAMPER_ALERT"
        assert data["action_required"] is True
