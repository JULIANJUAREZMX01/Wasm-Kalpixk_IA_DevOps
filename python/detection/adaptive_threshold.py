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
      5. Thread-safe (uses threading.Lock)
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


class AdversarialDriftGuard:
    """
    Robust adaptive threshold using Median and MAD (Median Absolute Deviation).
    Designed to resist adversarial drift by using dampened updates and robust statistics.
    """

    def __init__(
        self,
        window_size: int = 1000,
        k: float = 5.5,
        recalibrate_every: int = 100,
        alpha: float = 0.1,
    ):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every
        self.alpha = alpha  # Dampening factor for statistics updates

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()

        self._median = 0.5
        self._mad = 0.1
        self._current_threshold = 0.8

        self._updates_since_recalc = 0
        self._total_updates = 0
        self._initialized = False

    def update(self, scores: float | list[float], force_recalibrate: bool = False) -> float:
        """
        Update the guard with new scores and return the current adaptive threshold.
        """
        if isinstance(scores, (int, float)):
            scores = [float(scores)]

        with self._lock:
            for score in scores:
                self._buffer.append(score)
                self._updates_since_recalc += 1
                self._total_updates += 1

            if force_recalibrate or (
                self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 20
            ):
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Robust recalibration using dampened Median/MAD."""
        # Assumption: called while holding self._lock
        if not self._buffer:
            return

        data = np.array(self._buffer)
        new_median = float(np.median(data))
        new_mad = float(np.median(np.abs(data - new_median)))

        # Ensure MAD doesn't collapse to zero (floor of 0.01)
        new_mad = max(0.01, new_mad)

        if not self._initialized:
            self._median = new_median
            self._mad = new_mad
            self._initialized = True
        else:
            # Dampened update: EMA of the statistics to resist sudden adversarial shifts
            self._median = (1 - self.alpha) * self._median + self.alpha * new_median
            self._mad = (1 - self.alpha) * self._mad + self.alpha * new_mad

        # Robust threshold formula: Median + k * (MAD * 1.4826)
        # 1.4826 is the scaling factor to make MAD a consistent estimator of StdDev for Normal distribution
        self._current_threshold = float(self._median + self.k * (self._mad * 1.4826))
        self._updates_since_recalc = 0

    @property
    def current_threshold(self) -> float:
        with self._lock:
            return self._current_threshold

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "current_threshold": round(self._current_threshold, 4),
                "median": round(self._median, 4),
                "mad": round(self._mad, 4),
                "window_size": self.window_size,
                "buffer_len": len(self._buffer),
                "total_updates": self._total_updates,
                "initialized": self._initialized,
            }
