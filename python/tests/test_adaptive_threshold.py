"""
Tests for AdaptiveThreshold.
"""

import threading

import numpy as np

from python.detection.adaptive_threshold import AdaptiveThreshold, AdversarialDriftGuard


def test_adversarial_drift_guard_initialization():
    guard = AdversarialDriftGuard(window_size=200, k=5.0, alpha=0.2, recalibrate_every=20)
    assert guard.window_size == 200
    assert guard.k == 5.0
    assert guard.alpha == 0.2
    assert guard.current_threshold == 0.5


def test_adversarial_drift_guard_recalibration_and_poisoning_resilience():
    guard = AdversarialDriftGuard(window_size=100, k=3.0, alpha=0.5, recalibrate_every=10)

    # Feed benign low scores
    benign_scores = [0.1] * 15
    thresh = guard.update(benign_scores)

    # Median=0.1, MAD=0.0 -> mad_scaled=0.01. Target = 0.1 + 3.0*0.01 = 0.13
    # Initial = 0.5. After EMA (alpha=0.5): 0.5*0.5 + 0.5*0.13 = 0.315
    assert thresh < 0.35

    # Attempt baseline poisoning with high anomaly scores (> current threshold)
    poison_scores = [0.9] * 50
    thresh_after_poison = guard.update(poison_scores)
    # Threshold should not be pushed up by unconfirmed high scores
    assert thresh_after_poison == thresh


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