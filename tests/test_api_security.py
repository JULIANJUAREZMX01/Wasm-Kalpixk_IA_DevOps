import pytest
import os
import sys
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.main import app, detector, monitor

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def train():
    if not detector.is_trained:
        detector.train(monitor.generate_normal_baseline(100), epochs=1)

def test_api_security():
    os.environ["KALPIXK_API_KEY"] = "secure-key"
    # 1. Unauthorized
    assert client.get("/metrics").status_code == 403
    # 2. Authorized
    assert client.get("/metrics", headers={"X-Kalpixk-Key": "secure-key"}).status_code == 200
    # 3. Validation
    auth = {"X-Kalpixk-Key": "secure-key"}
    assert client.post("/detect", json={"features": [0.0]*32}, headers=auth).status_code == 200
    assert client.post("/detect", json={"features": [0.0]*31}, headers=auth).status_code == 422
