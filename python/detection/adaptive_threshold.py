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
    Hardened adaptive threshold with Z-score windowing and dampened updates
    to prevent 'boiling frog' poisoning attacks.
    """

    def __init__(
        self,
        window_size: int = 1000,
        z_threshold: float = 3.5,
        alpha: float = 0.1,
        initial_threshold: float = 0.8
    ):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.alpha = alpha  # Dampening factor
        self.current_threshold = initial_threshold
        self.buffer = deque(maxlen=window_size)
        self.lock = threading.Lock()

    def update(self, scores: list[float]) -> float:
        """
        Update threshold using a batch of scores.
        Only scores that pass the Z-score check are added to the buffer.
        """
        with self.lock:
            for score in scores:
                if len(self.buffer) < 50:
                    self.buffer.append(score)
                else:
                    # Z-score protection
                    arr = np.array(self.buffer)
                    mean = np.mean(arr)
                    std = np.std(arr) + 1e-6
                    z = abs(score - mean) / std

                    if z < self.z_threshold:
                        self.buffer.append(score)

            if len(self.buffer) >= 50:
                self._recalibrate()

            return self.current_threshold

    def _recalibrate(self):
        """Internal recalibration. MUST be called with lock held."""
        arr = np.array(self.buffer)
        target_threshold = float(np.mean(arr) + self.z_threshold * np.std(arr))
        # Apply dampening to prevent rapid threshold drift
        self.current_threshold = (1 - self.alpha) * self.current_threshold + self.alpha * target_threshold

    def to_dict(self) -> dict:
        with self.lock:
            return {
                "current_threshold": round(self.current_threshold, 4),
                "buffer_len": len(self.buffer),
                "window_size": self.window_size,
            }
