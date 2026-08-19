"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window adaptive threshold and robust adversarial drift guard for anomaly scores.
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
    Robust adaptive threshold for anomaly scores based on Median and Median Absolute Deviation (MAD).

    Formula:
      threshold = median + k * (MAD * 1.4826)

    Key Features:
      - Robust against outlier contamination ("boiling frog" attacks / baseline shifting).
      - Accepts single float or list/array of float scores in `update()`.
      - Implements EMA dampening for smooth threshold transitions.
      - Enforces a MAD floor of 0.01 to avoid collapse with constant scores.
      - Thread-safe.
    """

    def __init__(
        self,
        window_size: int = 500,
        k: float = 6.0,
        recalibrate_every: int = 100,
        mad_floor: float = 0.01,
        alpha: float = 0.1,
    ):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every
        self.mad_floor = mad_floor
        self.alpha = alpha

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5
        self._median = 0.5
        self._mad = mad_floor
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(
        self,
        scores: float | list[float] | np.ndarray,
        is_confirmed_benign: bool = False,
        force_recalibrate: bool = False,
    ) -> float:
        """
        Add score(s) to buffer and return current threshold value.
        Accepts single float or list/array of float scores.
        """
        if isinstance(scores, (float, int)):
            score_list = [float(scores)]
        elif isinstance(scores, np.ndarray):
            score_list = [float(s) for s in scores.flat]
        else:
            score_list = [float(s) for s in scores]

        with self._lock:
            for score in score_list:
                if is_confirmed_benign or score < self._current_threshold or len(self._buffer) < 10:
                    self._buffer.append(score)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if force_recalibrate or (
                self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10
            ):
                self._recalibrate()

            return float(self._current_threshold)

    def _recalibrate(self) -> None:
        """Recompute threshold based on robust statistics (Median & MAD). Internal use only."""
        data = np.array(self._buffer, dtype=np.float64)
        median = float(np.median(data))
        raw_mad = float(np.median(np.abs(data - median)))
        mad = max(raw_mad, self.mad_floor)

        target_threshold = float(median + self.k * (mad * 1.4826))

        if self._total_updates > len(self._buffer):
            self._current_threshold = float((1.0 - self.alpha) * self._current_threshold + self.alpha * target_threshold)
        else:
            self._current_threshold = target_threshold

        self._median = median
        self._mad = mad
        self._updates_since_recalc = 0

    def is_anomaly(self, score: float) -> bool:
        """Return True if score exceeds adaptive threshold."""
        with self._lock:
            return float(score) > self._current_threshold

    @property
    def current_threshold(self) -> float:
        """Current threshold value."""
        with self._lock:
            return float(self._current_threshold)

    def to_dict(self) -> dict:
        """Serializable state for /status endpoint."""
        with self._lock:
            return {
                "current_threshold": round(float(self._current_threshold), 4),
                "median": round(float(self._median), 4),
                "mad": round(float(self._mad), 4),
                "window_size": self.window_size,
                "buffer_len": len(self._buffer),
                "k": self.k,
                "total_updates": self._total_updates,
            }
