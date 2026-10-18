import pytest
from httpx import ASGITransport, AsyncClient
from python.api.kalpixk_api import app

HEADERS = {"X-Kalpixk-Key": "development_secret"}

@pytest.mark.asyncio
async def test_embedded_node_sync_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(headers=HEADERS, transport=transport, base_url="http://test") as client:
        payload = {
            "node_id": "embedded-arm64-node-01",
            "firmware_hash": "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
            "hardware_status": "OK",
            "tamper_detected": False,
            "threat_events": [],
            "embedded_key": "valid-node-key-123"
        }
        response = await client.post("/api/v1/guerrilla/embedded_node/sync", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SYNCHRONIZED"
        assert data["node_id"] == "embedded-arm64-node-01"
        assert data["firmware_valid"] is True
        assert "active_threshold" in data

@pytest.mark.asyncio
async def test_embedded_node_sync_tamper_detected():
    transport = ASGITransport(app=app)
    async with AsyncClient(headers=HEADERS, transport=transport, base_url="http://test") as client:
        payload = {
            "node_id": "embedded-arm64-node-02",
            "firmware_hash": "corrupted_hash",
            "hardware_status": "TAMPER_ALERT_GPIO_TRIGGERED",
            "tamper_detected": True,
            "threat_events": [{"event": "firmware_tamper"}],
            "embedded_key": "node-key"
        }
        response = await client.post("/api/v1/guerrilla/embedded_node/sync", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CRITICAL_TAMPER"
        assert data["firmware_valid"] is False
