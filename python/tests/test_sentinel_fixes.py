

import pytest

from python.db.database import get_alerts, init_db, insert_alert, insert_alerts


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

    # Malicious key in the first alert
    # We match the number of columns (4: ts, ip, anomaly_score, and whatever this key maps to)
    malicious_key = "severity) VALUES ('2023-10-27T10:00:00Z', '9.9.9.9', 0.99, 'INJECTED'); --"

    alerts = [
        {
            "ts": "2023-10-27T10:00:00Z",
            "ip": "1.1.1.1",
            "anomaly_score": 0.5,
            malicious_key: "CRITICAL"
        },
        {
            "ts": "2023-10-27T10:00:01Z",
            "ip": "2.2.2.2",
            "anomaly_score": 0.6,
            "severity": "HIGH"
        }
    ]

    # In the current vulnerable state, this might fail because executemany
    # expects all dicts to have the same keys as the first one,
    # or it might succeed if it just uses the first one's keys.
    # Actually, aiosqlite/sqlite3 executemany with named placeholders
    # requires all dicts to have all keys used in the query.
    try:
        await insert_alerts(alerts)
    except Exception as e:
        # We don't expect a crash here, even with malicious keys
        pytest.fail(f"insert_alerts crashed with: {e}")

    # Check alerts
    alerts_in_db, total = await get_alerts(limit=10)

    ips = [a['ip'] for a in alerts_in_db]
    assert '9.9.9.9' not in ips, "SQL Injection in insert_alerts was NOT blocked!"
