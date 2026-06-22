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
        """
        Recompute threshold based on buffer statistics. Internal use only.
        v9: Uses robust statistics (median and MAD) to prevent slow-burn poisoning.
        """
        # Assumption: called while holding self._lock
        data = np.array(self._buffer)
        if len(data) < 10:
            return

        # Robust statistics: Median instead of Mean
        median = np.median(data)

        # Median Absolute Deviation (MAD) as a robust scale estimator
        # MAD = median(|x_i - median(x)|)
        mad = np.median(np.abs(data - median))

        # Consistency factor for normal distribution (approx 1.4826)
        # But we use a direct robust Z-score approach with k
        # Standard deviation approx 1.4826 * MAD
        robust_std = 1.4826 * mad if mad > 0 else np.std(data)

        # New threshold calculation
        new_threshold = float(median + self.k * robust_std)

        # Dampening update (alpha=0.2) to prevent sudden jumps
        alpha = 0.2
        self._current_threshold = (1 - alpha) * self._current_threshold + alpha * new_threshold

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


# Legacy alias
AdaptiveThreshold = AdversarialDriftGuard
