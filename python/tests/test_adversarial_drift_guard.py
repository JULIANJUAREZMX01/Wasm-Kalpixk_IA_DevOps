"""
Tests for AdversarialDriftGuard.
"""

import pytest

from python.detection.adaptive_threshold import AdversarialDriftGuard


def test_adversarial_drift_guard_initialization():
    guard = AdversarialDriftGuard(window_size=100, z_threshold=3.5, recalibrate_every=10, alpha=0.1)
    assert guard.window_size == 100
    assert guard.z_threshold == 3.5
    assert guard.recalibrate_every == 10
    assert guard.alpha == 0.1
    assert guard.current_threshold == 0.5

def test_adversarial_drift_guard_recalibration_dampening():
    # Recalibrate every 10 updates, alpha = 0.5 (fast for testing)
    guard = AdversarialDriftGuard(window_size=100, recalibrate_every=10, alpha=0.5)
    initial_threshold = guard.current_threshold

    # Feed 10 low scores. Target threshold should be around 0.1 (if k=3.5)
    # new_threshold = (1-0.5)*0.5 + 0.5*target
    for _ in range(10):
        guard.update(0.1)

    # The new threshold should have moved towards 0.1 but not reached it immediately
    assert guard.current_threshold < initial_threshold
    assert guard.current_threshold > 0.1

def test_adversarial_drift_guard_z_score_protection():
    # recalibrate_every = 10
    guard = AdversarialDriftGuard(window_size=100, recalibrate_every=10, alpha=1.0) # alpha=1.0 for immediate update

    # Fill buffer with normal scores
    for _ in range(9):
        guard.update(0.1)

    # Add one high but not "extreme" score (0.4 < 0.5 * 1.5 = 0.75)
    # This score is an outlier compared to 0.1 but within the update limit.
    # Mu will be (9*0.1 + 0.4)/10 = 0.13. Sigma will be ~0.09.
    # Z-score of 0.4: (0.4 - 0.13) / 0.09 = 3.0.
    # If z_threshold is 2.0, this should be filtered out.
    guard.z_threshold = 2.0
    guard.update(0.4)

    # Threshold should be based on the "clean" data (only 0.1s)
    # target = 0.1 + 3.5 * 0 = 0.1
    # Since alpha=1.0, current_threshold should be 0.1
    assert pytest.approx(guard.current_threshold, 0.01) == 0.1

def test_adversarial_drift_guard_batch_update():
    guard = AdversarialDriftGuard(recalibrate_every=10, alpha=1.0)
    scores = [0.1] * 10
    guard.update(scores)

    assert guard.to_dict()["total_updates"] == 10
    assert guard.current_threshold < 0.5

def test_adversarial_drift_guard_poisoning_protection():
    guard = AdversarialDriftGuard(recalibrate_every=10, alpha=0.1)
    initial_threshold = guard.current_threshold

    # Attempt "boiling frog" attack with extreme scores
    # Scores > current_threshold * 1.5 should be ignored
    for _ in range(20):
        guard.update(0.9) # 0.9 > 0.5 * 1.5 = 0.75

    # Total updates should be 0 in the buffer logic
    assert guard.to_dict()["total_updates"] == 0
    assert guard.current_threshold == initial_threshold
