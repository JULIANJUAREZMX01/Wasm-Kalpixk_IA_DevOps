"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
AdversarialDriftGuard — Robust adaptive thresholding for anomaly scores.
Uses Median/MAD (Median Absolute Deviation) and dampened updates
to prevent "boiling frog" adversarial poisoning.
"""

import threading
from collections import deque
from typing import Any

import numpy as np


class AdversarialDriftGuard:
    """
    Robust adaptive threshold for anomaly scores.

    Algorithm:
      1. Maintains a ring buffer of the last N benign scores (default N=500)
      2. Every `recalibrate_every` new samples, recomputes:
           target = median(buffer) + k * MAD(buffer) * 1.4826
      3. Threshold is updated using dampening (alpha=0.1):
           threshold = (1 - alpha) * current_threshold + alpha * target
      4. Exposes is_anomaly(score) -> bool
      5. Thread-safe (uses threading.Lock)
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

    def update(
        self,
        scores: float | list[float],
        is_confirmed_benign: bool = False,
        force_recalibrate: bool = False
    ) -> float:
        """
        Add score(s) to buffer and return current threshold.
        Only updates buffer if is_confirmed_benign or score < current_threshold.
        """
        if isinstance(scores, (int, float)):
            scores = [float(scores)]

        with self._lock:
            for score in scores:
                if is_confirmed_benign or score < self._current_threshold:
                    self._buffer.append(score)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if force_recalibrate or (
                self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10
            ):
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Recompute threshold based on robust statistics. Internal use only."""
        # Assumption: called while holding self._lock
        data = np.array(self._buffer)
        if len(data) < 2:
            return

        median = np.median(data)
        # Median Absolute Deviation (MAD)
        mad = np.median(np.abs(data - median))
        # Scale MAD to align with standard deviation for normal distribution
        robust_std = mad * 1.4826

        target = float(median + self.k * robust_std)

        # Dampened update to prevent rapid poisoning shifts
        self._current_threshold = (1 - self.alpha) * self._current_threshold + self.alpha * target
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

    @current_threshold.setter
    def current_threshold(self, value: float) -> None:
        """Set current threshold value. Thread-safe."""
        with self._lock:
            self._current_threshold = value

    def to_dict(self) -> dict[str, Any]:
        """Serializable state for /api/status endpoint."""
        with self._lock:
            return {
                "current_threshold": round(self._current_threshold, 4),
                "window_size": self.window_size,
                "buffer_len": len(self._buffer),
                "k": self.k,
                "alpha": self.alpha,
                "total_updates": self._total_updates,
                "method": "median_mad_dampened"
            }

# Backward compatible alias
AdaptiveThreshold = AdversarialDriftGuard
