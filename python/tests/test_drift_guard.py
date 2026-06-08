
import pytest
import numpy as np
from python.detection.adaptive_threshold import AdversarialDriftGuard

def test_drift_guard_z_score_filtering():
    # alpha=1.0 to see immediate effect of target threshold
    guard = AdversarialDriftGuard(z_threshold=2.0, alpha=1.0)

    # Initialize with 20 scores of 0.1
    # Mean=0.1, Std=0.0
    guard.update([0.1] * 20)
    initial_threshold = guard.current_threshold

    # Try to poison with a score of 1.0
    # Mean=0.1, Std=0.0, score=1.0 -> Z is huge
    guard.update([1.0])

    # Threshold should not change because 1.0 was filtered out
    assert guard.current_threshold == initial_threshold

def test_drift_guard_alpha_dampening():
    # alpha=0.1
    guard = AdversarialDriftGuard(alpha=0.1)

    # Initialize buffer
    guard.update([0.1] * 20)

    # Initial threshold was 0.5.
    # Buffer has 20 scores of 0.1. Mean=0.1, Std=0.0 -> target_threshold = 0.1
    # new_threshold = 0.9 * 0.5 + 0.1 * 0.1 = 0.45 + 0.01 = 0.46
    assert abs(guard.current_threshold - 0.46) < 1e-6

def test_drift_guard_no_deadlock():
    # The memory mentioned a deadlock if re-acquiring lock in _recalibrate.
    # Our implementation doesn't have _recalibrate and only acquires lock once.
    guard = AdversarialDriftGuard()
    guard.update([0.1] * 100)
    assert guard.current_threshold < 0.5
