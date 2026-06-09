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
    Hardened adaptive threshold with protection against 'boiling frog' poisoning.

    Features:
      - Z-score filtering: Ignores suspicious scores that would bias the mean.
      - Dampened updates: New threshold is a moving average (alpha=0.1).
      - Optimized batch updates.
    """

    def __init__(
        self,
        window_size: int = 1000,
        z_threshold: float = 3.5,
        alpha: float = 0.1,
        initial_threshold: float = 0.95
    ):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.alpha = alpha  # Smoothing factor for threshold updates

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = initial_threshold
        self._total_updates = 0

    def update(self, scores: float | list[float]) -> float:
        """
        Add new scores and return the current (possibly updated) threshold.
        Uses Z-score filtering to prevent adversarial poisoning of the baseline.
        """
        if isinstance(scores, (int, float)):
            scores = [float(scores)]

        with self._lock:
            if not self._buffer:
                # Seed buffer if empty
                self._buffer.extend(scores)
                self._total_updates += len(scores)
                self._recalibrate()
                return self._current_threshold

            # Optimization: Calculate stats once per batch
            data = np.array(self._buffer)
            mean = np.mean(data)
            std = np.std(data) + 1e-9

            valid_scores = []
            for s in scores:
                z = abs(s - mean) / std
                # Only accept scores that aren't extreme outliers (potential poisoning)
                if z < self.z_threshold:
                    valid_scores.append(s)

            if valid_scores:
                self._buffer.extend(valid_scores)
                self._total_updates += len(valid_scores)
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Recompute threshold with dampening. Assumption: lock is held."""
        if len(self._buffer) < 10:
            return

        data = np.array(self._buffer)
        # Use a high percentile for the raw threshold (e.g. 99th)
        raw_target = float(np.percentile(data, 99))

        # Dampened update: T_new = (1-alpha)*T_old + alpha*T_target
        # This prevents the threshold from jumping too quickly
        self._current_threshold = (1 - self.alpha) * self._current_threshold + self.alpha * raw_target

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
                "total_updates": self._total_updates,
                "z_threshold": self.z_threshold
            }
