import pytest

from python.db.database import get_alerts, init_db, insert_alert


@pytest.fixture
def tmp_db(monkeypatch, tmp_path):
    db_file = str(tmp_path / "test_pagination_security.db")
    monkeypatch.setenv("KALPIXK_DB_PATH", db_file)
    return db_file


@pytest.mark.asyncio
async def test_get_alerts_clamps_negative_and_oversized_limits(tmp_db):
    await init_db()
    for index in range(3):
        await insert_alert(
            {
                "ts": f"2026-01-01T00:00:0{index}Z",
                "ip": f"192.0.2.{index + 1}",
                "anomaly_score": 0.1 + index,
            }
        )

    negative_alerts, negative_total = await get_alerts(limit=-1)
    oversized_alerts, oversized_total = await get_alerts(limit=999999)
    invalid_alerts, invalid_total = await get_alerts(limit="invalid")

    assert negative_total == 3
    assert len(negative_alerts) == 1
    assert oversized_total == 3
    assert len(oversized_alerts) == 3
    assert invalid_total == 3
    assert len(invalid_alerts) == 3


@pytest.mark.asyncio
async def test_api_alerts_clamping_endpoint(tmp_db):
    import httpx

    from python.api.kalpixk_api import app

    await init_db()
    for index in range(5):
        await insert_alert(
            {
                "ts": f"2026-01-01T00:00:0{index}Z",
                "ip": f"10.0.0.{index + 1}",
                "anomaly_score": 0.8,
            }
        )

    async with httpx.AsyncClient(
        headers={"X-Kalpixk-Key": "development_secret"},
        transport=httpx.ASGITransport(app=app),
        base_url="http://localhost:8000",
    ) as c:
        resp = await c.get("/api/alerts?limit=-50")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["alerts"]) == 1

        resp_over = await c.get("/api/alerts?limit=1000")
        assert resp_over.status_code == 200
        data_over = resp_over.json()
        assert len(data_over["alerts"]) == 5
