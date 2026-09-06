

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
async def test_non_finite_features_rejected_in_api():
    import httpx

    from python.api.kalpixk_api import app

    headers = {
        "X-Kalpixk-Key": "development_secret",
        "Content-Type": "application/json"
    }

    # Construct JSON string bodies containing non-standard NaN and Infinity literals
    nan_features_json = '{"features": [' + ', '.join(['0.1'] * 31) + ', NaN]}'
    inf_features_json = '{"features": [' + ', '.join(['0.1'] * 31) + ', Infinity]}'

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Test NaN in /api/detect
        res_nan_detect = await client.post("/api/detect", content=nan_features_json, headers=headers)
        assert res_nan_detect.status_code == 422
        assert "finite" in res_nan_detect.text.lower() or "nan" in res_nan_detect.text.lower()

        # Test Inf in /analyze
        res_inf_analyze = await client.post("/analyze", content=inf_features_json, headers=headers)
        assert res_inf_analyze.status_code == 422
        assert "finite" in res_inf_analyze.text.lower() or "infinity" in res_inf_analyze.text.lower()


def test_adversarial_drift_guard_filters_nan_and_inf():
    import math

    from python.detection.adaptive_threshold import AdversarialDriftGuard

    guard = AdversarialDriftGuard()

    # Update with a batch containing NaN, Inf, and valid scores
    guard.update([float("nan"), float("inf"), -float("inf"), 0.2, 0.3], force_recalibrate=True)

    updated_threshold = guard.current_threshold
    assert math.isfinite(updated_threshold), "Threshold corrupted to NaN or Inf!"
    assert updated_threshold != float("nan")
