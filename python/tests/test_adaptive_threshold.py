"""
Tests for AdaptiveThreshold and AdversarialDriftGuard.
"""

import threading

import numpy as np

from python.detection.adaptive_threshold import AdaptiveThreshold, AdversarialDriftGuard


def test_adaptive_threshold_initialization():
    at = AdaptiveThreshold(window_size=100, k=2.0, recalibrate_every=10)
    assert at.window_size == 100
    assert at.k == 2.0
    assert at.recalibrate_every == 10
    assert at.current_threshold == 0.5


def test_adaptive_threshold_recalibration():
    # recalibrate_every = 10, window_size = 100
    at = AdaptiveThreshold(window_size=100, k=3.0, recalibrate_every=10)

    # Feed 9 benign scores (no recalibration yet because < 10 updates)
    for _ in range(9):
        at.update(0.1)
    assert at.current_threshold == 0.5

    # 10th update triggers recalibration
    at.update(0.1)
    # mean=0.1, std=0.0, threshold = 0.1 + 3.0*0.0 = 0.1
    assert at.current_threshold == 0.1


def test_adaptive_threshold_no_move_on_anomalies():
    at = AdaptiveThreshold(window_size=100, k=3.0, recalibrate_every=10)
    initial_threshold = at.current_threshold

    # Feed anomalous scores (> 0.5)
    for _ in range(20):
        at.update(0.9)

    # Threshold should not have moved because scores were > current_threshold
    assert at.current_threshold == initial_threshold


def test_adaptive_threshold_thread_safety():
    at = AdaptiveThreshold(window_size=1000, k=3.0, recalibrate_every=50)

    def worker():
        for _ in range(100):
            at.update(np.random.uniform(0.0, 0.2))

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify that total updates is 1000
    assert at.to_dict()["total_updates"] == 1000
    # Threshold should be significantly lower than 0.5
    assert at.current_threshold < 0.4


def test_adversarial_drift_guard_robustness():
    # recalibrate_every=20, alpha=1.0 (no dampening for easier testing)
    guard = AdversarialDriftGuard(window_size=20, recalibrate_every=20, k=3.0, alpha=1.0)

    # 1. Baseline: constant normal traffic
    scores = [0.1] * 20
    guard.update(scores)

    # median=0.1, MAD=0.0 -> floor to 0.01
    # threshold = 0.1 + 3.0 * (0.01 * 1.4826) ~= 0.144478
    assert 0.14 < guard.current_threshold < 0.15

    # 2. Add some noise that would affect mean but not median
    # New buffer: [0.1]*15 + [0.14]*5 -> median is still 0.1
    noise = [0.14] * 5
    guard.update(noise, force_recalibrate=True)

    # Still 0.1 because median of [0.1]*maxlen is 0.1
    assert 0.14 < guard.current_threshold < 0.15


def test_adversarial_drift_guard_dampening():
    # alpha=0.1 (default)
    guard = AdversarialDriftGuard(recalibrate_every=20, k=3.0, alpha=0.1)

    # Initial recalibration (sets median/mad directly)
    guard.update([0.1] * 20)
    initial_threshold = guard.current_threshold
    print(f"DEBUG: Initial threshold: {initial_threshold}")

    # Second recalibration with different data
    # We MUST use scores < initial_threshold (0.144) to get them into the buffer
    # Let's use 0.14
    new_data = [0.14] * 20
    guard.update(new_data, force_recalibrate=True)

    print(f"DEBUG: New threshold: {guard.current_threshold}")

    # Threshold should have moved slightly up
    assert guard.current_threshold > initial_threshold
    assert guard.current_threshold < 0.25


def test_adversarial_drift_guard_batch_update():
    guard = AdversarialDriftGuard(recalibrate_every=10)
    guard.update([0.1, 0.1, 0.2, 0.1, 0.1])
    assert guard.to_dict()["total_updates"] == 5

    # Triggers recalibration
    guard.update([0.1] * 15)
    assert guard.to_dict()["total_updates"] == 20
    assert guard.to_dict()["initialized"] is True
