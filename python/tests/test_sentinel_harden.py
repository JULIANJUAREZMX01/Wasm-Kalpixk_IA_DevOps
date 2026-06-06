import pytest

from python.db.database import get_alerts, init_db, insert_alert
from python.detection.adaptive_threshold import AdversarialDriftGuard


def test_drift_guard_poisoning_protection():
    # alpha=0.1, z_threshold=3.5
    guard = AdversarialDriftGuard(window_size=100, alpha=0.1, z_threshold=3.5)

    # 1. Warm up with normal scores
    normal_scores = [0.1] * 50
    guard.update(normal_scores)

    initial_threshold = guard.current_threshold
    assert initial_threshold < 0.8

    # 2. Attempt poisoning with high scores (outliers)
    # These should be filtered by Z-score
    poison_scores = [0.9] * 50
    guard.update(poison_scores)

    # Threshold should not have moved UP (poisoned)
    assert guard.current_threshold <= initial_threshold + 0.01


def test_drift_guard_gradual_drift():
    guard = AdversarialDriftGuard(window_size=100, alpha=0.1, z_threshold=3.5)

    # Warm up
    guard.update([0.1] * 50)
    t1 = guard.current_threshold

    # Gradual drift (not outliers)
    guard.update([0.15] * 50)
    t2 = guard.current_threshold

    # Should adapt to gradual drift (moves towards 0.15 + 3*0 = 0.15)
    assert t2 < t1


@pytest.mark.asyncio
async def test_get_alerts_limit_hardening(monkeypatch, tmp_path):
    db_file = str(tmp_path / "test_harden.db")
    monkeypatch.setenv("KALPIXK_DB_PATH", db_file)

    await init_db()
    # Insert 10 alerts
    for i in range(10):
        await insert_alert({"ts": f"2023-10-27T10:00:{i:02d}Z", "anomaly_score": 0.5})

    # Test negative limit (SQLite bypass attempt)
    alerts, total = await get_alerts(limit=-1)
    assert len(alerts) == 1  # Clamped to 1

    # Test zero limit
    alerts, total = await get_alerts(limit=0)
    assert len(alerts) == 1

    # Test excessive limit
    alerts, total = await get_alerts(limit=9999)
    assert len(alerts) <= 500
