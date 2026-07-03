"""
Additional security tests for AdversarialDriftGuard.
"""
from python.detection.adaptive_threshold import AdversarialDriftGuard


def test_adversarial_drift_guard_dampening():
    # recalibrate_every=10, alpha=0.1
    guard = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10, alpha=0.1)

    # 1. Establish baseline (initial threshold 0.5)
    for _ in range(10):
        guard.update(0.2)

    # First recalibration: median=0.2, mad=0.0
    assert guard.current_threshold == 0.2

    # 2. Poisoning attempt: feed scores slightly below current threshold
    # Buffer after this: [0.2]*10 + [0.19]*10
    # new_median = median([0.2]*10 + [0.19]*10) = 0.195
    # new_mad = 1.4826 * median(|[0.2, 0.19] - 0.195|) = 1.4826 * 0.005 = 0.007413
    # Dampened median = (1-0.1)*0.2 + 0.1*0.195 = 0.18 + 0.0195 = 0.1995
    # Dampened MAD = (1-0.1)*0 + 0.1*0.007413 = 0.0007413
    # Threshold = 0.1995 + 3 * 0.0007413 = 0.1995 + 0.0022239 = 0.2017239

    for _ in range(10):
        guard.update(0.19)

    # Threshold should move as expected
    assert round(guard.current_threshold, 6) == 0.201724
    assert guard._median == 0.1995

def test_batch_update_recalibration():
    guard = AdversarialDriftGuard(window_size=100, k=3.0, recalibrate_every=10)
    # Batch update of 25 scores should trigger 2 recalibrations
    guard.update([0.1] * 25)
    assert guard.to_dict()["total_updates"] == 25
    assert guard.current_threshold == 0.1 # 0.1 + 3*0
