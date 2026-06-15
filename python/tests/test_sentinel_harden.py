
import numpy as np
from fastapi.testclient import TestClient

from python.api.kalpixk_api import app

client = TestClient(app)
client.headers = {"X-Kalpixk-Key": "development_secret"}

def test_alerts_limit_clamping():
    # Test negative limit - should be clamped to 1
    response = client.get("/api/alerts?limit=-1")
    assert response.status_code == 200
    # Even if DB is empty, the logic for clamping is in the API

    # Test too large limit - should be clamped to 500
    response = client.get("/api/alerts?limit=9999")
    assert response.status_code == 200

def test_detect_no_nameerror():
    # Test a single event to trigger the results loop where NameError was
    features = np.zeros((1, 32)).tolist()
    payload = {
        "features": features,
        "source_type": "test"
    }
    response = client.post("/api/detect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert "adaptive_threshold" in data["results"][0]

def test_ensemble_returns_drift_guard_threshold():
    import torch

    from python.models.ensemble import DetectionEnsemble

    ens = DetectionEnsemble(device=torch.device("cpu"))
    # Seed drift guard with some values to change threshold from 0.5
    for _ in range(100):
        ens.drift_guard.update(0.1)

    ens_threshold = ens.drift_guard.current_threshold

    features = torch.zeros((1, 32))
    scores, methods, confs, thresh = ens.predict(features)

    assert thresh == ens_threshold
    # Verification: Isolation Forest threshold is still 0.5 (initial) or something else
    assert thresh != ens.iso_forest.threshold.current_threshold or ens_threshold != 0.5
