"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window and robust adversarial adaptive thresholds for anomaly scores.
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
    [ATLATL-ORDNANCE v9.0.0-XOCHIMILCO] Robust Adversarial Drift Guard.

    Protects against 'boiling frog' baseline shifting and adversarial poisoning
    using Median and Median Absolute Deviation (MAD) with EMA dampening.
    Formula: threshold = median + k * (MAD * 1.4826)
    """

    def __init__(
        self,
        window_size: int = 1000,
        k: float = 5.5,
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
        self._current_threshold = 0.60
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(
        self,
        scores: float | Sequence[float] | np.ndarray,
        is_confirmed_benign: bool = False,
        force_recalibrate: bool = False,
    ) -> float:
        """
        Update drift guard with a single score or a batch of scores.
        Accepts float, list of floats, or numpy array.
        Returns the current active threshold float.
        """
        with self._lock:
            if isinstance(scores, (int, float)):
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

            if force_recalibrate or (
                self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10
            ):
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Recalculate threshold using median and MAD with EMA dampening."""
        if not self._buffer:
            return

        data = np.array(self._buffer)
        median = np.median(data)
        mad = np.median(np.abs(data - median))
        mad = max(float(mad), self.mad_floor)

        target_threshold = median + self.k * (mad * 1.4826)
        # Apply EMA update for smooth transition
        self._current_threshold = float(
            (1.0 - self.alpha) * self._current_threshold + self.alpha * target_threshold
        )
        self._updates_since_recalc = 0

    def is_anomaly(self, score: float) -> bool:
        """Check if anomaly score exceeds threshold."""
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
                "alpha": self.alpha,
                "mad_floor": self.mad_floor,
                "total_updates": self._total_updates,
                "version": "9.0.0-XOCHIMILCO",
            }
