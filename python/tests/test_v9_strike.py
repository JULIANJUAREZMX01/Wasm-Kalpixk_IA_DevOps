from fastapi.testclient import TestClient
from api.kalpixk_api import app
import os

client = TestClient(app)

def test_v9_strike_endpoint():
    # Set the key in environment so verify_api_key works
    os.environ["KALPIXK_API_KEY"] = "test_secret_v9"
    headers = {"X-Kalpixk-Key": "test_secret_v9"}

    response = client.post("/api/v1/guerrilla/v9/strike", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "GUILLOTINE_EXECUTED_V9"
    assert data["impact"] == "CRITICAL_DESTRUCTIVE"
    assert "bandwidth_saturation" in data
    assert "collapse_results" in data
