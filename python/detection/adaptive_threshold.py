"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window adaptive threshold for anomaly scores.
"""

import threading
from collections import deque

import numpy as np


class AdversarialDriftGuard:
    """
    [ATLATL-ORDNANCE] Adversarial Drift Guard v7
    Protects detection threshold from poisoning and 'boiling frog' attacks.
    Uses Z-score windowing and dampened updates.
    """
    def __init__(self, window_size: int = 100, z_threshold: float = 3.5):
        self.window = deque(maxlen=window_size)
        self.z_threshold = z_threshold
        self.current_threshold = 0.5
        self._lock = threading.Lock()

    def update(self, scores: list[float]) -> float:
        with self._lock:
            for s in scores:
                if len(self.window) > 10:
                    arr = np.array(self.window)
                    mean = np.mean(arr)
                    std = np.std(arr) + 1e-6
                    z = (s - mean) / std
                    # If score is not an outlier, add to window for threshold tracking
                    if abs(z) < self.z_threshold:
                        self.window.append(s)
                else:
                    self.window.append(s)

            if len(self.window) > 10:
                # Target threshold is mean + 2*std of benign window
                arr = np.array(self.window)
                target = np.mean(arr) + 2.0 * np.std(arr)
                # Dampened update to prevent rapid drift
                self.current_threshold = 0.9 * self.current_threshold + 0.1 * target

            return self.current_threshold

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
