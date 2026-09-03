"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window adaptive threshold and robust drift guard for anomaly scores.
Protects decision boundaries against baseline poisoning ('boiling frog' attacks).
"""

import threading
from collections import deque
from collections.abc import Sequence

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
    Robust Statistical Sentinel protecting the ensemble detection boundary
    against adversarial baseline poisoning ('boiling frog' attacks).

    Key Protections:
      1. Robust Median and Median Absolute Deviation (MAD) statistics.
      2. Dampened Exponential Moving Average (EMA) threshold updates.
      3. Clamped threshold range [min_threshold, max_threshold].
      4. Thread-safe updates supporting single float or batch score inputs.
    """

    def __init__(
        self,
        window_size: int = 500,
        k: float = 6.0,
        recalibrate_every: int = 100,
        alpha: float = 0.1,
        min_threshold: float = 0.3,
        max_threshold: float = 0.95,
    ):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every
        self.alpha = alpha
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(
        self,
        scores: float | Sequence[float],
        is_confirmed_benign: bool = False,
        force_recalibrate: bool = False,
        force_direct: bool = False,
    ) -> float:
        """
        Process score(s), update the sliding benign buffer, and recompute
        the adaptive threshold when necessary.

        Returns the active threshold value.
        """
        if isinstance(scores, (int, float)):
            score_list = [float(scores)]
        elif isinstance(scores, np.ndarray):
            score_list = scores.astype(float).tolist()
        else:
            score_list = [float(s) for s in scores]

        with self._lock:
            for s in score_list:
                if is_confirmed_benign or s < self._current_threshold:
                    self._buffer.append(s)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if force_recalibrate or (
                self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10
            ):
                self._recalibrate(force_direct=force_direct)

            return self._current_threshold

    def _recalibrate(self, force_direct: bool = False) -> None:
        """Recompute threshold using robust median/MAD statistics."""
        if not self._buffer:
            return

        data = np.array(self._buffer, dtype=np.float32)
        med = float(np.median(data))
        mad = float(np.median(np.abs(data - med)))
        mad = max(mad, 0.01)

        raw_threshold = med + self.k * (mad * 1.4826)
        clamped_threshold = float(
            np.clip(raw_threshold, self.min_threshold, self.max_threshold)
        )

        if force_direct or self._total_updates <= self.recalibrate_every:
            self._current_threshold = clamped_threshold
        else:
            self._current_threshold = (
                1.0 - self.alpha
            ) * self._current_threshold + self.alpha * clamped_threshold

        self._updates_since_recalc = 0

    def is_anomaly(self, score: float) -> bool:
        """Return True if score exceeds active threshold."""
        with self._lock:
            return score > self._current_threshold

    @property
    def current_threshold(self) -> float:
        """Current threshold value."""
        with self._lock:
            return self._current_threshold

    def to_dict(self) -> dict:
        """Serializable status for metrics and health endpoints."""
        with self._lock:
            return {
                "current_threshold": round(self._current_threshold, 4),
                "window_size": self.window_size,
                "buffer_len": len(self._buffer),
                "k": self.k,
                "alpha": self.alpha,
                "total_updates": self._total_updates,
            }
