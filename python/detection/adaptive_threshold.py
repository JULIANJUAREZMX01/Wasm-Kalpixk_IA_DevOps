"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window adaptive threshold for anomaly scores with adversarial hardening.
"""

import threading
from collections import deque

import numpy as np


class AdversarialDriftGuard:
    """
    Robust adaptive thresholding with protection against adversarial drift.
    Uses Median and Median Absolute Deviation (MAD) instead of Mean/StdDev
    to resist poisoning attacks.

    Features:
      - Robust Statistics: MAD scaled by 1.4826 for normal distribution parity.
      - Update Dampening: Alpha-based smoothing (alpha=0.1) to prevent rapid shifts.
      - Thread-Safe: Atomic updates and recalibration.
      - Batch Support: Efficiently processes batches of scores.
    """

    def __init__(
        self,
        window_size: int = 1000,
        k: float = 3.5,
        recalibrate_every: int = 50,
        alpha: float = 0.1,
    ):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every
        self.alpha = alpha  # Smoothing factor for threshold updates

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5  # Initial baseline
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(self, scores: float | list[float], is_confirmed_benign: bool = False) -> float:
        """
        Add score(s) to buffer and return current threshold.
        Only updates buffer if is_confirmed_benign or score < current_threshold.
        """
        if isinstance(scores, (int, float)):
            scores = [float(scores)]

        with self._lock:
            added_any = False
            for score in scores:
                self._total_updates += 1
                # Only trust scores that are below threshold or confirmed benign
                if is_confirmed_benign or score < self._current_threshold:
                    self._buffer.append(score)
                    self._updates_since_recalc += 1
                    added_any = True

            if (
                added_any
                and self._updates_since_recalc >= self.recalibrate_every
                and len(self._buffer) >= 10
            ):
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """
        Recompute threshold using robust statistics.
        Threshold = Median + k * (1.4826 * MAD)
        """
        # Assumption: called while holding self._lock
        data = np.array(self._buffer)
        if len(data) == 0:
            return

        median = np.median(data)
        mad = np.median(np.abs(data - median))
        robust_std = mad * 1.4826

        target_threshold = float(median + self.k * robust_std)

        # Update dampening (alpha-smoothing) to prevent "boiling frog" poisoning
        self._current_threshold = (
            1 - self.alpha
        ) * self._current_threshold + self.alpha * target_threshold
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
        """Serializable state for telemetry."""
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
