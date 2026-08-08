"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window adaptive threshold for anomaly scores.
Includes legacy AdaptiveThreshold and robust AdversarialDriftGuard.
"""

import threading
from collections import deque

import numpy as np


class AdaptiveThreshold:
    """
    Sliding-window adaptive threshold for anomaly scores.
    Original simple implementation using Mean and Standard Deviation.
    Tested in test_adaptive_threshold.py.
    """

    def __init__(self, window_size: int = 500, k: float = 3.0, recalibrate_every: int = 50, alpha: float = 0.2):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every
        self.alpha = alpha  # Smoothing factor for dampened updates (v9 hardening)

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
        """Recompute threshold based on buffer statistics. Internal use only."""
        # Assumption: called while holding self._lock
        data = np.array(self._buffer)
        mean = np.mean(data)
        std = np.std(data)
        new_threshold = float(mean + self.k * std)

        # Dampened update
        self._current_threshold = (1.0 - self.alpha) * self._current_threshold + self.alpha * new_threshold

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


class AdversarialDriftGuard:
    """
    AdversarialDriftGuard — Robust adaptive thresholding for ensemble scores.
    Uses Median and MAD (Median Absolute Deviation) to resist outlier influence.
    Optimized for version 9.0.0-XOCHIMILCO.
    """

    def __init__(self, window_size: int = 1000, k: float = 5.5, recalibrate_every: int = 100, alpha: float = 0.1):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every
        self.alpha = alpha

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5
        self._updates_since_recalc = 0
        self._total_updates = 0
        self._initialized = False
        self._median = 0.5
        self._mad = 0.1

    def update(
        self,
        scores: float | list[float],
        is_confirmed_benign: bool = False,
        force_recalibrate: bool = False,
    ) -> float:
        """Add score(s) to buffer and return current threshold."""
        with self._lock:
            # Handle single float or list of floats
            score_list = scores if isinstance(scores, list) else [scores]

            for s in score_list:
                if is_confirmed_benign or s < self._current_threshold or not self._initialized:
                    self._buffer.append(float(s))
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if force_recalibrate or (
                self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10
            ):
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Recompute threshold based on robust statistics (median/MAD) and dampened EMA."""
        data = np.array(self._buffer)
        if len(data) < 5:
            return

        new_median = np.median(data)
        new_mad = np.median(np.abs(data - new_median))

        if new_mad < 0.01:
            new_mad = 0.01

        if not self._initialized:
            # Direct calibration bypasses dampening for the initial baseline
            self._median = new_median
            self._mad = new_mad
            self._initialized = True
        else:
            # Dampened EMA updates
            self._median = (1.0 - self.alpha) * self._median + self.alpha * new_median
            self._mad = (1.0 - self.alpha) * self._mad + self.alpha * new_mad

        self._current_threshold = float(self._median + self.k * (self._mad * 1.4826))
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
        """Set threshold directly."""
        with self._lock:
            self._current_threshold = value

    def to_dict(self) -> dict:
        """Serializable state for status and telemetry."""
        with self._lock:
            return {
                "current_threshold": round(self._current_threshold, 4),
                "window_size": self.window_size,
                "median": round(self._median, 4),
                "mad": round(self._mad, 4),
                "buffer_len": len(self._buffer),
                "k": self.k,
                "total_updates": self._total_updates,
            }
