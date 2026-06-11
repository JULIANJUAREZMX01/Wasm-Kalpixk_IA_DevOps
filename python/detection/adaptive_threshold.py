"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window adaptive threshold for anomaly scores.
"""

import threading
from collections import deque

import numpy as np


class AdaptiveThreshold:
    """
    Sliding-window adaptive threshold for anomaly scores.

    Algorithm:
      1. Maintains a ring buffer of the last N benign scores (default N=500)
      2. Every `recalibrate_every` new samples, recomputes:
           threshold = mean(buffer) + k * std(buffer)   (default k=3.0)
      3. Exposes is_anomaly(score) -> bool
      4. Exposes current_threshold property
      5. Thread-safe (uses threading.RLock for re-entrancy)
    """

    def __init__(self, window_size: int = 500, k: float = 3.0, recalibrate_every: int = 50):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.RLock()
        self._current_threshold = 0.5  # Initial baseline
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(self, score: float, is_confirmed_benign: bool = False) -> None:
        """
        Add score to buffer.
        Only updates buffer if is_confirmed_benign or score < current_threshold.
        """
        with self._lock:
            if is_confirmed_benign or score < self._current_threshold:
                self._buffer.append(score)
                self._updates_since_recalc += 1
                self._total_updates += 1

                if self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10:
                    self._recalibrate()

    def _recalibrate(self) -> None:
        """Recompute threshold based on buffer statistics. Internal use only."""
        # Assumption: called while holding self._lock
        data = np.array(self._buffer)
        mean = np.mean(data)
        std = np.std(data)
        self._current_threshold = float(mean + self.k * std)
        self._updates_since_recalc = 0

    def is_anomaly(self, score: float) -> bool:
        """Return True if score exceeds adaptive threshold."""
        with self._lock:
            return score > self._current_threshold

    @property
    def current_threshold(self) -> float:
        """Current threshold value."""
        with self._lock:
            return self._current_threshold

    def to_dict(self) -> dict:
        """Serializable state for /api/status endpoint."""
        with self._lock:
            return {
                "current_threshold": round(self._current_threshold, 4),
                "window_size": self.window_size,
                "buffer_len": len(self._buffer),
                "k": self.k,
                "total_updates": self._total_updates,
            }


class AdversarialDriftGuard(AdaptiveThreshold):
    """
    [SEC-V9] Adversarial Drift Guard.
    Prevents "boiling frog" threshold poisoning attacks.

    Hardening:
      - Z-score outlier filtering: Discards scores with Z > 3.5 from buffer.
      - EMA dampening: Updates to current_threshold are dampened (alpha=0.1).
    """

    def __init__(self, window_size: int = 500, z_threshold: float = 3.5, alpha: float = 0.1):
        super().__init__(window_size=window_size, k=3.0, recalibrate_every=50)
        self.z_threshold = z_threshold
        self.alpha = alpha

    def update(self, scores: float | list[float]) -> float:
        """
        Hardened update: filters outliers and dampens threshold moves.
        Accepts single score or batch of scores.
        """
        if isinstance(scores, (int, float)):
            scores = [float(scores)]

        with self._lock:
            # If buffer is too small, just append (initialization phase)
            if len(self._buffer) < 20:
                for s in scores:
                    self._buffer.append(float(s))
                    self._total_updates += 1
                self._recalibrate()
                return self._current_threshold

            # Filter outliers before adding to buffer (Z-score filtering)
            data = np.array(self._buffer)
            mean = np.mean(data)
            std = np.std(data) + 1e-9

            for s in scores:
                z = abs(s - mean) / std
                if z < self.z_threshold:
                    self._buffer.append(float(s))
                    self._total_updates += 1
                    self._updates_since_recalc += 1

            if self._updates_since_recalc >= self.recalibrate_every:
                self._recalibrate_hardened()

            return self._current_threshold

    def _recalibrate_hardened(self) -> None:
        """EMA-dampened recalibration."""
        data = np.array(self._buffer)
        new_target = float(np.mean(data) + self.k * np.std(data))

        # Exponential Moving Average for the threshold itself
        self._current_threshold = (self.alpha * new_target) + (
            (1 - self.alpha) * self._current_threshold
        )
        self._updates_since_recalc = 0
