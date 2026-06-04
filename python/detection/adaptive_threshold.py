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
    [ATLATL-ORDNANCE] Adversarial Drift Guard.
    Protects the adaptive threshold from 'boiling frog' poisoning attacks
    using Z-score windowing and statistical invariant validation.
    """

    def __init__(self, window_size: int = 1000, z_threshold: float = 3.5, **kwargs):
        super().__init__(window_size=window_size, **kwargs)
        self.z_threshold = z_threshold
        # Start with a more permissive threshold to allow initial baseline establishment
        # in environments where model state on disk might be stale.
        self._current_threshold = 0.8

    def update(self, scores: list[float] | float) -> float:
        """
        Update the guard with new scores.
        Filters out adversarial outliers that attempt to shift the threshold.
        """
        if isinstance(scores, (int, float)):
            scores = [float(scores)]

        with self._lock:
            for score in scores:
                if not (0.0 <= score <= 1.0):
                    continue

                # Validation of statistical invariants
                # Only apply Z-score filtering if we have enough samples for a stable mean/std
                if len(self._buffer) > 50:
                    data = np.array(self._buffer)
                    mean = np.mean(data)
                    std = np.std(data)

                    if std > 1e-4:
                        z_score = abs(score - mean) / std
                        # If the score is a statistical outlier (potential poisoning),
                        # we don't use it to update our 'normal' baseline.
                        if z_score > self.z_threshold:
                            continue

                # Update baseline if score is below current threshold
                # OR if buffer is nearly empty (cold start)
                if score < self._current_threshold or len(self._buffer) < 20:
                    self._buffer.append(score)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

                if self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10:
                    self._recalibrate_with_lock()

            return self._current_threshold

    def _recalibrate_with_lock(self) -> None:
        """Recompute threshold with a more conservative approach. (Assumes lock held)"""
        if len(self._buffer) < 10:
            return
        data = np.array(self._buffer)
        mean = np.mean(data)
        std = np.std(data)

        # Increase k for the guard to reduce false positives in high-variance scenarios
        # Using k=4.0 by default (self.k=3.0 + 1.0)
        self._current_threshold = float(mean + (self.k + 1.0) * std)

        # Ensure threshold doesn't collapse too low during initialization
        # A floor of 0.4 ensures we don't start blocking almost everything
        # unless the model is extremely certain.
        self._current_threshold = max(self._current_threshold, 0.4)
        self._updates_since_recalc = 0
