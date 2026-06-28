"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
AdversarialDriftGuard — Robust adaptive threshold for anomaly scores.
Uses Median/MAD and update dampening to prevent threshold poisoning.
"""

import threading
from collections import deque
from typing import List, Union

import numpy as np


class AdversarialDriftGuard:
    """
    Robust adaptive threshold for anomaly scores.

    Algorithm (v9.0.0-XOCHIMILCO):
      1. Maintains a ring buffer of the last N benign scores.
      2. Uses robust statistics: Median and Median Absolute Deviation (MAD).
      3. Implements update dampening (alpha) to slow down threshold shifts.
      4. Processes batch updates efficiently.
    """

    def __init__(
        self,
        window_size: int = 500,
        k: float = 3.0,
        recalibrate_every: int = 50,
        alpha: float = 0.1,
    ):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every
        self.alpha = alpha  # Dampening factor

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5  # Initial baseline
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(self, score: Union[float, List[float]], is_confirmed_benign: bool = False) -> float:
        """
        Add score(s) to buffer and return current threshold.
        Only updates buffer if is_confirmed_benign or score < current_threshold.
        """
        scores = score if isinstance(score, list) else [score]

        with self._lock:
            for s in scores:
                if is_confirmed_benign or s < self._current_threshold:
                    self._buffer.append(s)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            # Recalibrate if recalibrate_every is exceeded
            while self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10:
                self._recalibrate()
                self._updates_since_recalc -= self.recalibrate_every

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Recompute threshold based on robust statistics. Internal use only."""
        # Assumption: called while holding self._lock
        if not self._buffer:
            self._current_threshold = 0.5
            return

        data = np.array(self._buffer)
        median = np.median(data)

        # Robust standard deviation: MAD * 1.4826
        mad = np.median(np.abs(data - median))
        robust_std = mad * 1.4826

        target_threshold = float(median + self.k * robust_std)

        if np.isnan(target_threshold):
            target_threshold = 0.5

        # Apply dampening (exponential smoothing)
        # new = old + alpha * (target - old)
        self._current_threshold = self._current_threshold + self.alpha * (
            target_threshold - self._current_threshold
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
