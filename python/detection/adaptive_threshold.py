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


class AdversarialDriftGuard(AdaptiveThreshold):
    """
    Hardened version of AdaptiveThreshold that protects against 'boiling frog' poisoning.
    It uses a more conservative update policy and Z-score outlier rejection for the buffer itself.
    """
    def __init__(self, window_size: int = 1000, z_threshold: float = 3.5, alpha: float = 0.1):
        super().__init__(window_size=window_size, recalibrate_every=20)
        self.z_threshold = z_threshold
        self.alpha = alpha  # Smoothing factor for threshold updates
        self._current_threshold = 0.7 # Start more conservative

    def update(self, scores: float | list[float]) -> float:
        if isinstance(scores, (float, int)):
            scores = [float(scores)]

        with self._lock:
            for score in scores:
                # Reject extreme outliers from the threshold buffer itself
                if len(self._buffer) > 20:
                    data = np.array(self._buffer)
                    mean = np.mean(data)
                    std = np.std(data)
                    z_score = abs(score - mean) / (std + 1e-9)
                    if z_score > self.z_threshold:
                        continue

                if score < self._current_threshold:
                    self._buffer.append(score)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10:
                self._recalibrate()

        return self._current_threshold

    def _recalibrate(self) -> None:
        data = np.array(self._buffer)
        new_base = float(np.mean(data) + 3.0 * np.std(data))
        # Exponential smoothing to prevent abrupt jumps
        self._current_threshold = (1 - self.alpha) * self._current_threshold + self.alpha * new_base
        self._updates_since_recalc = 0
