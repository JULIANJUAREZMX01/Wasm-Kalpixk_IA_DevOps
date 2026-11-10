

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
async def test_alert_timestamp_utc_timezone_aware(tmp_db):
    await init_db()
    from datetime import datetime

    # Insert alert without explicit 'ts' so database.py auto-generates it using datetime.now(UTC)
    alert_dict = {
        "ip": "10.0.0.1",
        "anomaly_score": 0.95,
        "event_type": "security_test",
        "severity": "CRITICAL",
    }
    await insert_alert(alert_dict)

    alerts, total = await get_alerts(limit=1)
    assert total == 1
    ts_str = alerts[0]["ts"]

    # Verify timestamp parsing and timezone presence
    parsed_dt = datetime.fromisoformat(ts_str)
    assert parsed_dt.tzinfo is not None, "Timestamp string must be timezone-aware"
    assert ts_str.endswith("+00:00") or ts_str.endswith("Z"), f"Timestamp '{ts_str}' missing UTC timezone designator"


@pytest.mark.asyncio
async def test_insert_alert_dict_features_json(tmp_db):
    await init_db()

    dict_features = {"probe_type": "bus_sniffing", "entropy": 0.99, "threshold": 0.5}
    alert_dict = {
        "ip": "10.0.0.2",
        "anomaly_score": 0.88,
        "event_type": "embedded_probe",
        "severity": "HIGH",
        "features_json": dict_features,
    }
    await insert_alert(alert_dict)

    alerts, total = await get_alerts(limit=1)
    assert total == 1
    assert alerts[0]["features_json"] == dict_features


@pytest.mark.asyncio
async def test_embedded_node_sync_tamper_alert_timestamp_utc(tmp_db):
    await init_db()
    from datetime import datetime

    from httpx import ASGITransport, AsyncClient

    from python.api.kalpixk_api import app

    transport = ASGITransport(app=app)
    headers = {"X-Kalpixk-Key": "development_secret"}
    payload = {
        "node_id": "sentinel-node-99",
        "firmware_version": "v9.0.0-XOCHIMILCO",
        "firmware_tampered": True,
        "bus_sniffing_detected": False,
        "cpu_usage_pct": 50.0,
        "ram_usage_pct": 50.0,
        "raw_logs": ["TAMPER DETECTED"],
    }

    async with AsyncClient(transport=transport, base_url="http://testserver", headers=headers) as client:
        res = await client.post("/api/v1/guerrilla/embedded_node/sync", json=payload)
        assert res.status_code == 200

    alerts, total = await get_alerts(limit=1)
    assert total >= 1
    ts_str = alerts[0]["ts"]
    parsed_dt = datetime.fromisoformat(ts_str)
    assert parsed_dt.tzinfo is not None, "Embedded node tamper alert timestamp must be timezone-aware"
    assert ts_str.endswith("+00:00") or ts_str.endswith("Z")
