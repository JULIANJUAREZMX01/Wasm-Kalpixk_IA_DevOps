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
    Protects the anomaly detection threshold from 'boiling frog' poisoning attacks.
    Uses Z-score windowing to filter out outliers from the baseline and dampened
    updates (exponential smoothing) to ensure stability.
    """

    def __init__(self, window_size: int = 500, alpha: float = 0.1, z_threshold: float = 3.5):
        self.window_size = window_size
        self.alpha = alpha  # Smoothing factor for threshold updates
        self.z_threshold = z_threshold
        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.8  # Conservative initial threshold
        self._total_updates = 0

    def update(self, scores: list[float]) -> float:
        """
        Update the guard with new scores and return the current dampened threshold.
        Filters out scores that are statistically likely to be malicious poisoning.
        """
        with self._lock:
            for score in scores:
                if len(self._buffer) < 50:
                    # Warm-up phase: accept samples to build baseline
                    if score < 0.9:
                        self._buffer.append(score)
                else:
                    # Z-score outlier detection
                    data = np.array(self._buffer)
                    mean = np.mean(data)
                    std = np.std(data) + 1e-6
                    z_score = (score - mean) / std

                    # Only add to buffer if it's not an extreme outlier
                    if z_score < self.z_threshold:
                        self._buffer.append(score)

                self._total_updates += 1

            if len(self._buffer) >= 50:
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self):
        """
        Recalculates the internal threshold target and applies dampening.
        Assumes self._lock is held.
        """
        data = np.array(self._buffer)
        # Target: mean + 3 sigma
        new_target = float(np.mean(data) + 3.0 * np.std(data))

        # Apply alpha dampening (exponential moving average)
        # current = current * (1 - alpha) + target * alpha
        self._current_threshold = (1.0 - self.alpha) * self._current_threshold + self.alpha * new_target

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
                "alpha": self.alpha,
                "total_updates": self._total_updates,
            }
