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
      5. Thread-safe (uses threading.RLock for re-entrancy)
    """

    def __init__(self, window_size: int = 500, k: float = 3.0, recalibrate_every: int = 50):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.RLock()
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
    [ATLATL-ORDNANCE] Adversarial Drift Guard v9.0.0-XOCHIMILCO
    Protects the adaptive threshold from 'boiling frog' poisoning attacks.

    Security Mechanisms:
      1. Z-Score Filtering: Rejects scores > 3.5 std devs from current mean to prevent spikes.
      2. Dampened Updates: Alpha-factor (0.1) smoothing prevents rapid threshold elevation.
      3. Re-entrant Locking: Uses RLock for safe internal recalibration.
    """

    def __init__(
        self,
        window_size: int = 1000,
        k: float = 3.5,
        recalibrate_every: int = 100,
        alpha: float = 0.1,
    ):
        super().__init__(window_size, k, recalibrate_every)
        self.alpha = alpha
        self._target_threshold = 0.5

    def update(self, scores: float | list[float], is_confirmed_benign: bool = False) -> float:
        """
        Processes a batch of scores and returns the current dampened threshold.
        Performance optimized: O(N + M) calculation.
        """
        if isinstance(scores, (int, float)):
            scores = [float(scores)]

        with self._lock:
            # 1. Filter and add to buffer
            for score in scores:
                # Poisoning protection: Only accept if confirmed or within statistical window
                if is_confirmed_benign or not self.is_poisonous(score):
                    self._buffer.append(score)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            # 2. Recalibrate if needed
            if self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10:
                self._recalibrate()

            return self._current_threshold

    def is_poisonous(self, score: float) -> bool:
        """Check if a score represents a poisoning attempt (Z-score > k)."""
        if len(self._buffer) < 20:
            return score > 0.8  # Default high-bar for small buffers

        data = np.array(self._buffer)
        mean = np.mean(data)
        std = np.std(data)
        z_score = (score - mean) / (std + 1e-9)
        return z_score > self.k

    def _recalibrate(self) -> None:
        """Recompute threshold with update dampening (alpha smoothing)."""
        data = np.array(self._buffer)
        mean = np.mean(data)
        std = np.std(data)

        # Calculate new target based on current window
        target = float(mean + self.k * std)

        # Dampen the update: move current threshold only 10% toward target
        # This prevents 'boiling frog' attacks where an attacker slowly raises the threshold
        self._current_threshold = (1 - self.alpha) * self._current_threshold + self.alpha * target
        self._updates_since_recalc = 0
