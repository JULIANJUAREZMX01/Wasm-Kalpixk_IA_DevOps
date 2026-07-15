"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window adaptive threshold for anomaly scores.
"""

from __future__ import annotations

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
    Robust adaptive thresholding using Median and Median Absolute Deviation (MAD).
    Designed to resist adversarial drift where an attacker slowly increases
    baseline scores to eventually bypass detection.
    """

    def __init__(
        self,
        window_size: int = 500,
        k: float = 5.5,
        recalibrate_every: int = 100,
        alpha: float = 0.1,
    ):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every
        self.alpha = alpha  # Dampening factor for updates

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.8  # Initial conservative baseline
        self._median = 0.5
        self._mad = 0.1
        self._updates_since_recalc = 0
        self._total_updates = 0
        self._initialized = False

    def update(self, scores: float | list[float]) -> float:
        """
        Update with new scores and return current threshold.
        Supports single float or batch of scores.
        """
        if isinstance(scores, (int, float)):
            scores_list = [float(scores)]
        else:
            scores_list = scores

        with self._lock:
            for score in scores_list:
                self._buffer.append(score)
                self._updates_since_recalc += 1
                self._total_updates += 1

            if (
                self._updates_since_recalc >= self.recalibrate_every or not self._initialized
            ) and len(self._buffer) >= 20:
                self._recalibrate()

        return self.current_threshold

    def _recalibrate(self) -> None:
        """Robust recalibration using Median and MAD."""
        data = np.array(self._buffer)
        new_median = np.median(data)
        new_mad = np.median(np.abs(data - new_median))
        new_mad = max(new_mad, 0.01)

        if not self._initialized:
            self._median = new_median
            self._mad = new_mad
            self._initialized = True
        else:
            self._median = (1 - self.alpha) * self._median + self.alpha * new_median
            self._mad = (1 - self.alpha) * self._mad + self.alpha * new_mad

        self._current_threshold = float(self._median + self.k * (self._mad * 1.4826))
        self._current_threshold = min(max(self._current_threshold, 0.05), 0.99)
        self._updates_since_recalc = 0

    @property
    def current_threshold(self) -> float:
        with self._lock:
            return self._current_threshold

    def set_threshold(self, value: float) -> None:
        with self._lock:
            self._current_threshold = value

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "current_threshold": round(self._current_threshold, 4),
                "median": round(self._median, 4),
                "mad": round(self._mad, 4),
                "window_size": self.window_size,
                "buffer_len": len(self._buffer),
                "total_updates": self._total_updates,
            }
