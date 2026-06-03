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
    [ATLATL-ORDNANCE] AdversarialDriftGuard v9
    Protects the detection threshold using Z-score windows and statistical invariant validation.
    Prevents 'boiling frog' attacks by enforcing strict boundaries on threshold drift.
    """

    def __init__(self, window_size: int = 1000, z_threshold: float = 3.5):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.65  # Default hardened threshold
        self._min_threshold = 0.4
        self._max_threshold = 0.85

    def update(self, scores: list[float]) -> float:
        """
        Update baseline with new scores and return the current adaptive threshold.
        Filters out outliers during baseline update to prevent poisoning.
        """
        with self._lock:
            for s in scores:
                # Statistical Invariant: scores must be in [0, 1]
                s = max(0.0, min(1.0, float(s)))

                # Poisoning Protection: Only update baseline with 'normal' scores
                if s < self._current_threshold:
                    self._buffer.append(s)

            if len(self._buffer) >= 100:
                data = np.array(self._buffer)
                mean = np.mean(data)
                std = np.std(data)

                # Z-score based adaptive threshold
                target_threshold = mean + self.z_threshold * std

                # Dampened Update: prevent sudden adversarial threshold shifts
                self._current_threshold = 0.95 * self._current_threshold + 0.05 * target_threshold

            # Hard Boundary Guard: prevent threshold from being pushed to extremes
            self._current_threshold = max(
                self._min_threshold, min(self._max_threshold, self._current_threshold)
            )

            return float(self._current_threshold)

    def validate_and_update(self, scores: list[float]) -> float:
        """Alias for update() for compatibility with ensemble logic."""
        return self.update(scores)
