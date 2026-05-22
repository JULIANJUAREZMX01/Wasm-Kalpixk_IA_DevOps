"""
Security tests for database pagination bypass.
"""

import pytest

from python.db.database import get_alerts, init_db, insert_alert


@pytest.fixture
async def tmp_db(monkeypatch, tmp_path):
    db_file = str(tmp_path / "test_security.db")
    monkeypatch.setenv("KALPIXK_DB_PATH", db_file)
    await init_db()
    return db_file

@pytest.mark.asyncio
async def test_get_alerts_limit_minus_one_bypass(tmp_db):
    # Insert 10 alerts
    for i in range(10):
        await insert_alert({
            "ts": f"2023-10-27T10:00:{i:02d}Z",
            "anomaly_score": 0.1 * i,
            "severity": "LOW",
        })

    # The vulnerability was that limit=-1 bypassed the limit in SQLite
    # Now it should be constrained to 1 if we passed -1
    alerts, total = await get_alerts(limit=-1)

    # After fix, it should return only 1 alert (the default for invalid limit)
    assert len(alerts) == 1
    assert total == 10 # Total count should still be 10
