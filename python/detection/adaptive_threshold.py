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
    Robust adaptive threshold guard resistant to baseline-shifting attacks (e.g. boiling frog).

    Uses Median and Median Absolute Deviation (MAD):
      threshold = median + k * (MAD * 1.4826)
    with EMA dampening on median/MAD updates and a minimum floor for MAD.
    """

    def __init__(
        self,
        window_size: int = 500,
        k: float = 6.0,
        recalibrate_every: int = 100,
        alpha: float = 0.1,
        mad_floor: float = 0.01,
    ):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every
        self.alpha = alpha
        self.mad_floor = mad_floor

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5  # Baseline
        self._updates_since_recalc = 0
        self._total_updates = 0
        self._ema_median: float | None = None
        self._ema_mad: float | None = None

    def update(
        self,
        scores: float | list[float] | np.ndarray,
        is_confirmed_benign: bool = False,
        force_recalibrate: bool = False,
    ) -> float:
        """
        Add score(s) to buffer and return current adaptive threshold.
        Accepts float, list of floats, or numpy array.
        """
        with self._lock:
            if isinstance(scores, (float, int)):
                score_list = [float(scores)]
            elif isinstance(scores, np.ndarray):
                score_list = scores.astype(float).tolist()
            else:
                score_list = [float(s) for s in scores]

            for score in score_list:
                if is_confirmed_benign or score < self._current_threshold:
                    self._buffer.append(score)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            should_recalibrate = (
                force_recalibrate
                or (
                    self._updates_since_recalc >= self.recalibrate_every
                    and len(self._buffer) >= 10
                )
                or (is_confirmed_benign and len(self._buffer) >= 10)
            )

            if should_recalibrate and len(self._buffer) > 0:
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Recompute threshold using median and MAD with EMA dampening."""
        data = np.array(self._buffer)
        med = float(np.median(data))
        mad = float(np.median(np.abs(data - med)))
        mad = max(mad, self.mad_floor)

        if self._ema_median is None:
            self._ema_median = med
            self._ema_mad = mad
        else:
            self._ema_median = (1.0 - self.alpha) * self._ema_median + self.alpha * med
            self._ema_mad = (1.0 - self.alpha) * self._ema_mad + self.alpha * mad

        self._current_threshold = float(self._ema_median + self.k * (self._ema_mad * 1.4826))
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

    @property
    def threshold(self) -> float:
        """Alias for current_threshold."""
        with self._lock:
            return self._current_threshold

    def to_dict(self) -> dict:
        """Serializable state for API endpoints."""
        with self._lock:
            return {
                "current_threshold": round(self._current_threshold, 4),
                "window_size": self.window_size,
                "buffer_len": len(self._buffer),
                "k": self.k,
                "total_updates": self._total_updates,
                "ema_median": round(self._ema_median, 4) if self._ema_median is not None else None,
                "ema_mad": round(self._ema_mad, 4) if self._ema_mad is not None else None,
            }
