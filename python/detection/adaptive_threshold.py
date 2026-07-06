"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
AdversarialDriftGuard — Robust adaptive threshold for anomaly scores.
Uses Median and Median Absolute Deviation (MAD) to resist threshold poisoning.
"""

import threading
from collections import deque
from typing import List, Union

import numpy as np


class AdversarialDriftGuard:
    """
    Robust adaptive threshold for anomaly scores using Median and MAD.
    Designed to resist adversarial drift (poisoning) by using dampened updates.

    Algorithm:
      1. Maintains a ring buffer of the last N scores.
      2. Threshold = Median + k * (MAD * 1.4826)
      3. Recalibration uses a dampening factor (alpha=0.1) to slowly adjust
         to new normal distributions.
    """

    def __init__(
        self,
        window_size: int = 1000,
        k: float = 3.5,
        recalibrate_every: int = 100,
        alpha: float = 0.1
    ):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every
        self.alpha = alpha

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5
        self._median = 0.5
        self._mad = 0.1
        self._updates_since_recalc = 0
        self._total_updates = 0
        self._initialized = False

    def update(
        self,
        scores: Union[float, List[float]],
        force_recalibrate: bool = False
    ) -> float:
        """
        Update the guard with new score(s).
        Returns the current adaptive threshold.
        """
        if isinstance(scores, (int, float)):
            scores = [float(scores)]

        with self._lock:
            for s in scores:
                self._buffer.append(s)
                self._updates_since_recalc += 1
                self._total_updates += 1

            if force_recalibrate or (
                self._updates_since_recalc >= self.recalibrate_every
                and len(self._buffer) >= 20
            ):
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Recompute threshold using robust statistics and dampening."""
        data = np.array(self._buffer)
        new_median = float(np.median(data))
        new_mad = float(np.median(np.abs(data - new_median)))

        # MAD floor to prevent threshold collapse
        new_mad = max(new_mad, 0.01)

        if not self._initialized:
            self._median = new_median
            self._mad = new_mad
            self._initialized = True
        else:
            # Dampened update to resist sudden drift
            self._median = (1 - self.alpha) * self._median + self.alpha * new_median
            self._mad = (1 - self.alpha) * self._mad + self.alpha * new_mad

        # Robust threshold: Median + k * (MAD * 1.4826)
        # 1.4826 is the scaling factor to make MAD consistent with StdDev for Normal distribution.
        self._current_threshold = float(self._median + self.k * (self._mad * 1.4826))
        self._updates_since_recalc = 0

    def is_anomaly(self, score: float) -> bool:
        """Check if a score exceeds the current adaptive threshold."""
        with self._lock:
            return score > self._current_threshold

    def set_threshold(self, value: float) -> None:
        """Manually override the detection threshold."""
        with self._lock:
            self._current_threshold = value

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
                "initialized": self._initialized
            }


# Backward compatibility alias
AdaptiveThreshold = AdversarialDriftGuard
