"""
Tests for AdversarialDriftGuard (v9).
"""

import threading

import numpy as np
import pytest

from python.detection.adaptive_threshold import AdversarialDriftGuard


def test_drift_guard_initialization():
    dg = AdversarialDriftGuard(window_size=100, k=2.0, recalibrate_every=10, alpha=0.2)
    assert dg.window_size == 100
    assert dg.k == 2.0
    assert dg.recalibrate_every == 10
    assert dg.alpha == 0.2
    assert dg.current_threshold == 0.5


def test_drift_guard_recalibration_robust():
    # recalibrate_every = 10, window_size = 100
    dg = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10, alpha=1.0) # alpha=1.0 for immediate jump in test

    # Feed 9 benign scores (no recalibration yet)
    for _ in range(9):
        dg.update(0.1)
    assert dg.current_threshold == 0.5

    # 10th update triggers recalibration
    # median=0.1, MAD=0.0, threshold = 0.1 + 3.0*0.0 = 0.1
    dg.update(0.1)
    assert pytest.approx(dg.current_threshold) == 0.1


def test_drift_guard_dampening():
    # alpha = 0.1 (default)
    dg = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10, alpha=0.1)

    # Target threshold after recalibration will be 0.1
    # Initial is 0.5
    # New = 0.9 * 0.5 + 0.1 * 0.1 = 0.45 + 0.01 = 0.46
    for _ in range(10):
        dg.update(0.1)

    assert pytest.approx(dg.current_threshold) == 0.46


def test_drift_guard_no_move_on_anomalies():
    dg = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10)
    initial_threshold = dg.current_threshold

    # Feed anomalous scores (> 0.5)
    for _ in range(20):
        dg.update(0.9)

    # Threshold should not have moved because scores were > current_threshold
    assert dg.current_threshold == initial_threshold


def test_drift_guard_thread_safety():
    dg = AdversarialDriftGuard(window_size=1000, k=3.0, recalibrate_every=50)

    def worker():
        for _ in range(100):
            dg.update(float(np.random.uniform(0.0, 0.2)))

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify that total updates is 1000
    assert dg.to_dict()["total_updates"] == 1000
    # Threshold should be lower than 0.5
    assert dg.current_threshold < 0.5


def test_drift_guard_batch_update():
    dg = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10, alpha=1.0)
    scores = [0.1] * 10
    new_thresh = dg.update(scores)

    assert pytest.approx(new_thresh) == 0.1
    assert dg.to_dict()["total_updates"] == 10


def test_is_anomaly():
    dg = AdversarialDriftGuard(alpha=1.0)
    # Initial threshold is 0.5
    assert not dg.is_anomaly(0.4)
    assert dg.is_anomaly(0.6)

    # Recalibrate to lower threshold
    dg.update([0.1] * 50)

    assert dg.current_threshold < 0.2
    assert dg.is_anomaly(0.3)
    assert not dg.is_anomaly(0.05)
