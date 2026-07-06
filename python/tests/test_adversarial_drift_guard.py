"""
Tests for AdversarialDriftGuard (v9).
"""

import threading

import numpy as np
import pytest

from python.detection.adaptive_threshold import AdversarialDriftGuard


def test_guard_initialization():
    guard = AdversarialDriftGuard(window_size=100, k=2.0, recalibrate_every=10)
    assert guard.window_size == 100
    assert guard.k == 2.0
    assert guard.recalibrate_every == 10
    assert guard.current_threshold == 0.5


def test_guard_recalibration():
    # recalibrate_every = 20, window_size = 100
    guard = AdversarialDriftGuard(window_size=100, k=3.5, recalibrate_every=20)

    # Feed 19 scores (no recalibration yet because < 20 updates)
    for _ in range(19):
        guard.update(0.1)
    assert guard.current_threshold == 0.5

    # 20th update triggers recalibration
    guard.update(0.1)
    # Median=0.1, MAD=0.01 (floor), Threshold = 0.1 + 3.5 * (0.01 * 1.4826) = 0.151891
    assert guard.current_threshold == pytest.approx(0.1 + 3.5 * (0.01 * 1.4826))


def test_guard_dampened_update():
    # alpha=0.1
    guard = AdversarialDriftGuard(window_size=100, k=3.5, recalibrate_every=20, alpha=0.1)

    # First calibration
    for _ in range(20):
        guard.update(0.1)

    first_threshold = guard.current_threshold
    assert first_threshold < 0.2

    # Second calibration with higher scores
    for _ in range(20):
        guard.update(0.3)

    second_threshold = guard.current_threshold
    # Should increase but slowly due to alpha=0.1
    assert second_threshold > first_threshold
    assert second_threshold < 0.3 # Dampened


def test_guard_thread_safety():
    guard = AdversarialDriftGuard(window_size=1000, k=3.5, recalibrate_every=50)

    def worker():
        for _ in range(100):
            guard.update(np.random.uniform(0.0, 0.2))

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert guard.to_dict()["total_updates"] == 1000
    assert guard.current_threshold < 0.5


def test_guard_to_dict():
    guard = AdversarialDriftGuard(window_size=500, k=3.5, recalibrate_every=50)
    for _ in range(10):
        guard.update(0.2)

    d = guard.to_dict()
    assert d["buffer_len"] == 10
    assert d["total_updates"] == 10
    assert "median" in d
    assert "mad" in d
