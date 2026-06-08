
import numpy as np
import pytest
from python.detection.adaptive_threshold import AdversarialDriftGuard

def test_drift_guard_poisoning_protection():
    # alpha=0.1 means threshold moves 10% towards target
    guard = AdversarialDriftGuard(window_size=100, z_threshold=3.0, alpha=0.1, initial_threshold=0.5)

    # Seed with normal data (around 0.1)
    normal_data = [0.1] * 50
    guard.update(normal_data)

    initial_t = guard.current_threshold
    assert initial_t < 0.5 # Should have dropped significantly

    # Attempt to poison with extreme outliers (e.g. 0.9)
    # Z-score for 0.9 when mean=0.1 and std=0 (or very small) will be huge
    poison = [0.9] * 10
    guard.update(poison)

    # Threshold should NOT move because 0.9 is filtered out by Z-score
    assert guard.current_threshold == initial_t

def test_drift_guard_dampening():
    # Use a high Z-threshold to allow some variance for testing
    guard = AdversarialDriftGuard(window_size=100, z_threshold=100.0, alpha=0.1, initial_threshold=0.5)

    # Seed with some initial variance so std > 0
    guard.update([0.1, 0.11, 0.09, 0.1, 0.11, 0.09, 0.1, 0.11, 0.09, 0.12])
    t1 = guard.current_threshold

    # Update with higher but allowed data
    # We need to provide more points to move the 99th percentile
    guard.update([0.2] * 20)
    t2 = guard.current_threshold

    assert t2 != t1

def test_drift_guard_batch_update():
    guard = AdversarialDriftGuard()
    scores = [0.1, 0.12, 0.09, 0.11, 0.4] # 0.4 might be borderline
    t = guard.update(scores)
    assert t > 0
    assert guard.to_dict()["total_updates"] == 5
