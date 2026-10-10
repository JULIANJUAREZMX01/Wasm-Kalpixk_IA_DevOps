import pytest
from httpx import ASGITransport, AsyncClient

from python.api.kalpixk_api import app

headers = {"X-Kalpixk-Key": "development_secret"}

@pytest.mark.asyncio
async def test_embedded_node_sync_nominal(monkeypatch):
    monkeypatch.setenv("KALPIXK_API_KEY", "development_secret")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "node_id": "NODE10-EMBEDDED-CEDIS01",
            "firmware_hash": "a1b2c3d4e5f67890123456789abcdef",
            "tamper_flag": False,
            "cpu_load": 24.5,
            "vram_mb": 128.0,
            "features": [0.3] * 32
        }
        response = await ac.post("/api/v1/guerrilla/embedded_node/sync", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["node_id"] == "NODE10-EMBEDDED-CEDIS01"
        assert data["status"] in ["NOMINAL", "ANOMALY_DETECTED"]

@pytest.mark.asyncio
async def test_embedded_node_sync_tamper(monkeypatch):
    monkeypatch.setenv("KALPIXK_API_KEY", "development_secret")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "node_id": "NODE10-EMBEDDED-CEDIS02",
            "firmware_hash": "a1b2c3d4e5f67890123456789abcdef",
            "tamper_flag": True,
            "cpu_load": 99.0,
            "vram_mb": 256.0,
        }
        response = await ac.post("/api/v1/guerrilla/embedded_node/sync", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "TAMPER_DETECTED"
        assert data["is_anomaly"] is True
        assert data["anomaly_score"] == 1.0
