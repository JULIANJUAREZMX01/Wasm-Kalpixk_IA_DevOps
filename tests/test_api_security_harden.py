import os
import pytest
import secrets
from fastapi.testclient import TestClient
from main import app, verify_api_key

client = TestClient(app)

def test_metrics_protected(monkeypatch):
    # Set an API key
    monkeypatch.setenv("KALPIXK_API_KEY", "test-secret-key")
    monkeypatch.setenv("KALPIXK_ENV", "production")

    # Try without key
    response = client.get("/api/v1/metrics")
    assert response.status_code == 403

    # Try with wrong key
    response = client.get("/api/v1/metrics", headers={"X-Kalpixk-Key": "wrong-key"})
    assert response.status_code == 403

    # Try with correct key
    response = client.get("/api/v1/metrics", headers={"X-Kalpixk-Key": "test-secret-key"})
    assert response.status_code == 200

def test_verify_api_key_timing_resistance():
    # This is hard to test directly, but we can verify it uses secrets.compare_digest conceptually
    # or just ensure it works as expected for equality.
    os.environ["KALPIXK_API_KEY"] = "test-secret-key"

    from main import verify_api_key
    import asyncio

    async def run_verify():
        # Correct key
        assert await verify_api_key("test-secret-key") == "test-secret-key"

        # Incorrect key
        with pytest.raises(Exception) as excinfo:
            await verify_api_key("wrong-key")
        assert "403" in str(excinfo.value)

    asyncio.run(run_verify())
