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


# ── AdversarialDriftGuard Tests ───────────────────────────────────────────────


def test_drift_guard_initialization():
    dg = AdversarialDriftGuard(window_size=100, k=6.0, recalibrate_every=10, alpha=0.1)
    assert dg.window_size == 100
    assert dg.k == 6.0
    assert dg.recalibrate_every == 10
    assert dg.alpha == 0.1
    assert dg.current_threshold == 0.5


def test_drift_guard_update_single_and_batch():
    dg = AdversarialDriftGuard(window_size=100, k=6.0, recalibrate_every=10, alpha=0.1)

    # Test single float update
    thresh = dg.update(0.2)
    assert thresh == 0.5

    # Test batch list update (9 scores) -> total 10 updates
    batch = [0.15] * 9
    thresh = dg.update(batch)
    # 10 updates triggers recalibration
    assert thresh < 0.5
    assert dg.current_threshold == thresh


def test_drift_guard_force_recalibrate():
    dg = AdversarialDriftGuard(window_size=100, k=6.0, recalibrate_every=100)

    # Add 15 scores
    scores = list(np.random.normal(0.2, 0.01, 15))
    dg.update(scores, is_confirmed_benign=True, force_recalibrate=True)

    d = dg.to_dict()
    assert d["buffer_len"] == 15
    assert d["total_updates"] == 15
    assert d["median"] > 0
    assert d["mad"] >= 0.01


def test_drift_guard_is_anomaly():
    dg = AdversarialDriftGuard()
    assert not dg.is_anomaly(0.3)
    assert dg.is_anomaly(0.8)


def test_drift_guard_to_dict():
    dg = AdversarialDriftGuard(window_size=500, k=6.0, recalibrate_every=50, alpha=0.1)
    scores = list(np.linspace(0.1, 0.3, 20))
    dg.update(scores, force_recalibrate=True)

    d = dg.to_dict()
    assert d["window_size"] == 500
    assert d["k"] == 6.0
    assert d["alpha"] == 0.1
    assert d["buffer_len"] == 20
    assert "median" in d
    assert "mad" in d
    assert "current_threshold" in d


def test_drift_guard_thread_safety():
    dg = AdversarialDriftGuard(window_size=1000, k=6.0, recalibrate_every=50)

    def worker():
        for _ in range(50):
            dg.update([0.1, 0.15])

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert dg.to_dict()["total_updates"] == 1000
