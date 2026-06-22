"""
Tests for AdversarialDriftGuard.
"""

import threading
import numpy as np
from python.detection.adaptive_threshold import AdversarialDriftGuard

def test_drift_guard_initialization():
    dg = AdversarialDriftGuard(window_size=100, k=2.0, recalibrate_every=10, alpha=0.5)
    assert dg.window_size == 100
    assert dg.k == 2.0
    assert dg.recalibrate_every == 10
    assert dg.alpha == 0.5
    assert dg.current_threshold == 0.5

def test_drift_guard_batch_update():
    dg = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10, alpha=1.0)
    # Batch update of 10 scores
    threshold = dg.update([0.1] * 10)
    # mean=0.1, std=0.0, target=0.1. alpha=1.0 means it jumps to 0.1
    assert round(threshold, 4) == 0.1
    assert round(dg.current_threshold, 4) == 0.1

def test_drift_guard_dampening():
    # alpha=0.1 means it only moves 10% towards target
    dg = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10, alpha=0.1)
    initial = dg.current_threshold # 0.5

    dg.update([0.1] * 10)
    # target = 0.1
    # expected = 0.5 + 0.1 * (0.1 - 0.5) = 0.5 - 0.04 = 0.46
    assert round(dg.current_threshold, 2) == 0.46

def test_drift_guard_no_move_on_anomalies():
    dg = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10)
    initial_threshold = dg.current_threshold

    # Feed anomalous scores (> 0.5)
    dg.update([0.9] * 20)

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

    assert dg.to_dict()["total_updates"] == 1000
    assert dg.current_threshold < 0.5

def test_is_anomaly():
    dg = AdversarialDriftGuard(alpha=1.0) # No dampening for easy test
    assert not dg.is_anomaly(0.4)
    assert dg.is_anomaly(0.6)

    dg.update([0.1] * 50)
    assert dg.current_threshold < 0.2
    assert dg.is_anomaly(0.3)
