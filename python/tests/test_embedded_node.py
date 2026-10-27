import pytest
from httpx import ASGITransport, AsyncClient

from python.api.kalpixk_api import app

HEADERS = {"X-Kalpixk-Key": "development_secret"}

@pytest.mark.asyncio
async def test_embedded_node_sync_healthy():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver", headers=HEADERS) as client:
        payload = {
            "node_id": "embedded-alpha-01",
            "firmware_version": "v9.0.0-XOCHIMILCO",
            "firmware_tampered": False,
            "bus_sniffing_detected": False,
            "cpu_usage_pct": 12.5,
            "ram_usage_pct": 45.0,
            "raw_logs": ["heartbeat ok"]
        }
        res = await client.post("/api/v1/guerrilla/embedded_node/sync", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["node_id"] == "embedded-alpha-01"
        assert data["status"] == "OK"
        assert data["tamper_detected"] is False
        assert data["mesh_action"] == "NODE_HEALTHY"

@pytest.mark.asyncio
async def test_embedded_node_sync_tamper_detected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver", headers=HEADERS) as client:
        payload = {
            "node_id": "embedded-beta-02",
            "firmware_version": "v9.0.0-XOCHIMILCO",
            "firmware_tampered": True,
            "bus_sniffing_detected": True,
            "cpu_usage_pct": 99.0,
            "ram_usage_pct": 88.0,
            "raw_logs": ["WARNING: SPI bus anomaly"]
        }
        res = await client.post("/api/v1/guerrilla/embedded_node/sync", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["node_id"] == "embedded-beta-02"
        assert data["status"] == "CRITICAL_TAMPER_ALERT"
        assert data["tamper_detected"] is True
        assert data["retaliation_armed"] is True
        assert data["mesh_action"] == "REISOLATE_NODE"

        # Verify alert stored in DB has timezone-aware ISO8601 UTC timestamp
        alerts_res = await client.get("/api/alerts?limit=10")
        assert alerts_res.status_code == 200
        alerts = alerts_res.json()["alerts"]
        tamper_alerts = [a for a in alerts if a.get("source") == "embedded-node-embedded-beta-02"]
        assert len(tamper_alerts) == 1
        ts_str = tamper_alerts[0]["ts"]
        assert ts_str.endswith("+00:00") or ts_str.endswith("Z"), f"Timestamp '{ts_str}' must be timezone-aware UTC"
