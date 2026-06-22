"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
AdversarialDriftGuard — Robust adaptive threshold for anomaly scores.
Protects against 'boiling frog' poisoning attacks via dampened updates.
"""

import threading
from collections import deque
from typing import Union, List

import numpy as np


class AdversarialDriftGuard:
    """
    Sliding-window adaptive threshold for anomaly scores with adversarial protection.

    Features:
      1. Maintains a ring buffer of the last N benign scores.
      2. Dampened updates (alpha factor) to prevent rapid threshold shifts.
      3. Thread-safe (uses threading.Lock).
      4. Batch update support.
    """

    def __init__(
        self,
        window_size: int = 500,
        k: float = 3.5,
        recalibrate_every: int = 50,
        alpha: float = 0.1  # Update dampening factor (0.1 = 10% move towards target)
    ):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every
        self.alpha = alpha

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5  # Initial baseline
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(
        self,
        score: Union[float, List[float]],
        is_confirmed_benign: bool = False
    ) -> float:
        """
        Add score(s) to buffer and return the current threshold.
        Only updates buffer if is_confirmed_benign or score < current_threshold.

        Args:
            score: A single score or list of scores.
            is_confirmed_benign: If True, bypass threshold check for buffer insertion.

        Returns:
            The current threshold value.
        """
        if isinstance(score, (float, int)):
            scores = [float(score)]
        else:
            scores = [float(s) for s in score]

        with self._lock:
            for s in scores:
                if is_confirmed_benign or s < self._current_threshold:
                    self._buffer.append(s)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10:
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Recompute threshold with dampening. Internal use only."""
        # Assumption: called while holding self._lock
        data = np.array(self._buffer)
        if len(data) == 0:
            return

        mean = np.mean(data)
        std = np.std(data)
        target_threshold = float(mean + self.k * std)

        # Security Enhancement: Dampened update to prevent poisoning
        # new = old + alpha * (target - old)
        self._current_threshold = self._current_threshold + self.alpha * (target_threshold - self._current_threshold)
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
