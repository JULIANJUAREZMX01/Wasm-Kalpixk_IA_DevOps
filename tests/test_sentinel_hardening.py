
from fastapi.testclient import TestClient
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.api.main import app

client = TestClient(app)

def test_honeypot_rate_limiting():
    # We test the rate limit on /api/v1/retaliate/exfiltrate
    # Limit is 1/minute

    # First request
    response = client.get("/api/v1/retaliate/exfiltrate")
    assert response.status_code == 200

    # Second request should be rate limited
    response = client.get("/api/v1/retaliate/exfiltrate")
    assert response.status_code == 429

def test_report_rate_limiting():
    os.environ["KALPIXK_API_KEY"] = "testkey"
    headers = {"X-Kalpixk-Key": "testkey"}

    # Limit is 5/minute
    for i in range(5):
        client.get("/api/v1/report", headers=headers)

    response = client.get("/api/v1/report", headers=headers)
    assert response.status_code == 429
