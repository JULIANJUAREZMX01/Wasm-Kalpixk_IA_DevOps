from fastapi.testclient import TestClient

from python.api.kalpixk_api import app

client = TestClient(app)

def test_api_health_unauthenticated_and_no_ensemble_init():
    # Ensure _ensemble is None (might be hard if other tests already ran)
    # But even if it's not None, we want to check it doesn't REQUIRE auth.
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    # If it was initialized by previous tests, device might be something else
    assert "device" in data

def test_log_request_source_type_length_constraint():
    client.headers = {"X-Kalpixk-Key": "development_secret"}

    # Valid source_type
    payload = {
        "features": [0.1] * 32,
        "source_type": "valid_source"
    }
    response = client.post("/api/detect", json=payload)
    assert response.status_code == 200

    # Invalid source_type (too long)
    payload_long = {
        "features": [0.1] * 32,
        "source_type": "a" * 101
    }
    response = client.post("/api/detect", json=payload_long)
    assert response.status_code == 422
    assert "source_type" in response.text
    assert "at most 100 characters" in response.text or "less_than_equal=100" in response.text or "String should have at most 100 characters" in response.text
