"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window adaptive threshold and Adversarial Drift Guard for anomaly scores.
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
    Robust Median/MAD adaptive threshold guard to mitigate adversarial drift attacks.

    Protects against 'boiling frog' baseline shifting by using robust statistics:
      threshold = median + k * (MAD * 1.4826)
    with MAD floor (0.01) and EMA updates (alpha=0.1) to resist poisoning attempts.
    """

    def __init__(
        self,
        window_size: int = 500,
        k: float = 6.0,
        recalibrate_every: int = 100,
        alpha: float = 0.1,
    ):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every
        self.alpha = alpha

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5
        self._median = 0.5
        self._mad = 0.01
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(
        self,
        scores: float | list[float],
        is_confirmed_benign: bool = False,
        force_recalibrate: bool = False,
    ) -> float:
        """
        Update the buffer with new score(s) and recalibrate threshold if necessary.
        Accepts either a single float score or a list of float scores.
        Returns the updated current_threshold float.
        """
        with self._lock:
            score_list = [scores] if isinstance(scores, (int, float)) else list(scores)
            for s in score_list:
                s_float = float(s)
                if is_confirmed_benign or s_float < self._current_threshold:
                    self._buffer.append(s_float)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if force_recalibrate or (
                self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10
            ):
                self._recalibrate(force=force_recalibrate)

            return self._current_threshold

    def _recalibrate(self, force: bool = False) -> None:
        """Recompute threshold based on Median and MAD statistics."""
        if not self._buffer:
            return
        data = np.array(self._buffer)
        self._median = float(np.median(data))
        self._mad = float(np.median(np.abs(data - self._median)))
        self._mad = max(0.01, self._mad)
        raw_threshold = float(self._median + self.k * (self._mad * 1.4826))

        if force or self._updates_since_recalc == self._total_updates:
            self._current_threshold = raw_threshold
        else:
            self._current_threshold = float(
                self.alpha * raw_threshold + (1 - self.alpha) * self._current_threshold
            )
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
                "median": round(self._median, 4),
                "mad": round(self._mad, 4),
                "total_updates": self._total_updates,
            }
