

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
async def test_insert_alerts_hardening(tmp_db):
    await init_db()

    # Test 1: Whitelist filtering in batch
    malicious_key = "severity) --"
    alerts_list = [
        {"ts": "2023-10-27T10:00:00Z", "ip": "1.1.1.1", "anomaly_score": 0.5, "event_type": "normal"},
        {"ts": "2023-10-27T10:01:00Z", "ip": "2.2.2.2", "anomaly_score": 0.9, malicious_key: "CRITICAL"}
    ]

    await insert_alerts(alerts_list)
    alerts, total = await get_alerts()
    assert total == 2
    ips = [a['ip'] for a in alerts]
    assert "1.1.1.1" in ips
    assert "2.2.2.2" in ips

    # Test 2: Key consistency padding
    # alert1 has 'source', alert2 does not. alert2 has 'technique', alert1 does not.
    alerts_diff_keys = [
        {"ts": "2023-10-27T11:00:00Z", "ip": "3.3.3.3", "anomaly_score": 0.1, "source": "src1"},
        {"ts": "2023-10-27T11:01:00Z", "ip": "4.4.4.4", "anomaly_score": 0.2, "technique": "tech1"}
    ]

    # This would fail with standard executemany if not padded
    await insert_alerts(alerts_diff_keys)
    alerts, total = await get_alerts()
    assert total == 4

    # Verify padding
    alert3 = next(a for a in alerts if a['ip'] == "3.3.3.3")
    assert alert3['source'] == "src1"
    assert alert3['technique'] is None

    alert4 = next(a for a in alerts if a['ip'] == "4.4.4.4")
    assert alert4['source'] is None
    assert alert4['technique'] == "tech1"
