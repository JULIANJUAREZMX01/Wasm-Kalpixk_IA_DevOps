"""
Tests for AdversarialDriftGuard.
"""

import numpy as np
import pytest
from python.detection.adaptive_threshold import AdversarialDriftGuard

def test_adversarial_drift_guard_dampening():
    # recalibrate_every=10, alpha=0.1
    # We need at least 10 samples in buffer to recalibrate
    guard = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10, alpha=0.1)
    initial_threshold = guard.current_threshold # 0.5

    # Fill buffer with very low scores to force a big drop in target threshold
    for _ in range(10):
        guard.update(0.01)

    # Target threshold would be ~0.01 + 3*0 = 0.01
    # With alpha=0.1, new_threshold = 0.5 + 0.1 * (0.01 - 0.5) = 0.5 - 0.049 = 0.451
    assert guard.current_threshold < initial_threshold
    assert guard.current_threshold > 0.44

def test_adversarial_drift_guard_batch_update():
    # recalibrate_every=10, we need 10 samples
    guard = AdversarialDriftGuard(recalibrate_every=10)
    scores = [0.1] * 10
    guard.update(scores)

    assert guard.to_dict()["total_updates"] == 10
    assert guard.current_threshold < 0.5

def test_adversarial_drift_guard_poisoning_protection():
    # Boiling frog attack attempt: gradually increase scores just below threshold
    # recalibrate_every=10, we need 10 samples
    guard = AdversarialDriftGuard(recalibrate_every=10, alpha=0.1)

    # Initial threshold 0.5
    # First batch: all 0.4
    guard.update([0.4] * 10)
    t1 = guard.current_threshold
    assert t1 < 0.5 # Should move towards 0.4

    # Second batch: all 0.45 (slightly higher)
    guard.update([0.45] * 10)
    t2 = guard.current_threshold

    # Because of dampening (alpha=0.1), it should move slowly
    assert abs(t2 - t1) < 0.05

def test_adversarial_drift_guard_empty_buffer():
    guard = AdversarialDriftGuard()
    # Mock empty buffer recalibrate
    with guard._lock:
        guard._buffer.clear()
        guard._recalibrate()
    assert guard.current_threshold == 0.5
