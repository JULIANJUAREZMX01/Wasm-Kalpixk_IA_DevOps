"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
[ATLATL-ORDNANCE] Adversarial Drift Guard — Robust Adaptive Thresholding.
Resists 'boiling frog' poisoning attacks using Median/MAD statistics.
"""

import threading
from collections import deque
from typing import Any

import numpy as np


class AdversarialDriftGuard:
    """
    Robust adaptive thresholding for anomaly scores.

    Algorithm:
      1. Maintains a ring buffer of benign scores.
      2. Uses Median and Median Absolute Deviation (MAD) for robust statistics.
      3. Implements update dampening (alpha) to prevent rapid threshold shifts.
      4. Protects against adversarial 'slow-burn' poisoning.
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
        self.alpha = alpha  # Update dampening factor

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5  # Initial baseline
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(
        self, scores: float | list[float], is_confirmed_benign: bool = False, force_recalibrate: bool = False
    ) -> float:
        """
        Add score(s) to buffer and re-evaluate threshold.
        Returns the updated threshold.
        """
        if isinstance(scores, (int, float)):
            scores = [float(scores)]

        with self._lock:
            for score in scores:
                # Security logic: only include in baseline if confirmed benign
                # or if it's below the current threshold (self-reinforcing benign).
                if is_confirmed_benign or score < self._current_threshold:
                    self._buffer.append(score)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if (force_recalibrate or self._updates_since_recalc >= self.recalibrate_every) and len(
                self._buffer
            ) >= 10:
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """
        Recompute threshold using robust statistics.
        Uses Median and MAD (Median Absolute Deviation) which are more
        resistant to outliers than Mean/StdDev.
        """
        data = np.array(self._buffer)
        if len(data) < 2:
            return

        median = np.median(data)
        # MAD = median(|x_i - median|)
        # 1.4826 scale factor makes MAD consistent with standard deviation for normal distribution
        mad = np.median(np.abs(data - median)) * 1.4826

        target_threshold = float(median + self.k * mad)

        # Dampen the update to prevent rapid adversarial shifts (alpha-smoothing)
        self._current_threshold = (1 - self.alpha) * self._current_threshold + self.alpha * target_threshold
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

    def set_threshold(self, value: float) -> None:
        """Manually set the threshold (e.g. during calibration)."""
        with self._lock:
            self._current_threshold = float(value)

    def to_dict(self) -> dict[str, Any]:
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
