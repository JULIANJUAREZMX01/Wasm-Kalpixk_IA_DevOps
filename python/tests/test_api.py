import sys
from pathlib import Path

from fastapi.testclient import TestClient

# Add python dir to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.kalpixk_api import app

client = TestClient(app)
client.headers = {"X-Kalpixk-Key": "development_secret"}

def test_status_endpoint():
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "device" in data

def test_features_endpoint():
    response = client.get("/features")
    assert response.status_code == 200
    data = response.json()
    assert data["feature_dim"] == 32
    assert len(data["features"]) == 32


def test_detect_nan_features_rejected():
    raw_json = '{"features": [' + ','.join(['NaN'] * 32) + ']}'
    response = client.post(
        "/api/detect",
        content=raw_json,
        headers={"Content-Type": "application/json", "X-Kalpixk-Key": "development_secret"},
    )
    assert response.status_code == 422
