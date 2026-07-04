"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Adversarial-robust sliding-window adaptive threshold.
"""

import threading
from collections import deque
from typing import List, Union

import numpy as np


class AdversarialDriftGuard:
    """
    Robust adaptive threshold for anomaly scores using Median and MAD.
    Protects against "slow-burn" adversarial threshold poisoning.

    Algorithm:
      1. Maintains a ring buffer of the last N benign scores.
      2. Every `recalibrate_every` new samples, recomputes:
           median = np.median(buffer)
           mad = np.median(abs(buffer - median)) * 1.4826
           target_threshold = median + k * mad
      3. Applies dampening (alpha=0.1) to threshold updates to resist drift.
      4. Thread-safe (uses threading.Lock).
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
        self.alpha = alpha

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5  # Initial baseline
        self._updates_since_recalc = 0
        self._total_updates = 0
        self._initialized = False

    def update(self, score: Union[float, List[float]], is_confirmed_benign: bool = False) -> float:
        """
        Add score(s) to buffer and return the current threshold.
        Only updates buffer if is_confirmed_benign or score < current_threshold.
        """
        with self._lock:
            scores = [score] if isinstance(score, (int, float)) else score

            for s in scores:
                if is_confirmed_benign or s < self._current_threshold:
                    self._buffer.append(float(s))
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            while self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10:
                self._recalibrate()
                self._updates_since_recalc -= self.recalibrate_every

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Recompute threshold using Median and MAD. Internal use only."""
        # Assumption: called while holding self._lock
        data = np.array(self._buffer)
        median = np.median(data)
        # MAD consistency factor for normal distribution is 1.4826
        mad = np.median(np.abs(data - median)) * 1.4826

        target_threshold = float(median + self.k * mad)

        if not self._initialized:
            self._current_threshold = target_threshold
            self._initialized = True
        else:
            # Dampened update to resist sudden adversarial shifts
            self._current_threshold = (1 - self.alpha) * self._current_threshold + self.alpha * target_threshold

    def is_anomaly(self, score: float) -> bool:
        """Return True if score exceeds adaptive threshold."""
        with self._lock:
            return score > self._current_threshold

    def set_threshold(self, value: float) -> None:
        """Manually override current threshold."""
        with self._lock:
            self._current_threshold = value
            self._initialized = True

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
                "initialized": self._initialized
            }

# Backward compatibility alias
AdaptiveThreshold = AdversarialDriftGuard
