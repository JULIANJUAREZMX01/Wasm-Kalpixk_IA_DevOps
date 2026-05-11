"""
Tests para db/database.py
"""

import pytest

from db.database import get_alerts, init_db, insert_alert


@pytest.fixture
def tmp_db(monkeypatch, tmp_path):
    """Provee una base de datos temporal aislada para cada test."""
    db_file = str(tmp_path / "test_alerts.db")
    monkeypatch.setenv("KALPIXK_DB_PATH", db_file)
    return db_file


@pytest.mark.asyncio
async def test_init_db_creates_table(tmp_db):
    """Verifica que init_db crea la tabla alerts."""
    import aiosqlite
    await init_db()
    async with aiosqlite.connect(tmp_db) as db:
        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'"
        ) as cursor:
            row = await cursor.fetchone()
    assert row is not None, "Tabla 'alerts' no fue creada"


@pytest.mark.asyncio
async def test_insert_and_retrieve_alert(tmp_db):
    await init_db()
    await insert_alert({
        "ts": "2023-10-27T10:00:00Z",
        "anomaly_score": 0.85,
        "severity": "HIGH",
    })
    alerts, total = await get_alerts(limit=10)
    assert total == 1
    assert alerts[0]["anomaly_score"] == pytest.approx(0.85)
    assert alerts[0]["severity"] == "HIGH"


@pytest.mark.asyncio
async def test_get_alerts_filter_by_severity(tmp_db):
    await init_db()
    for sev in ["CRITICAL", "HIGH", "LOW"]:
        await insert_alert({"ts": "2023-10-27T10:00:00Z", "anomaly_score": 0.5, "severity": sev})

    critical, total_c = await get_alerts(severity_filter="CRITICAL")
    assert total_c == 1 and critical[0]["severity"] == "CRITICAL"

    high, total_h = await get_alerts(severity_filter="HIGH")
    assert total_h == 1 and high[0]["severity"] == "HIGH"


@pytest.mark.asyncio
async def test_get_alerts_since(tmp_db):
    await init_db()
    for ts in ["2023-10-27T10:00:00Z", "2023-10-27T11:00:00Z"]:
        await insert_alert({"ts": ts, "anomaly_score": 0.7, "severity": "HIGH"})

    alerts, total = await get_alerts(since_ts="2023-10-27T10:30:00Z")
    assert total == 1
    assert alerts[0]["ts"] == "2023-10-27T11:00:00Z"
