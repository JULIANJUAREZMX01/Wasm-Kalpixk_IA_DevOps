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


def test_adaptive_threshold_to_dict():
    at = AdaptiveThreshold(window_size=500, k=3.0, recalibrate_every=50)
    for _ in range(10):
        at.update(0.2)

    d = at.to_dict()
    assert d["window_size"] == 500
    assert d["k"] == 3.0
    assert d["buffer_len"] == 10
    assert d["total_updates"] == 10
    assert "current_threshold" in d


def test_is_anomaly():
    at = AdaptiveThreshold()
    # Initial threshold is 0.5
    assert not at.is_anomaly(0.4)
    assert at.is_anomaly(0.6)

    # Recalibrate to lower threshold
    for _ in range(50):
        at.update(0.1)

    new_threshold = at.current_threshold
    assert new_threshold < 0.2
    assert at.is_anomaly(0.3)
    assert not at.is_anomaly(0.05)


# ── AdversarialDriftGuard Tests ──────────────────────────────────────────────


def test_adversarial_drift_guard_initialization():
    guard = AdversarialDriftGuard(window_size=200, k=4.0, recalibrate_every=20)
    assert guard.window_size == 200
    assert guard.k == 4.0
    assert guard.recalibrate_every == 20
    assert guard.current_threshold == 0.5


def test_adversarial_drift_guard_batch_update_and_recalibration():
    guard = AdversarialDriftGuard(window_size=100, k=6.0, recalibrate_every=10)
    scores = [0.1, 0.12, 0.11, 0.09, 0.13, 0.08, 0.1, 0.11, 0.1, 0.12]
    thresh = guard.update(scores, is_confirmed_benign=True, force_recalibrate=True)

    assert isinstance(thresh, float)
    assert guard.current_threshold < 0.4
    d = guard.to_dict()
    assert d["buffer_len"] == 10
    assert d["total_updates"] == 10
    assert "median" in d
    assert "mad" in d


def test_adversarial_drift_guard_robustness_against_outliers():
    guard = AdversarialDriftGuard(window_size=100, k=6.0, recalibrate_every=10)
    # Feed normal scores
    normal_scores = [0.15] * 20
    guard.update(normal_scores, is_confirmed_benign=True, force_recalibrate=True)
    normal_thresh = guard.current_threshold

    # Inject extreme outliers ("boiling frog" attack attempt)
    outlier_scores = [0.95] * 10
    guard.update(outlier_scores)

    # Median & MAD based guard should remain stable and not shift wildly
    assert abs(guard.current_threshold - normal_thresh) < 0.15


def test_adversarial_drift_guard_thread_safety():
    guard = AdversarialDriftGuard(window_size=1000, k=6.0, recalibrate_every=50)

    def worker():
        for _ in range(50):
            guard.update([np.random.uniform(0.1, 0.2) for _ in range(2)])

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert guard.to_dict()["total_updates"] == 1000
    assert guard.current_threshold < 0.4
