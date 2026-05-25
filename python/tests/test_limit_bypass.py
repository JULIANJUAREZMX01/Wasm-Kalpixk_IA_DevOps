

import pytest

from python.db.database import get_alerts, init_db, insert_alert


@pytest.fixture
async def setup_db(monkeypatch, tmp_path):
    db_file = str(tmp_path / "test_limit.db")
    monkeypatch.setenv("KALPIXK_DB_PATH", db_file)
    await init_db()

    # Insert some dummy alerts
    for i in range(10):
        await insert_alert({
            "ts": f"2023-10-27T10:00:0{i}Z",
            "ip": f"1.1.1.{i}",
            "anomaly_score": 0.1 * i,
            "event_type": "test",
            "severity": "LOW"
        })
    return db_file

@pytest.mark.asyncio
async def test_get_alerts_limit_protection(setup_db):
    # In SQLite, LIMIT -1 means "no limit".
    # After fix, it should be constrained to at least 1.

    # Attempt bypass with -1
    alerts, total = await get_alerts(limit=-1)

    # We expect it to return 1 alert instead of all 10
    assert len(alerts) == 1
    assert total == 10

@pytest.mark.asyncio
async def test_api_alerts_limit_protection(setup_db, monkeypatch):
    from fastapi.testclient import TestClient

    from python.api.kalpixk_api import app, verify_api_key

    # Mocking verify_api_key to skip auth for testing
    async def skip_verify():
        return "test_key"

    app.dependency_overrides[verify_api_key] = skip_verify

    try:
        with TestClient(app) as client:
            # Test with negative limit
            response = client.get("/api/alerts?limit=-1")
            assert response.status_code == 200
            data = response.json()
            # After fix, it returns 1 alert instead of 10
            assert len(data["alerts"]) == 1
    finally:
        app.dependency_overrides = {}
