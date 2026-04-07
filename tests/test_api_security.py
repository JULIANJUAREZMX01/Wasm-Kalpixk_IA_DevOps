import pytest
import os
from fastapi.testclient import TestClient
from src.api.main import app, detector, monitor

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def train():
    if not detector.is_trained:
        detector.train(monitor.generate_normal_baseline(100), epochs=1)

def test_api_security():
    os.environ["KALPIXK_API_KEY"] = "secure-key"
    assert client.get("/metrics").status_code == 403
    assert client.get("/metrics", headers={"X-Kalpixk-Key": "secure-key"}).status_code == 200
    headers = {"X-Kalpixk-Key": "secure-key"}
    assert client.post("/detect", json={"features": [0.0]*32}, headers=headers).status_code == 200
    assert client.post("/detect", json={"features": [0.0]*31}, headers=headers).status_code == 422
