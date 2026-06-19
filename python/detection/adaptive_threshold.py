"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window adaptive threshold for anomaly scores.
"""

import threading
from collections import deque
from typing import List, Union

import numpy as np


class AdversarialDriftGuard:
    """
    [SEC-V9] Defensive adaptive threshold guard.
    Implements update dampening (alpha-factor) and Z-score windowing
    to protect against 'boiling frog' poisoning attacks.
    """

    def __init__(
        self,
        window_size: int = 500,
        z_score: float = 3.5,
        recalibrate_every: int = 50,
        alpha: float = 0.1,  # Dampening factor
    ):
        self.window_size = window_size
        self.z_score = z_score
        self.recalibrate_every = recalibrate_every
        self.alpha = alpha

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(self, scores: Union[float, List[float]]) -> float:
        """
        Add new scores to the buffer and return current threshold.
        Applies update dampening to the threshold during recalibration.
        """
        if isinstance(scores, float):
            scores = [scores]

        with self._lock:
            for score in scores:
                # Security: Only ingest scores that are 'normal' or slightly above
                # to prevent rapid poisoning of the baseline.
                if score < self._current_threshold * 1.5:
                    self._buffer.append(score)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if (
                self._updates_since_recalc >= self.recalibrate_every
                and len(self._buffer) >= 10
            ):
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Internal recalibration with dampened updates."""
        data = np.array(self._buffer)
        if len(data) == 0:
            return

        mean = np.mean(data)
        std = np.std(data)

        target_threshold = float(mean + self.z_score * std)

        # SECURITY: Dampened update (EMA) to prevent sudden threshold jumps
        # that could be used to blind the detector.
        self._current_threshold = (
            (1 - self.alpha) * self._current_threshold + self.alpha * target_threshold
        )
        self._updates_since_recalc = 0

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
