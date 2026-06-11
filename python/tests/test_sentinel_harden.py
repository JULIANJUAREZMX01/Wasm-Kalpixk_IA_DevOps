
import numpy as np
import pytest
from python.detection.adaptive_threshold import AdversarialDriftGuard
from fastapi.testclient import TestClient
from python.api.kalpixk_api import app

def test_drift_guard_poisoning_protection():
    # alpha=0.1, z_threshold=3.5
    guard = AdversarialDriftGuard(window_size=100, z_threshold=3.5, alpha=0.1)

    # 1. Initial baseline (seed with 20 low scores)
    initial_scores = [0.1] * 20
    guard.update(initial_scores)
    initial_threshold = guard.current_threshold
    assert initial_threshold < 0.2

    # 2. Attempt "Boiling Frog" Poisoning:
    # Inject 100 "high but not too high" scores to slowly drift the threshold
    poison_scores = [0.25] * 100
    guard.update(poison_scores)

    drifted_threshold = guard.current_threshold
    assert drifted_threshold < 0.3, f"Threshold drifted too much: {drifted_threshold}"

    # 3. Attempt "Direct Poisoning" (Outliers):
    # Inject extremely high scores (0.9). These should be filtered by Z-score.
    outlier_scores = [0.9] * 50
    guard.update(outlier_scores)

    # Threshold should not move because 0.9 is way outside Z=3.5 of [0.1, 0.25]
    final_threshold = guard.current_threshold
    assert final_threshold == drifted_threshold, "Threshold moved by outliers!"

client = TestClient(app)
client.headers = {"X-Kalpixk-Key": "development_secret"}

@pytest.mark.asyncio
async def test_pagination_hardening():
    # Test with very large limit
    response = client.get("/api/alerts?limit=1000")
    assert response.status_code == 200

    # Test with negative limit
    response = client.get("/api/alerts?limit=-10")
    assert response.status_code == 200

    # Test with zero limit
    response = client.get("/api/alerts?limit=0")
    assert response.status_code == 200
