"""
tests/integration/test_full_pipeline.py
────────────────────────────────────────
Full pipeline integration tests.
"""
import httpx
import numpy as np
import pytest
import torch

BASE = "http://localhost:8000"

@pytest.fixture
def brute_force_features():
    X = np.zeros((50, 32), dtype=np.float32)
    X[:, 0] = 0.2
    X[:, 1] = 0.45
    X[:, 5] = 1.0
    X[:, 6] = 0.0
    X[:, 8] = 1.0
    X[:, 9] = 0.85
    return X

@pytest.fixture
def normal_traffic_features():
    rng = np.random.default_rng(42)
    X = rng.normal(0.3, 0.05, (100, 32)).clip(0, 1).astype(np.float32)
    X[:, 5] = 0.0
    X[:, 6] = 1.0
    return X

@pytest.mark.asyncio
async def test_api_health():
    async with httpx.AsyncClient() as c:
        try:
            r = await c.get(f"{BASE}/api/health")
            assert r.status_code == 200
        except httpx.ConnectError:
            pytest.skip("API server not running")

@pytest.mark.asyncio
async def test_detect_brute_force(brute_force_features):
    payload = {
        "features": brute_force_features.tolist(),
        "event_ids": [f"ssh_{i}" for i in range(50)],
        "source_type": "syslog",
        "metadata": [{"event_type": "login_failure"}] * 50,
    }
    async with httpx.AsyncClient(timeout=30) as c:
        try:
            r = await c.post(f"{BASE}/api/detect", json=payload)
            assert r.status_code == 200
        except httpx.ConnectError:
            pytest.skip("API server not running")

class TestIsolationForest:
    def test_fit_and_predict(self):
        from detection.isolation_forest import KalpixkIsolationForest
        model = KalpixkIsolationForest(torch.device("cpu"), force_cpu=True)
        X = np.random.default_rng(0).normal(0.3, 0.1, (200, 32)).clip(0, 1).astype(np.float32)
        model.fit(X)
        scores, confs = model.predict(X[:10])
        assert len(scores) == 10

class TestAutoencoder:
    def test_fit_and_predict(self):
        from detection.autoencoder import KalpixkAutoencoder
        ae = KalpixkAutoencoder(torch.device("cpu"))
        X = np.random.default_rng(1).normal(0.3, 0.1, (300, 32)).clip(0, 1).astype(np.float32)
        ae.fit(X, epochs=1)
        scores, confs = ae.predict(X[:10])
        assert len(scores) == 10

class TestWmsConnector:
    def test_mock_stream_generates_logs(self):
        from utils.wms_connector import WmsConnector
        c = WmsConnector(mode="mock")
        batch = c.stream_batch(n=20)
        assert len(batch) == 20
