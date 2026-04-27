"""
tests/integration/test_full_pipeline.py
────────────────────────────────────────
Full pipeline integration tests:
  raw log → WASM parse → feature matrix → GPU detect → alert → explain

Run: cd python && KALPIXK_FORCE_CPU=true uv run pytest tests/ -v
"""

import time

import httpx
import numpy as np
import pytest

BASE = "http://localhost:8000"


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def brute_force_features():
    """Feature matrix simulating 50 SSH brute-force events."""
    X = np.zeros((50, 32), dtype=np.float32)
    X[:, 0] = 0.2  # event_type: LoginFailure
    X[:, 1] = 0.45  # local_severity
    X[:, 5] = 1.0  # is_off_hours
    X[:, 6] = 0.0  # not internal
    X[:, 8] = 1.0  # has_user
    X[:, 9] = 0.85  # source_entropy (random IP)
    return X


@pytest.fixture
def normal_traffic_features():
    """Feature matrix simulating 100 normal WMS operations."""
    rng = np.random.default_rng(42)
    X = rng.normal(0.3, 0.05, (100, 32)).clip(0, 1).astype(np.float32)
    X[:, 5] = 0.0  # not off-hours
    X[:, 6] = 1.0  # internal IPs
    return X


# ── Health check ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_api_health():
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert "device" in data
    assert "ensemble_version" in data


# ── Detection ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_detect_brute_force(brute_force_features):
    payload = {
        "features": brute_force_features.tolist(),
        "event_ids": [f"ssh_{i}" for i in range(50)],
        "source_type": "syslog",
        "metadata": [{"event_type": "login_failure"}] * 50,
    }
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/api/detect", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "results" in data
    assert "total_anomalies" in data
    assert "inference_time_ms" in data
    assert len(data["results"]) == 50
    assert data["total_anomalies"] > 0, "Brute force events should be detected"


@pytest.mark.asyncio
async def test_detect_normal_traffic_low_anomalies(normal_traffic_features):
    payload = {
        "features": normal_traffic_features.tolist(),
        "event_ids": [f"normal_{i}" for i in range(100)],
        "source_type": "json",
        "metadata": [{"event_type": "db_query"}] * 100,
    }
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/api/detect", json=payload)
    assert r.status_code == 200
    data = r.json()
    anomaly_rate = data["total_anomalies"] / 100
    assert anomaly_rate < 0.30, f"Normal traffic FP rate too high: {anomaly_rate:.1%}"


@pytest.mark.asyncio
async def test_detection_latency_under_50ms():
    """Hackathon metric: detection latency < 50ms for 100 events."""
    rng = np.random.default_rng(0)
    features = rng.uniform(0, 1, (100, 32)).tolist()
    payload = {
        "features": features,
        "event_ids": [f"e{i}" for i in range(100)],
        "source_type": "json",
        "metadata": [{}] * 100,
    }
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(f"{BASE}/api/detect", json=payload)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert r.status_code == 200
    assert elapsed_ms < 50, f"Latency {elapsed_ms:.1f}ms exceeds 50ms hackathon target"


@pytest.mark.asyncio
async def test_all_scores_in_unit_interval():
    rng = np.random.default_rng(1)
    features = rng.uniform(0, 1, (200, 32)).tolist()
    payload = {
        "features": features,
        "event_ids": [f"e{i}" for i in range(200)],
        "source_type": "syslog",
        "metadata": [{}] * 200,
    }
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/api/detect", json=payload)
    for result in r.json()["results"]:
        s = result["anomaly_score"]
        assert 0.0 <= s <= 1.0, f"Score {s} out of [0,1]"


# ── Input validation ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_empty_batch_handled():
    payload = {"features": [], "event_ids": [], "source_type": "syslog", "metadata": []}
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(f"{BASE}/api/detect", json=payload)
    assert r.status_code in (200, 422)


@pytest.mark.asyncio
async def test_wrong_feature_dimension_rejected():
    """Feature vectors with wrong dimension must be rejected."""
    payload = {
        "features": [[0.1] * 10],  # 10 dims instead of 32
        "event_ids": ["e0"],
        "source_type": "syslog",
        "metadata": [{}],
    }
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(f"{BASE}/api/detect", json=payload)
    assert r.status_code in (400, 422), "Wrong feature dimension should be rejected"


@pytest.mark.asyncio
async def test_mismatched_counts_rejected():
    """features and event_ids must have the same length."""
    payload = {
        "features": [[0.1] * 32, [0.2] * 32],
        "event_ids": ["only_one"],  # Mismatch
        "source_type": "syslog",
        "metadata": [{}],
    }
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(f"{BASE}/api/detect", json=payload)
    assert r.status_code in (400, 422)


# ── Metrics endpoint ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_metrics_endpoint():
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/api/metrics")
    assert r.status_code == 200
    m = r.json()
    for key in ["total_events_processed", "mean_latency_ms", "device"]:
        assert key in m, f"Missing metric: {key}"


# ── Unit tests for detection models (no server needed) ────────────────────────


class TestIsolationForest:
    def test_fit_and_predict(self):
        import torch

        from detection.isolation_forest import KalpixkIsolationForest

        model = KalpixkIsolationForest(torch.device("cpu"), force_cpu=True)
        X = np.random.default_rng(0).normal(0.3, 0.1, (200, 32)).clip(0, 1).astype(np.float32)
        model.fit(X)
        scores, confs = model.predict(X[:10])
        assert len(scores) == 10
        assert all(0.0 <= s <= 1.0 for s in scores)
        assert all(0.0 <= c <= 1.0 for c in confs)

    def test_synthetic_fit(self):
        import torch

        from detection.isolation_forest import KalpixkIsolationForest

        model = KalpixkIsolationForest(torch.device("cpu"), force_cpu=True)
        model.fit_synthetic(n_samples=500)
        assert model.is_trained

    def test_anomaly_scores_higher_for_outliers(self):
        import torch

        from detection.isolation_forest import KalpixkIsolationForest

        model = KalpixkIsolationForest(torch.device("cpu"), force_cpu=True)
        X_normal = (
            np.random.default_rng(0).normal(0.3, 0.05, (500, 32)).clip(0, 1).astype(np.float32)
        )
        model.fit(X_normal)

        # Extreme outliers
        X_outlier = np.ones((10, 32), dtype=np.float32)
        X_outlier[:, 1] = 0.99  # max severity
        X_outlier[:, 5] = 1.0  # off hours
        X_outlier[:, 16] = 1.0  # destructive op

        normal_scores, _ = model.predict(X_normal[:20])
        outlier_scores, _ = model.predict(X_outlier)

        assert np.mean(outlier_scores) > np.mean(normal_scores), (
            "Outlier scores should be higher than normal scores on average"
        )


class TestAutoencoder:
    def test_fit_and_predict(self):
        import torch

        from detection.autoencoder import KalpixkAutoencoder

        ae = KalpixkAutoencoder(torch.device("cpu"))
        X = np.random.default_rng(1).normal(0.3, 0.1, (300, 32)).clip(0, 1).astype(np.float32)
        ae.fit(X, epochs=5)  # Quick for tests
        scores, confs = ae.predict(X[:10])
        assert len(scores) == 10
        assert all(0.0 <= s <= 1.0 for s in scores)

    def test_latent_representation_shape(self):
        import torch

        from detection.autoencoder import KalpixkAutoencoder

        ae = KalpixkAutoencoder(torch.device("cpu"))
        ae.fit_synthetic(n_samples=200)
        X = np.random.rand(5, 32).astype(np.float32)
        latent = ae.get_latent(X)
        assert latent.shape == (5, 4), f"Bottleneck should be 4-dim, got {latent.shape}"


class TestWmsConnector:
    def test_mock_stream_generates_logs(self):
        from utils.wms_connector import WmsConnector

        c = WmsConnector(mode="mock")
        batch = c.stream_batch(n=20)
        assert len(batch) == 20
        for line in batch:
            assert "TIMESTAMP=" in line
            assert "AUTHID=" in line
            assert "SQL=" in line

    def test_mock_contains_anomalies(self):
        """With enough logs, at least 1 anomaly should appear."""
        from utils.wms_connector import WmsConnector

        c = WmsConnector(mode="mock")
        batch = c.stream_batch(n=500)
        suspicious = [
            line
            for line in batch
            if any(kw in line.upper() for kw in ["DROP", "EXPORT", "GRANT", "UNKNOWN"])
        ]
        assert len(suspicious) > 0, "Mock stream should inject anomalies"

    def test_log_format_parseable(self):
        """Generated logs must match the DB2 parser format."""
        from utils.wms_connector import WmsConnector

        c = WmsConnector(mode="mock")
        for line in c.stream_batch(n=10):
            assert "TIMESTAMP=" in line
            assert "HOSTNAME=" in line
            assert "SQL=" in line
            assert len(line) < 2048  # Reasonable length
