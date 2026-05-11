import os

import aiosqlite
import pytest

from python.db.database import get_alerts, init_db, insert_alert

DB_TEST_PATH = "./test_kalpixk_alerts.db"

@pytest.fixture(autouse=True)
async def setup_db():
    os.environ["KALPIXK_DB_PATH"] = DB_TEST_PATH
    if os.path.exists(DB_TEST_PATH):
        os.remove(DB_TEST_PATH)
    await init_db()
    yield
    if os.path.exists(DB_TEST_PATH):
        os.remove(DB_TEST_PATH)

@pytest.mark.asyncio
async def test_init_db_creates_table():
    async with aiosqlite.connect(DB_TEST_PATH) as db:
        async with db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'") as cursor:
            row = await cursor.fetchone()
            assert row is not None

@pytest.mark.asyncio
async def test_insert_and_retrieve_alert():
    alert_data = {
        "ts": "2023-10-27T10:00:00Z",
        "ip": "127.0.0.1",
        "anomaly_score": 0.85,
        "event_type": "ssh_login",
        "severity": "HIGH",
        "technique": "Brute Force",
        "confidence": 0.9,
        "features_json": [0.1] * 32,
        "source": "agent"
    }
    await insert_alert(alert_data)

    alerts, total = await get_alerts(limit=10)
    assert total == 1
    assert len(alerts) == 1
    assert alerts[0]["anomaly_score"] == 0.85
    assert alerts[0]["severity"] == "HIGH"
    assert alerts[0]["features_json"] == [0.1] * 32

@pytest.mark.asyncio
async def test_get_alerts_filter_by_severity():
    alerts_to_insert = [
        {"ts": "2023-10-27T10:00:00Z", "anomaly_score": 0.9, "severity": "CRITICAL"},
        {"ts": "2023-10-27T10:01:00Z", "anomaly_score": 0.7, "severity": "HIGH"},
        {"ts": "2023-10-27T10:02:00Z", "anomaly_score": 0.3, "severity": "LOW"},
    ]
    for alert in alerts_to_insert:
        await insert_alert(alert)

    # Filter by CRITICAL
    alerts, total = await get_alerts(severity_filter="CRITICAL")
    assert total == 1
    assert alerts[0]["severity"] == "CRITICAL"

    # Filter by HIGH
    alerts, total = await get_alerts(severity_filter="HIGH")
    assert total == 1
    assert alerts[0]["severity"] == "HIGH"

@pytest.mark.asyncio
async def test_get_alerts_since():
    alerts_to_insert = [
        {"ts": "2023-10-27T10:00:00Z", "anomaly_score": 0.9, "severity": "CRITICAL"},
        {"ts": "2023-10-27T11:00:00Z", "anomaly_score": 0.7, "severity": "HIGH"},
    ]
    for alert in alerts_to_insert:
        await insert_alert(alert)

    alerts, total = await get_alerts(since_ts="2023-10-27T10:30:00Z")
    assert total == 1
    assert alerts[0]["ts"] == "2023-10-27T11:00:00Z"
