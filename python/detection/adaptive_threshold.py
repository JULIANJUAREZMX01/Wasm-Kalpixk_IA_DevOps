"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window adaptive threshold for anomaly scores.
v9.0.0-XOCHIMILCO: AdversarialDriftGuard implementation.
"""

import threading
from collections import deque
from typing import Union

import numpy as np


class AdversarialDriftGuard:
    """
    Robust sliding-window adaptive threshold for anomaly scores.
    Protects against adversarial 'slow-burn' threshold poisoning.

    Algorithm:
      1. Maintains a ring buffer of the last N benign scores (default N=500)
      2. Uses Median and Median Absolute Deviation (MAD) for robust statistics.
      3. Threshold = Median + k * (1.4826 * MAD)
      4. Every `recalibrate_every` new samples, recomputes the target threshold.
      5. Applies update dampening (alpha=0.1) to prevent rapid threshold shifts.
      6. Thread-safe.
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

    def update(self, scores: Union[float, list[float]], is_confirmed_benign: bool = False) -> float:
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

            while self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10:
                self._recalibrate()
                self._updates_since_recalc -= self.recalibrate_every

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Recompute threshold based on robust statistics. Internal use only."""
        # Assumption: called while holding self._lock
        if not self._buffer:
            return

        data = np.array(self._buffer)
        median = np.median(data)
        mad = np.median(np.abs(data - median))

        # Scale MAD to match standard deviation for normal distribution
        # k=3.0 covers 99.7% of a normal distribution
        robust_std = 1.4826 * mad
        target_threshold = float(median + self.k * robust_std)

        # Apply dampening to prevent rapid shifts (poisoning defense)
        if np.isnan(target_threshold):
            self._current_threshold = 0.5
        else:
            self._current_threshold = (
                (1 - self.alpha) * self._current_threshold + self.alpha * target_threshold
            )

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
                "alpha": self.alpha,
                "total_updates": self._total_updates,
            }

# Backward compatibility alias
AdaptiveThreshold = AdversarialDriftGuard
