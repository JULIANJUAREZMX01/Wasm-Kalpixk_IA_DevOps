"""
Tests for AdversarialDriftGuard (v9 Guerrilla Hardening).
"""

import threading

import numpy as np

from python.detection.adaptive_threshold import AdversarialDriftGuard


def test_adversarial_drift_guard_initialization():
    at = AdversarialDriftGuard(window_size=100, k=2.0, recalibrate_every=10, alpha=0.5)
    assert at.window_size == 100
    assert at.k == 2.0
    assert at.recalibrate_every == 10
    assert at.alpha == 0.5
    assert at.current_threshold == 0.5


def test_adversarial_drift_guard_dampening():
    # recalibrate_every = 10, alpha = 0.1 (default)
    at = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10, alpha=0.1)

    # Feed 9 benign scores (no recalibration yet)
    for _ in range(9):
        at.update(0.1)
    assert at.current_threshold == 0.5

    # 10th update triggers recalibration with dampening
    at.update(0.1)
    # target_threshold = 0.1 + 3.0 * (0.0 * 1.4826) = 0.1
    # new_threshold = (1-0.1)*0.5 + 0.1*0.1 = 0.45 + 0.01 = 0.46
    assert round(at.current_threshold, 2) == 0.46


def test_adversarial_drift_guard_robust_stats():
    # Test that outliers in the buffer don't shift the threshold as much as Mean/Std
    # Median of [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.9] is 0.1
    # MAD is median of [0, 0, 0, 0, 0, 0, 0, 0, 0, 0.8] which is 0
    at = AdversarialDriftGuard(
        window_size=10, k=3.0, recalibrate_every=10, alpha=1.0
    )  # alpha=1.0 for immediate jump

    # Manually fill buffer with some outliers (though update() usually prevents this,
    # we want to test _recalibrate robustness)
    for _ in range(9):
        at.update(0.1, is_confirmed_benign=True)
    at.update(0.9, is_confirmed_benign=True)  # Triggers recalibrate

    # Robust threshold should still be 0.1
    assert at.current_threshold == 0.1


def test_adversarial_drift_guard_batch_update():
    at = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10, alpha=1.0)
    scores = [0.1] * 10
    at.update(scores)
    assert at.current_threshold == 0.1


def test_adversarial_drift_guard_no_move_on_anomalies():
    at = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10)
    initial_threshold = at.current_threshold

    # Feed anomalous scores (> 0.5)
    for _ in range(20):
        at.update(0.9)

    # Threshold should not have moved because scores were > current_threshold
    assert at.current_threshold == initial_threshold


def test_adversarial_drift_guard_thread_safety():
    at = AdversarialDriftGuard(window_size=1000, k=3.0, recalibrate_every=50)

    def worker():
        for _ in range(100):
            at.update(float(np.random.uniform(0.0, 0.2)))

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert at.to_dict()["total_updates"] == 1000
    assert at.current_threshold < 0.5


def test_adversarial_drift_guard_to_dict():
    at = AdversarialDriftGuard(window_size=500, k=3.0, recalibrate_every=50)
    at.update(0.2)

    d = at.to_dict()
    assert d["window_size"] == 500
    assert d["k"] == 3.0
    assert d["total_updates"] == 1
    assert "current_threshold" in d
    assert "alpha" in d


def test_is_anomaly():
    at = AdversarialDriftGuard(alpha=1.0)  # immediate update
    # Initial threshold is 0.5
    assert not at.is_anomaly(0.4)
    assert at.is_anomaly(0.6)

    # Recalibrate to lower threshold
    # Need 50 updates to trigger recalibrate by default
    for _ in range(50):
        at.update(0.1)

    new_threshold = at.current_threshold
    assert new_threshold < 0.2
    assert at.is_anomaly(0.3)
    assert not at.is_anomaly(0.05)
