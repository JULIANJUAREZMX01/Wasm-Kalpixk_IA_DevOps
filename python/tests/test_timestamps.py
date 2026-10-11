from datetime import datetime

from fastapi.testclient import TestClient

from python.api.kalpixk_api import app

client = TestClient(app, headers={"X-Kalpixk-Key": "development_secret"})

def test_api_timestamps_utc():
    # Test /api/detect with anomaly feature vector to trigger alert generation
    anomaly_features = [0.95] * 32
    payload = {
        "features": [anomaly_features],
        "source": "unit_test",
        "source_type": "security_test"
    }

    response = client.post("/api/detect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data

    # Verify alerts generated in DB
    alerts_resp = client.get("/api/alerts")
    assert alerts_resp.status_code == 200
    alerts_data = alerts_resp.json()
    assert "alerts" in alerts_data
    assert len(alerts_data["alerts"]) > 0

    latest_alert = alerts_data["alerts"][0]
    ts_str = latest_alert["ts"]

    # Verify ISO format and timezone offset/UTC representation (+00:00 or Z)
    parsed_dt = datetime.fromisoformat(ts_str)
    assert parsed_dt.tzinfo is not None
    assert parsed_dt.utcoffset().total_seconds() == 0
