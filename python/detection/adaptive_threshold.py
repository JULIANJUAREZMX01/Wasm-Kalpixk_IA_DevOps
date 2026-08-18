"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window adaptive threshold and Adversarial Drift Guard for anomaly scores.
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
    Robust adaptive threshold guard against adversarial baseline drift ("boiling frog" attacks).

    Uses Median and Median Absolute Deviation (MAD) instead of mean/std,
    preventing outlier or slowly injected high scores from shifting the baseline upward.

    Formula:
        threshold = median + k * (MAD * 1.4826)
    where 1.4826 normalizes MAD to match standard deviation for normal distributions.
    MAD is constrained by a floor (default 0.01) to prevent hyper-sensitivity.
    Exponential moving average dampening (alpha=0.1) is applied on threshold adjustments.
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
        self._current_threshold = 0.58  # Baseline default for v9.0.0
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(
        self,
        scores: float | Sequence[float],
        is_confirmed_benign: bool = False,
        force_recalibrate: bool = False,
    ) -> float:
        """
        Update buffer with new score(s) and return the current threshold.
        Accepts a single float or a sequence/batch of floats.
        Only stores scores if confirmed benign or below the current threshold.
        """
        if isinstance(scores, (int, float)):
            batch = [float(scores)]
        else:
            batch = [float(s) for s in scores]

        with self._lock:
            for s in batch:
                if is_confirmed_benign or s < self._current_threshold:
                    self._buffer.append(s)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if force_recalibrate or (
                self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10
            ):
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Recompute threshold using robust median and MAD with EMA dampening."""
        if not self._buffer:
            return

        data = np.array(self._buffer)
        med = float(np.median(data))
        abs_dev = np.abs(data - med)
        mad = float(np.median(abs_dev))

        # Scale MAD to match normal std (1.4826 factor) with a safety floor
        scaled_mad = max(self.mad_floor, mad * 1.4826)
        raw_threshold = med + self.k * scaled_mad

        # Exponential Moving Average smooth update to avoid drastic jumps
        self._current_threshold = float(
            (1.0 - self.alpha) * self._current_threshold + self.alpha * raw_threshold
        )
        self._updates_since_recalc = 0

    def is_anomaly(self, score: float) -> bool:
        """Return True if score exceeds current threshold."""
        with self._lock:
            return score > self._current_threshold

    @property
    def current_threshold(self) -> float:
        """Current threshold value."""
        with self._lock:
            return self._current_threshold

    def to_dict(self) -> dict:
        """Serializable state for /status endpoint."""
        with self._lock:
            return {
                "current_threshold": round(self._current_threshold, 4),
                "window_size": self.window_size,
                "buffer_len": len(self._buffer),
                "k": self.k,
                "total_updates": self._total_updates,
            }
