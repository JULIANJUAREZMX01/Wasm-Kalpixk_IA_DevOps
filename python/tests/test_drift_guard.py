from python.detection.adaptive_threshold import AdversarialDriftGuard


def test_drift_guard_initialization():
    guard = AdversarialDriftGuard(window_size=100, z_threshold=3.0, recalibrate_every=10, alpha=0.5)
    assert guard.window_size == 100
    assert guard.current_threshold == 0.95


def test_drift_guard_batch_update_and_recalibrate():
    # Recalibrate every 10 updates, alpha=1.0 for immediate change in test
    guard = AdversarialDriftGuard(window_size=500, z_threshold=3.0, recalibrate_every=10, alpha=1.0)

    # Initial threshold 0.95
    # Batch of 10 normal scores
    scores = [0.1] * 10
    new_threshold = guard.update(scores)

    # Recalibration should have happened: mean=0.1, std=0.0 -> threshold = 0.1 + 3.0*0 = 0.1
    assert new_threshold == 0.1
    assert guard.current_threshold == 0.1


def test_drift_guard_poisoning_protection():
    guard = AdversarialDriftGuard(window_size=500, z_threshold=3.0, recalibrate_every=10, alpha=1.0)

    # 1. Establish low threshold
    guard.update([0.1] * 10)
    assert guard.current_threshold == 0.1

    # 2. Attempt to poison with high scores (obvious anomalies)
    # These should be filtered out by 's < self._current_threshold'
    poison_scores = [0.9] * 20
    guard.update(poison_scores)

    # Threshold should NOT change
    assert guard.current_threshold == 0.1


def test_drift_guard_dampening():
    # alpha = 0.1 (dampened)
    guard = AdversarialDriftGuard(window_size=500, z_threshold=3.0, recalibrate_every=10, alpha=0.1)

    # Initial threshold 0.95
    # Target threshold (from scores) would be 0.1
    # New threshold = 0.9 * 0.95 + 0.1 * 0.1 = 0.855 + 0.01 = 0.865
    guard.update([0.1] * 10)

    assert round(guard.current_threshold, 3) == 0.865
