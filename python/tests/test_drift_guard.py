
import numpy as np
import pytest
from python.detection.adaptive_threshold import AdversarialDriftGuard

def test_drift_guard_initialization():
    guard = AdversarialDriftGuard(initial_threshold=0.8)
    assert guard.current_threshold == 0.8
    assert len(guard.buffer) == 0

def test_drift_guard_recalibrate():
    # Set alpha=1.0 to see immediate recalibration effect
    guard = AdversarialDriftGuard(alpha=1.0, z_threshold=2.0)

    # Fill buffer with normal scores (low values)
    normal_scores = [0.1] * 100
    guard.update(normal_scores)

    # After 100 samples, recalibrate should have fired
    # mean=0.1, std=0.0 -> threshold = 0.1 + 2.0*0 = 0.1
    assert guard.current_threshold == pytest.approx(0.1, abs=1e-5)

def test_drift_guard_poisoning_protection():
    # Alpha=1.0 for testing, so we see full update if it passes Z-score
    guard = AdversarialDriftGuard(alpha=1.0, z_threshold=3.0)

    # Initialize with stable baseline
    guard.update([0.1] * 100)
    baseline = guard.current_threshold

    # Try to inject a massive outlier (poisoning attempt)
    # Mean ~ 0.1, Std ~ 0.0 (very small)
    # Score 1.0 will have a huge Z-score and should be REJECTED from the buffer
    guard.update([1.0])

    # Verify the buffer didn't grow with the outlier and threshold didn't jump
    assert len(guard.buffer) == 100
    assert 1.0 not in guard.buffer
    assert guard.current_threshold == baseline

def test_drift_guard_dampening():
    # Use alpha=0.1 (default)
    guard = AdversarialDriftGuard(alpha=0.1, initial_threshold=0.8)

    # Buffer has enough to recalibrate
    scores = [0.2] * 100
    guard.update(scores)

    # target_threshold would be ~0.2
    # new_threshold = 0.9 * 0.8 + 0.1 * 0.2 = 0.72 + 0.02 = 0.74
    assert guard.current_threshold == pytest.approx(0.74)
