"""
Tests for AdversarialDriftGuard (AdaptiveThreshold) v9.
"""

import threading

import numpy as np

from python.detection.adaptive_threshold import AdversarialDriftGuard


def test_adaptive_threshold_initialization():
    at = AdversarialDriftGuard(window_size=100, k=2.0, recalibrate_every=10, alpha=0.5)
    assert at.window_size == 100
    assert at.k == 2.0
    assert at.recalibrate_every == 10
    assert at.alpha == 0.5
    assert at.current_threshold == 0.5


def test_adaptive_threshold_recalibration():
    # recalibrate_every = 10, window_size = 100, alpha = 1.0 (immediate update for test)
    at = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10, alpha=1.0)

    # Feed 9 benign scores
    for _ in range(9):
        at.update(0.1)
    assert at.current_threshold == 0.5

    # 10th update triggers recalibration
    at.update(0.1)
    # median=0.1, MAD=0.0, target_threshold = 0.1 + 3.0*0.001*1.4826 = 0.1044 (approx)
    assert at.current_threshold < 0.2


def test_adaptive_threshold_dampening():
    # alpha = 0.1
    at = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10, alpha=0.1)

    # Target threshold will be approx 0.1
    for _ in range(10):
        at.update(0.1)

    # threshold = 0.9 * 0.5 + 0.1 * 0.1044 = 0.45 + 0.01044 = 0.46044
    assert 0.46 < at.current_threshold < 0.47


def test_adaptive_threshold_no_move_on_anomalies():
    at = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10)
    initial_threshold = at.current_threshold

    # Feed anomalous scores (> 0.5)
    for _ in range(20):
        at.update(0.9)

    # Threshold should not have moved because scores were > current_threshold
    assert at.current_threshold == initial_threshold


def test_adaptive_threshold_thread_safety():
    at = AdversarialDriftGuard(window_size=1000, k=3.0, recalibrate_every=50)

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
    # Threshold should have moved from 0.5
    assert at.current_threshold != 0.5


def test_adaptive_threshold_to_dict():
    at = AdversarialDriftGuard(window_size=500, k=3.0, recalibrate_every=50)
    for _ in range(10):
        at.update(0.2)

    d = at.to_dict()
    assert d["window_size"] == 500
    assert d["k"] == 3.0
    assert d["buffer_len"] == 10
    assert d["total_updates"] == 10
    assert "current_threshold" in d
    assert "median" in d
    assert "mad" in d


def test_is_anomaly():
    at = AdversarialDriftGuard(alpha=1.0) # Full update for test
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
