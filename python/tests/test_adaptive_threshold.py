"""
Tests for AdversarialDriftGuard.
"""

import threading

import numpy as np
import pytest

from python.detection.adaptive_threshold import AdversarialDriftGuard


def test_drift_guard_initialization():
    at = AdversarialDriftGuard(window_size=100, k=2.0, recalibrate_every=10, alpha=0.5)
    assert at.window_size == 100
    assert at.k == 2.0
    assert at.recalibrate_every == 10
    assert at.alpha == 0.5
    assert at.current_threshold == 0.5


def test_drift_guard_dampening():
    # recalibrate_every = 10, alpha = 0.1
    at = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10, alpha=0.1)

    # Feed 10 benign scores
    for _ in range(10):
        at.update(0.1)

    # Target threshold: mean(0.1) + 3*std(0.0) = 0.1
    # New threshold: 0.5 + 0.1 * (0.1 - 0.5) = 0.5 - 0.04 = 0.46
    assert pytest.approx(at.current_threshold) == 0.46


def test_drift_guard_batch_update():
    at = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10, alpha=1.0)
    # alpha=1.0 means it jumps directly to target

    at.update([0.1] * 10)
    assert pytest.approx(at.current_threshold) == 0.1


def test_drift_guard_no_move_on_anomalies():
    at = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10)
    initial_threshold = at.current_threshold

    # Feed anomalous scores (> 0.5)
    at.update([0.9] * 20)

    # Threshold should not have moved because scores were > current_threshold
    assert at.current_threshold == initial_threshold


def test_drift_guard_thread_safety():
    at = AdversarialDriftGuard(window_size=1000, k=3.0, recalibrate_every=50, alpha=0.1)

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
    # Threshold should be lower than 0.5
    assert at.current_threshold < 0.5


def test_drift_guard_to_dict():
    at = AdversarialDriftGuard(window_size=500, k=3.5, recalibrate_every=50, alpha=0.1)
    at.update([0.2] * 10)

    d = at.to_dict()
    assert d["window_size"] == 500
    assert d["k"] == 3.5
    assert d["alpha"] == 0.1
    assert d["buffer_len"] == 10
    assert d["total_updates"] == 10
    assert "current_threshold" in d


def test_is_anomaly():
    at = AdversarialDriftGuard(alpha=1.0) # No dampening for this test
    # Initial threshold is 0.5
    assert not at.is_anomaly(0.4)
    assert at.is_anomaly(0.6)

    # Recalibrate to lower threshold
    at.update([0.1] * 50)

    new_threshold = at.current_threshold
    assert new_threshold < 0.2
    assert at.is_anomaly(0.3)
    assert not at.is_anomaly(0.05)
