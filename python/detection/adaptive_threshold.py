"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window adaptive threshold for anomaly scores with protection against poisoning.
"""

import threading
from collections import deque

import numpy as np


class AdversarialDriftGuard:
    """
    Sliding-window adaptive threshold for anomaly scores with protection against poisoning.

    Algorithm:
      1. Maintains a ring buffer of the last N benign scores (default N=500)
      2. Every `recalibrate_every` new samples, recomputes:
           threshold = median(buffer) + k * (MAD(buffer) * 1.4826)
      3. Implements update dampening (alpha=0.1) to prevent rapid threshold shifts.
    """

    def __init__(self, window_size: int = 500, k: float = 3.0, recalibrate_every: int = 50):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5  # Initial baseline
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(self, scores: float | list[float], is_confirmed_benign: bool = False) -> float:
        """Add score(s) to buffer and return current threshold."""
        score_list = (
            [scores] if isinstance(scores, (float, int, np.floating, np.integer)) else scores
        )

        with self._lock:
            for score in score_list:
                if is_confirmed_benign or score < self._current_threshold:
                    self._buffer.append(float(score))
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10:
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Recompute threshold based on robust statistics. Internal use only."""
        if not self._buffer:
            return
        data = np.array(self._buffer)
        median = np.median(data)
        mad = np.median(np.abs(data - median))
        target = float(median + self.k * (mad * 1.4826))

        # Dampening (alpha=0.1) prevents "boiling frog" poisoning
        alpha = 0.1
        self._current_threshold = (1 - alpha) * self._current_threshold + alpha * target
        self._updates_since_recalc = 0

    def is_anomaly(self, score: float) -> bool:
        """Return True if score exceeds adaptive threshold."""
        with self._lock:
            return score > self._current_threshold

    @property
    def current_threshold(self) -> float:
        return self._current_threshold

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "current_threshold": round(self._current_threshold, 4),
                "window_size": self.window_size,
                "buffer_len": len(self._buffer),
                "k": self.k,
                "total_updates": self._total_updates,
            }


# Backward compatibility
AdaptiveThreshold = AdversarialDriftGuard
