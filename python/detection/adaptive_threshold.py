"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window adaptive threshold for anomaly scores.
"""

import threading
from collections import deque

import numpy as np


class AdversarialDriftGuard:
    """
    Sliding-window adaptive threshold for anomaly scores.
    Protects against adversarial drift using robust statistics (MAD).

    Algorithm:
      1. Maintains a ring buffer of the last N benign scores (default N=500)
      2. Every `recalibrate_every` new samples, recomputes:
           threshold = median(buffer) + k * (MAD * 1.4826)
      3. Exposes is_anomaly(score) -> bool
      4. Exposes current_threshold property
      5. Thread-safe (uses threading.Lock)
    """

    def __init__(self, window_size: int = 500, k: float = 3.5, recalibrate_every: int = 50):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5  # Initial baseline
        self._updates_since_recalc = 0
        self._total_updates = 0
        self._initialized = False

    def update(
        self,
        scores: float | list[float],
        is_confirmed_benign: bool = False,
        force_recalibrate: bool = False
    ) -> float:
        """
        Add score(s) to buffer and return current threshold.
        """
        if isinstance(scores, (int, float)):
            scores = [float(scores)]

        with self._lock:
            for s in scores:
                if is_confirmed_benign or s < self._current_threshold:
                    self._buffer.append(s)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if force_recalibrate or (self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10):
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Recompute threshold based on robust buffer statistics (MAD). Internal use only."""
        # Assumption: called while holding self._lock
        if not self._buffer:
            return

        data = np.array(self._buffer)
        median = np.median(data)
        mad = float(np.median(np.abs(data - median)))
        # Floor MAD to prevent collapse
        mad = max(0.01, mad)

        # 1.4826 makes MAD a consistent estimator of standard deviation
        new_threshold = float(median + self.k * (mad * 1.4826))

        # First recalibration sets the threshold directly
        if not self._initialized:
            self._current_threshold = new_threshold
            self._initialized = True
        else:
            # Maintain stability against adversarial drift
            alpha = 0.1
            self._current_threshold = (1 - alpha) * self._current_threshold + alpha * new_threshold

        self._updates_since_recalc = 0

    def set_threshold(self, value: float):
        with self._lock:
            self._current_threshold = value

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
                "version": "9.0.0-XOCHIMILCO",
            }


# Backward compatibility alias
AdaptiveThreshold = AdversarialDriftGuard
