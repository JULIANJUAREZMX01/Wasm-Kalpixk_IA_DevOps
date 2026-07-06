"""Tests for AdaptiveThreshold."""

import threading

import numpy as np
import pytest

from python.detection.adaptive_threshold import AdaptiveThreshold


def test_adaptive_threshold_initialization():
    at = AdaptiveThreshold(window_size=100, k=2.0, recalibrate_every=10)
    assert at.window_size == 100
    assert at.k == 2.0
    assert at.recalibrate_every == 10
    assert at.current_threshold == 0.5


def test_adaptive_threshold_recalibration():
    at = AdaptiveThreshold(window_size=100, k=3.5, recalibrate_every=10)
    for _ in range(20):
        at.update(0.1)
    # Median=0.1, MAD=0.01 (floor), Threshold = 0.1 + 3.5 * (0.01 * 1.4826) = 0.151891
    assert at.current_threshold == pytest.approx(0.1 + 3.5 * (0.01 * 1.4826))


def test_adaptive_threshold_dampened_update():
    at = AdaptiveThreshold(window_size=100, k=3.5, recalibrate_every=10, alpha=0.1)
    # 1st calibration (20 samples)
    for _ in range(20):
        at.update(0.1)
    t1 = at.current_threshold
    # 2nd calibration (another 10 samples) - majority remains 0.1
    # Median of [0.1*20, 0.3*10] is 0.1.
    # To shift median, we need more than half the window or just more than current buffer half.
    for _ in range(30):
        at.update(0.3)
    t2 = at.current_threshold
    # Median of [0.1*20, 0.3*30] is 0.3.
    # New median = (1-0.1)*0.1 + 0.1*0.3 = 0.12
    assert t2 > t1
    assert t2 < 0.5


def test_adaptive_threshold_thread_safety():
    at = AdaptiveThreshold(window_size=1000, k=3.5, recalibrate_every=50)

    def worker():
        for _ in range(100):
            at.update(np.random.uniform(0.0, 0.2))

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert at.to_dict()["total_updates"] == 1000
    assert at.current_threshold < 0.5


def test_is_anomaly():
    at = AdaptiveThreshold()
    assert not at.is_anomaly(0.4)
    assert at.is_anomaly(0.6)
    # Recalibrate to lower
    for _ in range(100):
        at.update(0.1)
    assert at.is_anomaly(0.3)
