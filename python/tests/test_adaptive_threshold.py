"""
Tests for AdversarialDriftGuard (and backward compatible AdaptiveThreshold).
"""

import threading

import numpy as np

from python.detection.adaptive_threshold import AdaptiveThreshold, AdversarialDriftGuard


def test_adaptive_threshold_initialization():
    at = AdversarialDriftGuard(window_size=100, k=2.0, recalibrate_every=10)
    assert at.window_size == 100
    assert at.k == 2.0
    assert at.recalibrate_every == 10
    assert at.current_threshold == 0.5


def test_adaptive_threshold_recalibration_with_dampening():
    # recalibrate_every = 10, window_size = 100, alpha = 0.1
    at = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10, alpha=0.1)

    # Feed 9 benign scores (no recalibration yet)
    for _ in range(9):
        at.update(0.1)
    assert at.current_threshold == 0.5

    # 10th update triggers recalibration
    at.update(0.1)

    # Target threshold: median(0.1...) + 3.0 * MAD(0.1...) = 0.1 + 0 = 0.1
    # New threshold with dampening: (1 - 0.1) * 0.5 + 0.1 * 0.1 = 0.45 + 0.01 = 0.46
    assert round(at.current_threshold, 2) == 0.46


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
    # Threshold should be lower than 0.5 after several recalibrations
    assert at.current_threshold < 0.5


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


def test_is_anomaly():
    at = AdaptiveThreshold(alpha=1.0) # alpha=1.0 means no dampening (for testing legacy-like behavior)
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
