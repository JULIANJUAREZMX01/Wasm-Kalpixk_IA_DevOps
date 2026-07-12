"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window adaptive threshold for anomaly scores.
"""

import threading
from collections import deque

import numpy as np


class AdaptiveThreshold:
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
        """Recompute threshold based on buffer statistics. Internal use only."""
        # Assumption: called while holding self._lock
        data = np.array(self._buffer)
        mean = np.mean(data)
        std = np.std(data)
        self._current_threshold = float(mean + self.k * std)
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
    Robust threshold protection using Median and Median Absolute Deviation (MAD).
    Designed to resist slow-poisoning (adversarial drift) attacks.

    Formula: threshold = median + k * (MAD * 1.4826)
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
        self.alpha = alpha  # Dampening factor for recalibration

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._initialized = False

        self._median = 0.5
        self._mad = 0.1
        self._current_threshold = 0.8
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(self, scores: float | list[float], force_recalibrate: bool = False) -> float:
        """Add new score(s) and return the current threshold."""
        if isinstance(scores, (int, float)):
            scores = [float(scores)]

        with self._lock:
            for s in scores:
                # We only add scores that are not extreme outliers to avoid poisoning
                # but we keep a larger window than AdaptiveThreshold.
                if s < self._current_threshold * 1.5:
                    self._buffer.append(s)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if (force_recalibrate or self._updates_since_recalc >= self.recalibrate_every) and len(
                self._buffer
            ) >= 50:
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Recompute median and MAD with dampening."""
        data = np.array(self._buffer)
        new_median = np.median(data)
        new_mad = np.median(np.abs(data - new_median))
        if new_mad < 0.01:
            new_mad = 0.01

        if not self._initialized:
            self._median = new_median
            self._mad = new_mad
            self._initialized = True
        else:
            # Apply dampening (EMA-style) to resist sudden adversarial shifts
            self._median = (1 - self.alpha) * self._median + self.alpha * new_median
            self._mad = (1 - self.alpha) * self._mad + self.alpha * new_mad

        # Robust threshold: median + k * (normalized MAD)
        # 1.4826 is the scaling factor for MAD to match standard deviation
        self._current_threshold = float(self._median + self.k * (self._mad * 1.4826))
        self._updates_since_recalc = 0

    def set_threshold(self, value: float) -> None:
        """Manually override the threshold."""
        with self._lock:
            self._current_threshold = value

    @property
    def current_threshold(self) -> float:
        with self._lock:
            return self._current_threshold

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "median": round(self._median, 4),
                "mad": round(self._mad, 4),
                "current_threshold": round(self._current_threshold, 4),
                "buffer_len": len(self._buffer),
                "total_updates": self._total_updates,
                "version": "9.0.0-XOCHIMILCO-GUARD",
            }
