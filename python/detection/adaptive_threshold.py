"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
AdversarialDriftGuard — Robust adaptive threshold for anomaly scores.
Uses Median/MAD and update dampening to prevent adversarial poisoning.
"""

import threading
from collections import deque

import numpy as np


class AdversarialDriftGuard:
    """
    Robust adaptive thresholding to protect against 'slow-burn' poisoning attacks.

    Security Enhancements:
      1. Robust Statistics: Uses Median and Median Absolute Deviation (MAD)
         instead of Mean/Std, making it resilient to outliers and poisoning.
      2. Update Dampening: Alpha-factor smoothing prevents sudden jumps in
         threshold that attackers might try to induce.
      3. Thread-Safe: Atomic updates and recalibrations.
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

    def update(
        self,
        scores: float | list[float],
        is_confirmed_benign: bool = False,
        force_recalibrate: bool = False,
    ) -> float:
        """
        Add score(s) to buffer and return current threshold.
        Only updates buffer if is_confirmed_benign or score < current_threshold.
        """
        if isinstance(scores, (int, float)):
            scores_list = [float(scores)]
        else:
            scores_list = scores

        with self._lock:
            for score in scores_list:
                if is_confirmed_benign or score < self._current_threshold:
                    self._buffer.append(score)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            # Recalibrate if batch threshold met or forced
            if force_recalibrate or (
                self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10
            ):
                self._recalibrate(force=force_recalibrate)

            return self._current_threshold

    def _recalibrate(self, force: bool = False) -> None:
        """Recompute threshold using robust statistics. Internal use only."""
        # Assumption: called while holding self._lock
        if not self._buffer:
            return

        data = np.array(self._buffer)
        median = np.median(data)

        # Median Absolute Deviation (MAD)
        mad = np.median(np.abs(data - median))

        # Consistency constant for normal distribution: 1.4826
        # robust_std = MAD * 1.4826
        robust_std = mad * 1.4826

        target_threshold = float(median + self.k * robust_std)

        # Apply dampening unless forced (e.g. on startup baseline)
        if force:
            self._current_threshold = target_threshold
        else:
            # New = (1-alpha)*Old + alpha*Target
            self._current_threshold = (1 - self.alpha) * self._current_threshold + (
                self.alpha * target_threshold
            )

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
                "alpha": self.alpha,
                "total_updates": self._total_updates,
            }


# Backward compatibility alias
AdaptiveThreshold = AdversarialDriftGuard
