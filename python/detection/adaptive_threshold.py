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
    Robust sliding-window adaptive threshold for anomaly scores.
    Designed to resist 'boiling frog' poisoning attacks by using:
      1. Median and MAD (Median Absolute Deviation) instead of Mean/Std.
      2. Dampened updates (alpha=0.1) to prevent rapid threshold jumps.
    """

    def __init__(
        self,
        window_size: int = 500,
        k: float = 3.0,
        recalibrate_every: int = 50,
        alpha: float = 0.1
    ):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every
        self.alpha = alpha

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5  # Initial baseline
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(self, score: float | list[float], is_confirmed_benign: bool = False) -> float:
        """
        Add score(s) to buffer and return the current threshold.
        """
        if isinstance(score, (float, int, np.float32)):
            scores = [score]
        else:
            scores = score

        with self._lock:
            for s in scores:
                if is_confirmed_benign or s < self._current_threshold:
                    self._buffer.append(float(s))
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10:
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Recompute threshold using robust statistics and dampening."""
        # Assumption: called while holding self._lock
        data = np.array(self._buffer)
        if len(data) == 0:
            return

        median = np.median(data)
        # Robust scale estimator: 1.4826 * Median Absolute Deviation
        mad = np.median(np.abs(data - median))
        robust_std = 1.4826 * mad

        target_threshold = float(median + self.k * robust_std)

        # Dampening: move towards target slowly to prevent rapid poisoning
        self._current_threshold = (1 - self.alpha) * self._current_threshold + self.alpha * target_threshold
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
                "alpha": self.alpha,
            }

# Backward compatibility alias
AdaptiveThreshold = AdversarialDriftGuard
