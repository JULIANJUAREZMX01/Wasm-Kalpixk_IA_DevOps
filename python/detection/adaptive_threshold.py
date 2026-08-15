"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window adaptive threshold for anomaly scores.
Includes AdversarialDriftGuard (Median/MAD + EMA) for v9.0.0-XOCHIMILCO.
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

    def update(self, score: float, is_confirmed_benign: bool = False) -> float:
        """
        Add score to buffer.
        Only updates buffer if is_confirmed_benign or score < current_threshold.
        Returns current threshold.
        """
        with self._lock:
            if is_confirmed_benign or score < self._current_threshold:
                self._buffer.append(score)
                self._updates_since_recalc += 1
                self._total_updates += 1

                if self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10:
                    self._recalibrate()
            return float(self._current_threshold)

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
    v9.0.0-XOCHIMILCO Adversarial Drift Guard.
    Uses Median and Median Absolute Deviation (MAD) with Exponential Moving Average (EMA)
    smoothing to prevent baseline shifting ('boiling frog') attacks.
    """

    def __init__(
        self,
        window_size: int = 1000,
        k: float = 5.5,
        alpha: float = 0.1,
        recalibrate_every: int = 100,
        mad_floor: float = 0.01,
    ):
        self.window_size = window_size
        self.k = k
        self.alpha = alpha
        self.recalibrate_every = recalibrate_every
        self.mad_floor = mad_floor

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(
        self,
        scores: float | list[float],
        is_confirmed_benign: bool = False,
        force_recalibrate: bool = False,
    ) -> float:
        """
        Ingests score(s), updates ring buffer, and recalibrates if needed.
        Returns the current threshold.
        """
        if isinstance(scores, (int, float)):
            scores_list = [float(scores)]
        else:
            scores_list = [float(s) for s in scores]

        with self._lock:
            for s in scores_list:
                # Accept scores during warm-up phase or when explicitly benign / force / below threshold
                if (
                    is_confirmed_benign
                    or force_recalibrate
                    or self._total_updates < self.recalibrate_every
                    or s < self._current_threshold
                ):
                    self._buffer.append(s)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if force_recalibrate or (
                self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10
            ):
                self._recalibrate()

            return float(self._current_threshold)

    def _recalibrate(self) -> None:
        """Recompute threshold using robust median + k * (MAD * 1.4826) with EMA dampening."""
        data = np.array(self._buffer)
        med = float(np.median(data))
        abs_dev = np.abs(data - med)
        mad = float(np.median(abs_dev))
        mad_adj = max(mad * 1.4826, self.mad_floor)

        target_threshold = med + self.k * mad_adj

        if self._total_updates <= self.recalibrate_every or self._current_threshold == 0.5:
            self._current_threshold = target_threshold
        else:
            self._current_threshold = (1.0 - self.alpha) * self._current_threshold + self.alpha * target_threshold

        self._updates_since_recalc = 0

    def is_anomaly(self, score: float) -> bool:
        """Return True if score exceeds current adaptive threshold."""
        with self._lock:
            return score > self._current_threshold

    @property
    def current_threshold(self) -> float:
        """Current threshold value."""
        with self._lock:
            return self._current_threshold

    def to_dict(self) -> dict:
        """Serializable state for API status endpoint."""
        with self._lock:
            return {
                "guard_type": "AdversarialDriftGuard_v9_XOCHIMILCO",
                "current_threshold": round(self._current_threshold, 4),
                "window_size": self.window_size,
                "buffer_len": len(self._buffer),
                "k": self.k,
                "alpha": self.alpha,
                "total_updates": self._total_updates,
            }
