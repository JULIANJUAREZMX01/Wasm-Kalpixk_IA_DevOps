"""
Tests para db/database.py
Ejecutar: cd python && uv run pytest tests/test_database.py -v
"""
import os

import aiosqlite
import pytest

from db.database import get_alerts, init_db, insert_alert

DB_TEST_PATH = "/tmp/test_kalpixk_alerts_pytest.db"
os.environ["KALPIXK_DB_PATH"] = DB_TEST_PATH


@pytest.fixture(autouse=True)
def clean_db_path():
    """Limpia el archivo de DB antes y después de cada test."""
    if os.path.exists(DB_TEST_PATH):
        os.remove(DB_TEST_PATH)
    yield
    if os.path.exists(DB_TEST_PATH):
        os.remove(DB_TEST_PATH)


@pytest.mark.asyncio
async def test_init_db_creates_table():
    await init_db()
    async with aiosqlite.connect(DB_TEST_PATH) as db:
        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'"
        ) as cursor:
            row = await cursor.fetchone()
            assert row is not None, "Tabla 'alerts' no fue creada"


@pytest.mark.asyncio
async def test_insert_and_retrieve_alert():
    await init_db()
    alert_data = {
        "ts": "2023-10-27T10:00:00Z",
        "ip": "127.0.0.1",
        "anomaly_score": 0.85,
        "event_type": "ssh_login",
        "severity": "HIGH",
        "technique": "Brute Force",
        "confidence": 0.9,
        "source": "agent",
    }
    await insert_alert(alert_data)

    alerts, total = await get_alerts(limit=10)
    assert total == 1
    assert len(alerts) == 1
    assert alerts[0]["anomaly_score"] == pytest.approx(0.85)
    assert alerts[0]["severity"] == "HIGH"


@pytest.mark.asyncio
async def test_get_alerts_filter_by_severity():
    await init_db()
    for a in [
        {"ts": "2023-10-27T10:00:00Z", "anomaly_score": 0.9, "severity": "CRITICAL"},
        {"ts": "2023-10-27T10:01:00Z", "anomaly_score": 0.7, "severity": "HIGH"},
        {"ts": "2023-10-27T10:02:00Z", "anomaly_score": 0.3, "severity": "LOW"},
    ]:
        await insert_alert(a)

    critical, total_c = await get_alerts(severity_filter="CRITICAL")
    assert total_c == 1
    assert critical[0]["severity"] == "CRITICAL"

    high, total_h = await get_alerts(severity_filter="HIGH")
    assert total_h == 1
    assert high[0]["severity"] == "HIGH"


@pytest.mark.asyncio
async def test_get_alerts_since():
    await init_db()
    for a in [
        {"ts": "2023-10-27T10:00:00Z", "anomaly_score": 0.9, "severity": "CRITICAL"},
        {"ts": "2023-10-27T11:00:00Z", "anomaly_score": 0.7, "severity": "HIGH"},
    ]:
        await insert_alert(a)

    alerts, total = await get_alerts(since_ts="2023-10-27T10:30:00Z")
    assert total == 1
    assert alerts[0]["ts"] == "2023-10-27T11:00:00Z"
