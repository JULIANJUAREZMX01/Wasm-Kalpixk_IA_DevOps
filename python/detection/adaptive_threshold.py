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
    Uses Median and MAD (Median Absolute Deviation) for robust statistics.

    Algorithm:
      1. Maintains a ring buffer of the last N benign scores (default N=1000)
      2. Every `recalibrate_every` new samples, recomputes:
           threshold = median(buffer) + k * (MAD(buffer) * 1.4826)
      3. Exposes is_anomaly(score) -> bool
      4. Exposes current_threshold property
      5. Thread-safe (uses threading.Lock)
    """

    def __init__(
        self,
        window_size: int = 1000,
        k: float = 3.0,
        recalibrate_every: int = 100,
        alpha: float = 0.1
    ):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every
        self.alpha = alpha  # Update dampening factor

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5  # Initial baseline
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(self, score: float | list[float], is_confirmed_benign: bool = False) -> float:
        """
        Add score(s) to buffer. Returns the current threshold.
        Only updates buffer if is_confirmed_benign or score < current_threshold.
        """
        scores = [score] if isinstance(score, (int, float)) else score

        with self._lock:
            for s in scores:
                if is_confirmed_benign or s < self._current_threshold:
                    self._buffer.append(s)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            while self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10:
                self._recalibrate()
                self._updates_since_recalc -= self.recalibrate_every

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Recompute threshold based on robust buffer statistics. Internal use only."""
        if not self._buffer:
            return

        data = np.array(self._buffer)
        median = np.median(data)
        mad = np.median(np.abs(data - median))

        # Scale MAD by 1.4826 to align with standard deviation
        robust_std = mad * 1.4826
        target_threshold = float(median + self.k * robust_std)

        # Dampened update to prevent poisoning
        self._current_threshold = (1 - self.alpha) * self._current_threshold + self.alpha * target_threshold

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


# Backward compatibility alias
AdaptiveThreshold = AdversarialDriftGuard
