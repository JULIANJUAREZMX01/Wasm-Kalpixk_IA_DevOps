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
    [ATLATL-ORDNANCE] Adversarial Drift Guard v9.0.0-XOCHIMILCO
    Robust sliding-window adaptive threshold using Median and MAD.

    Algorithm:
      1. Maintains a ring buffer of the last N benign scores (default N=500)
      2. Every `recalibrate_every` new samples, recomputes:
           threshold = median(buffer) + k * MAD(buffer) * 1.4826
      3. Updates are dampened by alpha (0.1) to prevent rapid poisoning.
      4. Thread-safe (uses threading.Lock)
    """

    def __init__(self, window_size: int = 500, k: float = 3.5, recalibrate_every: int = 50, alpha: float = 0.1):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every
        self.alpha = alpha

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5  # Initial baseline
        self._updates_since_recalc = 0
        self._total_updates = 0

        # Robust statistics
        self._median = 0.5
        self._mad = 0.1

    def update(self, score: float | list[float], is_confirmed_benign: bool = False, force_recalibrate: bool = False) -> None:
        """
        Add score(s) to buffer and recalibrate if needed.
        Only updates buffer if is_confirmed_benign or score < current_threshold.
        """
        scores = [score] if isinstance(score, (int, float, np.float32, np.float64)) else score

        with self._lock:
            for s in scores:
                if is_confirmed_benign or s < self._current_threshold:
                    self._buffer.append(float(s))
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if (self._updates_since_recalc >= self.recalibrate_every or force_recalibrate) and len(self._buffer) >= 10:
                while self._updates_since_recalc >= self.recalibrate_every or force_recalibrate:
                    self._recalibrate()
                    force_recalibrate = False
                    if self._updates_since_recalc < self.recalibrate_every:
                        break

    def _recalibrate(self) -> None:
        """Recompute threshold based on robust statistics. Internal use only."""
        # Assumption: called while holding self._lock
        data = np.array(self._buffer)
        new_median = float(np.median(data))
        new_mad = float(np.median(np.abs(data - new_median)))

        if new_mad == 0:
            new_mad = 0.001 # Prevent collapse

        # Aligned with normal distribution (1.4826 * MAD ~ STD)
        target_threshold = new_median + self.k * new_mad * 1.4826

        # Dampened update to prevent 'boiling frog' attacks
        self._current_threshold = (1 - self.alpha) * self._current_threshold + self.alpha * target_threshold

        self._median = new_median
        self._mad = new_mad
        self._updates_since_recalc = 0

    def set_threshold(self, value: float) -> None:
        """Manually set the current threshold."""
        with self._lock:
            self._current_threshold = value

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
                "median": round(self._median, 4),
                "mad": round(self._mad, 4),
                "total_updates": self._total_updates,
            }

# Backward compatibility alias
AdaptiveThreshold = AdversarialDriftGuard
