"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window adaptive threshold for anomaly scores.
"""

import threading
from collections import deque
from typing import Union, List

import numpy as np


class AdversarialDriftGuard:
    """
    Sliding-window adaptive threshold for anomaly scores with protection against poisoning.

    Algorithm:
      1. Maintains a ring buffer of the last N benign scores (default N=500)
      2. Every `recalibrate_every` new samples, recomputes:
           threshold = median(buffer) + k * MAD(buffer)
      3. Implements update dampening (alpha=0.1) to prevent rapid threshold shifts.
      4. Exposes is_anomaly(score) -> bool
      5. Exposes current_threshold property
      6. Thread-safe (uses threading.Lock)
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

    def update(self, scores: Union[float, List[float]], is_confirmed_benign: bool = False) -> float:
        """
        Add score(s) to buffer and return current threshold.
        Only updates buffer if is_confirmed_benign or score < current_threshold.
        """
        if isinstance(scores, (float, int, np.floating, np.integer)):
            score_list = [float(scores)]
        else:
            score_list = scores

        with self._lock:
            for score in score_list:
                if is_confirmed_benign or score < self._current_threshold:
                    self._buffer.append(score)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10:
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Recompute threshold based on robust statistics. Internal use only."""
        # Assumption: called while holding self._lock
        if not self._buffer:
            return

        data = np.array(self._buffer)
        # Robust statistics: Median and Median Absolute Deviation (MAD)
        # are more resistant to outliers/poisoning than mean/std.
        median = np.median(data)
        mad = np.median(np.abs(data - median))

        # 1.4826 is the consistency constant to make MAD equivalent to STD for normal distribution
        target_threshold = float(median + self.k * (mad * 1.4826))

        # Update dampening (alpha=0.1) to prevent "boiling frog" poisoning attacks
        alpha = 0.1
        self._current_threshold = (1 - alpha) * self._current_threshold + alpha * target_threshold

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

# Backward compatibility alias
AdaptiveThreshold = AdversarialDriftGuard
