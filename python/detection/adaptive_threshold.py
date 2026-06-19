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
    Hardened version of AdaptiveThreshold to prevent 'Boiling Frog' attacks.
    Uses Z-score outlier removal and dampening to ensure threshold stability.
    """

    def __init__(
        self,
        window_size: int = 500,
        k: float = 3.5,
        recalibrate_every: int = 50,
        alpha: float = 0.1
    ):
        super().__init__(window_size, k, recalibrate_every)
        self.alpha = alpha  # Dampening factor

    def update(self, scores: float | list[float]) -> float:
        """
        Batch update support and adversarial filtering.
        Returns the current threshold.
        """
        if isinstance(scores, (float, int, np.float32)):
            scores = [float(scores)]

        with self._lock:
            for score in scores:
                # Adversarial filtering: only update with benign-looking samples
                # to prevent rapid threshold poisoning.
                if score < self._current_threshold:
                    self._buffer.append(float(score))
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10:
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Robust recalibration with dampening and Z-score filtering."""
        # Assumption: called while holding self._lock
        data = np.array(self._buffer)
        if len(data) == 0:
            self._current_threshold = 0.5
            return

        # Filter out potential poisoning samples in the buffer using a strict Z-score
        mean_raw = np.mean(data)
        std_raw = np.std(data)

        if std_raw > 1e-6:
            z_scores = np.abs((data - mean_raw) / std_raw)
            clean_data = data[z_scores < 3.5]
            if len(clean_data) >= 5:
                data = clean_data

        target_mean = np.mean(data)
        target_std = np.std(data)
        target_threshold = float(target_mean + self.k * target_std)

        # Dampening: prevents rapid shifts in threshold (Boiling Frog protection)
        # New Threshold = Old + Alpha * (Target - Old)
        self._current_threshold = (
            self._current_threshold + self.alpha * (target_threshold - self._current_threshold)
        )

        # Ensure threshold stays within valid bounds [0.01, 0.99]
        self._current_threshold = max(0.01, min(0.99, self._current_threshold))

        if np.isnan(self._current_threshold):
            self._current_threshold = 0.5

        self._updates_since_recalc = 0
