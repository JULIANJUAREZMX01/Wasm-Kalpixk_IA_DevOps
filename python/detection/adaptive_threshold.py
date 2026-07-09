"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Robust adaptive thresholding for anomaly scores.
Uses Median and MAD (Median Absolute Deviation) for outlier-resistant thresholding.
"""

import threading
from collections import deque
from typing import Any

import numpy as np


class AdaptiveThreshold:
    """
    Sliding-window adaptive threshold for anomaly scores (Legacy implementation).

    Algorithm:
      1. Maintains a ring buffer of the last N benign scores (default N=500)
      2. Every `recalibrate_every` new samples, recomputes:
           threshold = mean(buffer) + k * std(buffer)   (default k=3.0)
    """

    def __init__(self, window_size: int = 500, k: float = 3.0, recalibrate_every: int = 50):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(self, score: float, is_confirmed_benign: bool = False) -> None:
        with self._lock:
            if is_confirmed_benign or score < self._current_threshold:
                self._buffer.append(score)
                self._updates_since_recalc += 1
                self._total_updates += 1

                if self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10:
                    self._recalibrate()

    def _recalibrate(self) -> None:
        data = np.array(self._buffer)
        mean = np.mean(data)
        std = np.std(data)
        self._current_threshold = float(mean + self.k * std)
        self._updates_since_recalc = 0

    def is_anomaly(self, score: float) -> bool:
        with self._lock:
            return score > self._current_threshold

    @property
    def current_threshold(self) -> float:
        with self._lock:
            return self._current_threshold

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "current_threshold": round(self._current_threshold, 4),
                "window_size": self.window_size,
                "buffer_len": len(self._buffer),
                "k": self.k,
                "total_updates": self._total_updates,
            }


class AdversarialDriftGuard:
    """
    [ATLATL-ORDNANCE] v9.0.0-XOCHIMILCO Robust Drift Guard.
    Uses Median and MAD (Median Absolute Deviation) to prevent adversarial threshold poisoning.

    Formula:
      threshold = median + k * (MAD * 1.4826)
      where 1.4826 is the scaling factor for normal distribution consistency.
    """

    def __init__(
        self,
        window_size: int = 1000,
        k: float = 5.5,
        recalibrate_every: int = 100,
        alpha: float = 0.1,
    ):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every
        self.alpha = alpha  # Dampening for threshold updates

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.8  # Default v9 hardened threshold
        self._median = 0.5
        self._mad = 0.1

        self._updates_since_recalc = 0
        self._total_updates = 0
        self._initialized = False

    def update(self, scores: float | list[float], force_recalibrate: bool = False) -> float:
        """Add new scores and return the current (possibly updated) threshold."""
        if isinstance(scores, (float, int)):
            scores = [float(scores)]

        with self._lock:
            for s in scores:
                # Only ingest if not a massive outlier to prevent poisoning
                if s < self._current_threshold * 1.5:
                    self._buffer.append(s)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if force_recalibrate or (
                self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 20
            ):
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Robust recalibration using Median/MAD."""
        data = np.array(self._buffer)
        if len(data) < 2:
            return

        new_median = np.median(data)
        new_mad = np.median(np.abs(data - new_median))

        # Consistent estimator for standard deviation
        # MAD * 1.4826 is a robust proxy for STD
        robust_std = max(new_mad, 0.01) * 1.4826
        new_threshold = float(new_median + self.k * robust_std)

        if not self._initialized:
            self._current_threshold = new_threshold
            self._median = new_median
            self._mad = new_mad
            self._initialized = True
        else:
            # Apply dampening to prevent abrupt shifts (Adversarial Resistance)
            self._current_threshold = (1 - self.alpha) * self._current_threshold + self.alpha * new_threshold
            self._median = (1 - self.alpha) * self._median + self.alpha * new_median
            self._mad = (1 - self.alpha) * self._mad + self.alpha * new_mad

        self._updates_since_recalc = 0

    def set_threshold(self, value: float) -> None:
        """Manually set the threshold (used for initial calibration)."""
        with self._lock:
            self._current_threshold = value

    def to_dict(self) -> dict[str, Any]:
        with self._lock:
            return {
                "current_threshold": round(self._current_threshold, 4),
                "median": round(self._median, 4),
                "mad": round(self._mad, 4),
                "window_size": self.window_size,
                "buffer_len": len(self._buffer),
                "k": self.k,
                "total_updates": self._total_updates,
                "initialized": self._initialized,
            }
