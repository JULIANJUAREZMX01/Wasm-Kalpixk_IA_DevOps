

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
        malicious_key: "CRITICAL"
    }

    # This should not raise an exception now, but the malicious key should be ignored
    await insert_alert(malicious_dict)

    # Check alerts
    alerts, total = await get_alerts(limit=10)

    # Should have exactly 1 alert (the one with IP 1.1.1.1)
    # The injection attempt should NOT have created a second alert with IP 1.2.3.4
    assert total == 1
    assert alerts[0]['ip'] == "1.1.1.1"

    ips = [a['ip'] for a in alerts]
    assert '1.2.3.4' not in ips, "SQL Injection was NOT blocked!"

@pytest.mark.asyncio
async def test_insert_alert_only_invalid_fields(tmp_db):
    await init_db()

    invalid_dict = {
        "invalid_field": "some_value",
        "another_bad_field": 123
    }

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
            "event_type": "normal"
        },
        {
            "ts": "2023-10-27T11:00:01Z",
            "ip": "3.3.3.3",
            "anomaly_score": 0.8,
            malicious_key: "CRITICAL"
        }
    ]

    await insert_alerts(batch)

    alerts, total = await get_alerts(limit=10)

    # Should have 2 alerts
    assert total == 2

    ips = [a['ip'] for a in alerts]
    assert "2.2.2.2" in ips
    assert "3.3.3.3" in ips
    assert "8.8.8.8" not in ips, "Batch SQL Injection was NOT blocked!"

@pytest.mark.asyncio
async def test_get_alerts_limit_protection(tmp_db):
    """Verifies that the limit parameter in get_alerts is correctly constrained."""
    await init_db()
    # Insert 5 alerts
    for i in range(5):
        await insert_alert({
            "ts": f"2023-10-27T10:00:0{i}Z",
            "ip": f"1.1.1.{i}",
            "anomaly_score": 0.5,
            "severity": "LOW"
        })

    # Test with negative limit - should be constrained to at least 1
    alerts_neg, total_neg = await get_alerts(limit=-10)
    assert len(alerts_neg) >= 1
    # SQLite with LIMIT 1 returns 1, but total count is still 5
    assert len(alerts_neg) == 1
    assert total_neg == 5

    # Test with zero limit - should be constrained to 1
    alerts_zero, total_zero = await get_alerts(limit=0)
    assert len(alerts_zero) == 1
    assert total_zero == 5
