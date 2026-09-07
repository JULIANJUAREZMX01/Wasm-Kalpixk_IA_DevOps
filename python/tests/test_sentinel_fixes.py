import pytest

from python.db.database import get_alerts, init_db, insert_alert


@pytest.fixture
def tmp_db(monkeypatch, tmp_path):
    db_file = str(tmp_path / "test_security.db")
    monkeypatch.setenv("KALPIXK_DB_PATH", db_file)
    return db_file


@pytest.mark.asyncio
async def test_insert_alert_sql_injection_protection(tmp_db):
    await init_db()

    # Malicious key that attempts SQL injection
    malicious_key = "severity) VALUES ('2023-10-27T10:00:00Z', '1.2.3.4', 0.9, 'injection', 'CRITICAL', 'none', 1.0, '[]', 'agent'); --"

    malicious_dict = {
        "ts": "2023-10-27T10:00:00Z",
        "ip": "1.1.1.1",
        "anomaly_score": 0.5,
        "event_type": "normal",
        malicious_key: "CRITICAL",
    }

    # This should not raise an exception now, but the malicious key should be ignored
    await insert_alert(malicious_dict)

    # Check alerts
    alerts, total = await get_alerts(limit=10)

    # Should have exactly 1 alert (the one with IP 1.1.1.1)
    # The injection attempt should NOT have created a second alert with IP 1.2.3.4
    assert total == 1
    assert alerts[0]["ip"] == "1.1.1.1"

    ips = [a["ip"] for a in alerts]
    assert "1.2.3.4" not in ips, "SQL Injection was NOT blocked!"


@pytest.mark.asyncio
async def test_insert_alert_only_invalid_fields(tmp_db):
    await init_db()

    invalid_dict = {"invalid_field": "some_value", "another_bad_field": 123}

    # Should not crash and should not insert anything
    await insert_alert(invalid_dict)

    alerts, total = await get_alerts()
    assert total == 0


@pytest.mark.asyncio
async def test_insert_alerts_batch_sql_injection_protection(tmp_db):
    await init_db()
    from python.db.database import insert_alerts

    malicious_key = "severity) VALUES ('2023-10-27T10:00:00Z', '8.8.8.8', 0.9, 'batch_injection', 'CRITICAL', 'none', 1.0, '[]', 'agent'); --"

    batch = [
        {
            "ts": "2023-10-27T11:00:00Z",
            "ip": "2.2.2.2",
            "anomaly_score": 0.1,
            "event_type": "normal",
        },
        {
            "ts": "2023-10-27T11:00:01Z",
            "ip": "3.3.3.3",
            "anomaly_score": 0.8,
            malicious_key: "CRITICAL",
        },
    ]

    await insert_alerts(batch)

    alerts, total = await get_alerts(limit=10)

    # Should have 2 alerts
    assert total == 2

    ips = [a["ip"] for a in alerts]
    assert "2.2.2.2" in ips
    assert "3.3.3.3" in ips
    assert "8.8.8.8" not in ips, "Batch SQL Injection was NOT blocked!"


@pytest.mark.asyncio
async def test_nan_infinity_features_rejected():
    import json

    import httpx

    from python.api.kalpixk_api import app

    headers = {"X-Kalpixk-Key": "development_secret", "Content-Type": "application/json"}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Single payload with NaN encoded with allow_nan=True
        nan_single = json.dumps({"features": [0.5] * 31 + [float("nan")]}, allow_nan=True)
        resp = await client.post("/analyze", content=nan_single, headers=headers)
        assert resp.status_code == 422, (
            f"Expected 422 for NaN single feature, got {resp.status_code}"
        )

        # Single payload with Infinity
        inf_single = json.dumps({"features": [0.5] * 31 + [float("inf")]}, allow_nan=True)
        resp = await client.post("/analyze", content=inf_single, headers=headers)
        assert resp.status_code == 422, (
            f"Expected 422 for Inf single feature, got {resp.status_code}"
        )

        # Batch payload with NaN
        nan_batch = json.dumps(
            {"features": [[0.5] * 32, [0.5] * 31 + [float("nan")]]}, allow_nan=True
        )
        resp = await client.post("/api/detect", content=nan_batch, headers=headers)
        assert resp.status_code == 422, (
            f"Expected 422 for NaN batch feature, got {resp.status_code}"
        )
