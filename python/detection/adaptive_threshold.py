"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window adaptive threshold and AdversarialDriftGuard for anomaly scores.
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
    Robust adaptive threshold for SIEM anomaly scores using Median and MAD,
    dampened exponential moving average (EMA) updates, and baseline poison protection.

    Formula:
      median = np.median(buffer)
      mad = max(0.01, np.median(np.abs(buffer - median)))
      raw_threshold = median + k * (mad * 1.4826)   (k=6.0 for v9.0.0-XOCHIMILCO)
    """

    def __init__(
        self,
        window_size: int = 500,
        k: float = 6.0,
        recalibrate_every: int = 100,
        alpha: float = 0.1,
    ):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every
        self.alpha = alpha

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(
        self,
        score: float | list[float],
        is_confirmed_benign: bool = False,
        force_recalibrate: bool = False,
    ) -> float:
        """
        Add single score or list of scores to buffer and return the active threshold.
        """
        scores = [score] if isinstance(score, (int, float)) else list(score)

        with self._lock:
            for s in scores:
                s_val = float(s)
                if is_confirmed_benign or s_val < self._current_threshold:
                    self._buffer.append(s_val)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if force_recalibrate or (
                self._updates_since_recalc >= self.recalibrate_every
                and len(self._buffer) >= 10
            ):
                self._recalibrate(force_direct=force_recalibrate)

            return self._current_threshold

    def _recalibrate(self, force_direct: bool = False) -> None:
        """Recompute threshold using robust statistics (Median & MAD)."""
        if len(self._buffer) < 2:
            return

        data = np.array(self._buffer)
        med = float(np.median(data))
        mad = float(np.median(np.abs(data - med)))
        mad = max(0.01, mad)

        raw_threshold = float(med + self.k * (mad * 1.4826))

        if force_direct or self._total_updates <= self.recalibrate_every:
            self._current_threshold = raw_threshold
        else:
            self._current_threshold = (
                1.0 - self.alpha
            ) * self._current_threshold + self.alpha * raw_threshold

        self._updates_since_recalc = 0

    def is_anomaly(self, score: float) -> bool:
        """Return True if score exceeds adaptive threshold."""
        with self._lock:
            return score > self._current_threshold

    @property
    def current_threshold(self) -> float:
        """Current active threshold."""
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
