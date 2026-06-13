"""
Tests for AdversarialDriftGuard.
"""

import numpy as np
import pytest
from python.detection.adaptive_threshold import AdversarialDriftGuard


def test_drift_guard_poisoning_protection():
    """Verify that the drift guard rejects high-Z-score poisoning attempts."""
    # Seed with many normal scores
    guard = AdversarialDriftGuard(window_size=100, k=3.5, recalibrate_every=10)

    # 50 normal scores around 0.1
    normal_scores = np.random.normal(0.1, 0.01, 50).tolist()
    guard.update(normal_scores, is_confirmed_benign=True)

    initial_threshold = guard.current_threshold
    # With alpha=0.1, it should move from 0.5 toward ~0.135
    # (0.9 * 0.5) + (0.1 * 0.135) = 0.4635
    assert initial_threshold == pytest.approx(0.4635, abs=0.01)

    # Attempt poisoning: Feed many high scores that should be rejected by Z-score
    poison_scores = [0.8] * 50
    guard.update(poison_scores)

    # Threshold should NOT have moved much (if at all) because 0.8 is many std devs away from 0.1
    # Z-score = (0.8 - 0.1) / 0.01 = 70.0 >> 3.5
    assert guard.current_threshold == initial_threshold


def test_drift_guard_dampened_updates():
    """Verify that updates move toward the target via alpha smoothing (0.1)."""
    guard = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10, alpha=0.1)

    # 50 normal scores at 0.1
    guard.update([0.1] * 50, is_confirmed_benign=True)
    initial_threshold = guard.current_threshold
    # Recalibrate is triggered. Since all are 0.1, mean=0.1, std=0.0, target=0.1
    # current = 0.5 (initial) -> (0.9 * 0.5) + (0.1 * 0.1) = 0.45 + 0.01 = 0.46
    assert guard.current_threshold == pytest.approx(0.46)

    # Feed more 0.1 scores
    guard.update([0.1] * 10, is_confirmed_benign=True)
    # Target is still 0.1. current = 0.46 -> (0.9 * 0.46) + (0.1 * 0.1) = 0.414 + 0.01 = 0.424
    assert guard.current_threshold == pytest.approx(0.424)


def test_drift_guard_batch_processing():
    """Verify O(N+M) batch update logic."""
    guard = AdversarialDriftGuard(window_size=1000, recalibrate_every=50)
    scores = np.random.uniform(0, 0.2, 100).tolist()
    threshold = guard.update(scores)

    assert len(guard._buffer) == 100
    assert guard._total_updates == 100
    assert threshold < 0.5 # Should have dropped due to recalibration
