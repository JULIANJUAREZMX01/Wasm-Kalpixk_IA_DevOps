"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window adaptive threshold with poisoning protection.
"""

import threading
from collections import deque

import numpy as np


class AdversarialDriftGuard:
    """
    Hardened adaptive threshold for anomaly scores.

    Features:
      1. Z-score windowing for noise rejection (default k=3.5).
      2. "Boiling Frog" poisoning protection via alpha-dampening (alpha=0.1).
      3. Thread-safe implementation.
      4. Support for batch updates.
    """

    def __init__(
        self,
        window_size: int = 500,
        k: float = 3.5,
        recalibrate_every: int = 50,
        alpha: float = 0.1
    ):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every
        self.alpha = alpha

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.RLock()  # Re-entrant lock for safe recalibrate calls
        self._current_threshold = 0.5  # Initial baseline
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(self, scores: float | list[float], is_confirmed_benign: bool = False) -> float:
        """
        Add score(s) to buffer and return current threshold.
        Only updates buffer if is_confirmed_benign or score < current_threshold.
        """
        if isinstance(scores, (int, float)):
            scores = [float(scores)]

        with self._lock:
            for score in scores:
                if is_confirmed_benign or score < self._current_threshold:
                    self._buffer.append(score)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10:
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Recompute threshold with dampening to prevent rapid drift."""
        with self._lock:
            data = np.array(self._buffer)
            if len(data) < 2:
                return

            mean = np.mean(data)
            std = np.std(data)

            # Target threshold based on current statistics
            target_threshold = float(mean + self.k * std)

            # Dampened update: new = old + alpha * (target - old)
            # This prevents "boiling frog" attacks from rapidly shifting the threshold.
            self._current_threshold += self.alpha * (target_threshold - self._current_threshold)
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
                "alpha": self.alpha,
                "total_updates": self._total_updates,
            }


# Backward compatibility alias
AdaptiveThreshold = AdversarialDriftGuard
