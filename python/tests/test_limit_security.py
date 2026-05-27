

import pytest

from python.db.database import get_alerts, init_db, insert_alert


@pytest.fixture
async def setup_db(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test_limit.db")
    monkeypatch.setenv("KALPIXK_DB_PATH", db_file)
    await init_db()

    # Insert 10 alerts
    for i in range(10):
        await insert_alert({
            "ts": f"2023-10-27T10:00:0{i}Z",
            "ip": "1.1.1.1",
            "anomaly_score": 0.1 * i,
            "severity": "LOW"
        })
    return db_file

@pytest.mark.asyncio
async def test_get_alerts_limit_mitigation(setup_db):
    # Test negative limit
    alerts, total = await get_alerts(limit=-1)
    # Our mitigation should force limit to at least 1
    assert len(alerts) == 1
    assert total == 10

    # Test zero limit
    alerts, total = await get_alerts(limit=0)
    assert len(alerts) == 1

    # Test non-integer limit
    alerts, total = await get_alerts(limit="abc")
    # Should fallback to 100
    assert len(alerts) == 10

    # Test very large limit (app-level capping might still apply elsewhere,
    # but database.py just uses what it's given after forcing min 1)
    alerts, total = await get_alerts(limit=1000)
    assert len(alerts) == 10
