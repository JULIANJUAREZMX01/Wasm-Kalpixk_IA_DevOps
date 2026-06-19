
import numpy as np

from python.detection.adaptive_threshold import AdversarialDriftGuard


def test_drift_guard_initialization():
    guard = AdversarialDriftGuard(window_size=100, z_score=3.0, recalibrate_every=10, alpha=0.1)
    assert guard.window_size == 100
    assert guard.z_score == 3.0
    assert guard.recalibrate_every == 10
    assert guard.alpha == 0.1
    assert guard.current_threshold == 0.5

def test_drift_guard_dampening():
    # recalibrate_every=10, alpha=0.1
    guard = AdversarialDriftGuard(window_size=100, z_score=3.0, recalibrate_every=10, alpha=0.1)

    # Feed 10 low scores. Target threshold should be 0.1 + 3*0 = 0.1
    # New threshold = 0.9 * 0.5 + 0.1 * 0.1 = 0.45 + 0.01 = 0.46
    scores = [0.1] * 10
    guard.update(scores)

    assert round(guard.current_threshold, 2) == 0.46

def test_drift_guard_poisoning_protection():
    guard = AdversarialDriftGuard(window_size=100, z_score=3.0, recalibrate_every=10, alpha=0.1)
    initial_threshold = guard.current_threshold

    # Feed high scores (> current_threshold * 1.5)
    # 0.5 * 1.5 = 0.75. Let's feed 0.8
    guard.update([0.8] * 20)

    # Buffer should be empty or not updated enough to recalibrate
    assert guard.to_dict()["buffer_len"] == 0
    assert guard.current_threshold == initial_threshold

def test_drift_guard_batch_update():
    guard = AdversarialDriftGuard(window_size=500, recalibrate_every=50)
    scores = np.random.uniform(0.1, 0.2, 100).tolist()
    guard.update(scores)

    # Recalibration should have happened twice
    assert guard.to_dict()["total_updates"] == 100
    assert guard.current_threshold < 0.5
