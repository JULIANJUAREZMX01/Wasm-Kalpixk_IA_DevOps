

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
async def test_ensemble_drift_guard_integration():
    import torch
    from python.models.ensemble import DetectionEnsemble
    from python.detection.adaptive_threshold import AdversarialDriftGuard

    device = torch.device("cpu")
    ensemble = DetectionEnsemble(device=device)

    # Verify drift guard is initialized
    assert isinstance(ensemble.drift_guard, AdversarialDriftGuard)

    # Test predict returns threshold from drift guard
    features = torch.zeros((1, 32))
    scores, methods, confs, thresh = ensemble.predict(features)
    assert thresh == ensemble.drift_guard.current_threshold

@pytest.mark.asyncio
async def test_api_status_reports_drift_guard():
    import httpx
    from python.api.kalpixk_api import app
    async with httpx.AsyncClient(headers={"X-Kalpixk-Key": "development_secret"},
                                transport=httpx.ASGITransport(app=app),
                                base_url="http://testserver") as c:
        r = await c.get("/status")

    assert r.status_code == 200
    data = r.json()
    assert "adaptive_threshold" in data
    # AdversarialDriftGuard to_dict includes alpha, whereas AdaptiveThreshold included k
    assert "alpha" in data["adaptive_threshold"]
    assert "k" not in data["adaptive_threshold"]

@pytest.mark.asyncio
async def test_analyze_detect_no_name_error():
    import httpx
    from python.api.kalpixk_api import app
    # This specifically tests the fix for 'threshold' vs 'adaptive_threshold' NameError
    payload = {
        "features": [[0.3] * 32],
        "event_ids": ["test_1"],
        "source_type": "test",
        "metadata": [{"key": "val"}]
    }
    async with httpx.AsyncClient(headers={"X-Kalpixk-Key": "development_secret"},
                                transport=httpx.ASGITransport(app=app),
                                base_url="http://testserver") as c:
        r = await c.post("/api/detect", json=payload)

    assert r.status_code == 200
    data = r.json()
    assert "results" in data
    assert data["results"][0]["adaptive_threshold"] is not None

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
