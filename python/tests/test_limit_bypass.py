
import pytest
import os
from db.database import get_alerts, init_db, insert_alert

@pytest.fixture
async def tmp_db(monkeypatch, tmp_path):
    db_file = str(tmp_path / "test_limit.db")
    monkeypatch.setenv("KALPIXK_DB_PATH", db_file)
    await init_db()
    return db_file

@pytest.mark.asyncio
async def test_get_alerts_limit_minus_one_hardened(tmp_db):
    # Insert 5 alerts
    for i in range(5):
        await insert_alert({
            "ts": f"2023-10-27T10:00:0{i}Z",
            "anomaly_score": 0.1 * i,
            "severity": "LOW",
        })

    # Try with limit=-1
    # Hardened: should be constrained to at least 1
    alerts, total = await get_alerts(limit=-1)

    assert len(alerts) == 1
    assert total == 5

@pytest.mark.asyncio
async def test_get_alerts_limit_zero_hardened(tmp_db):
    # Insert 5 alerts
    for i in range(5):
        await insert_alert({
            "ts": f"2023-10-27T10:00:0{i}Z",
            "anomaly_score": 0.1 * i,
            "severity": "LOW",
        })

    # Try with limit=0
    # Hardened: should be constrained to at least 1
    alerts, total = await get_alerts(limit=0)

    assert len(alerts) == 1

@pytest.mark.asyncio
async def test_get_alerts_limit_large_hardened(tmp_db):
    # Insert 5 alerts
    for i in range(5):
        await insert_alert({
            "ts": f"2023-10-27T10:00:0{i}Z",
            "anomaly_score": 0.1 * i,
            "severity": "LOW",
        })

    # Try with very large limit
    # Hardened: should be constrained to 500
    # (Since we only have 5, it returns 5, but we check if it handles the large input)
    alerts, total = await get_alerts(limit=1000000)
    assert len(alerts) == 5
