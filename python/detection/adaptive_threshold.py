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
    Hardened version of AdaptiveThreshold that protects against 'boiling frog'
    poisoning attacks where an attacker slowly increases scores to shift the threshold.

    Features:
    - Z-score filtering: Ignores scores that are too far (Z > 3.5) from current window.
    - Dampened updates: Threshold shifts are smoothed via alpha (0.1) factor.
    - Batch support: Efficiently handles lists of scores.
    """

    def __init__(self, window_size: int = 500, k: float = 3.5, recalibrate_every: int = 50, alpha: float = 0.1):
        super().__init__(window_size, k, recalibrate_every)
        self.alpha = alpha

    def update(self, scores: float | list[float], is_confirmed_benign: bool = False) -> float:
        """
        Add scores to buffer with adversarial filtering.
        Returns the current threshold.
        """
        if isinstance(scores, (float, int)):
            scores_list = [float(scores)]
        else:
            scores_list = [float(s) for s in scores]

        with self._lock:
            # Optimization: Calculate stats once for the batch if buffer is large enough
            mean = 0.5
            std = 0.1
            has_stats = len(self._buffer) >= 10
            if has_stats:
                data = np.array(self._buffer)
                mean = np.mean(data)
                std = max(np.std(data), 1e-6)

            for score in scores_list:
                # 1. Adversarial filtering: Z-score check
                if has_stats and not is_confirmed_benign:
                    z = abs(score - mean) / std
                    if z > 3.5:
                        # Potentially poisoning or legitimate anomaly, don't drift the threshold
                        continue

                # 2. Standard filtering: Only learn from benign-looking samples
                if is_confirmed_benign or score < self._current_threshold:
                    self._buffer.append(score)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            if self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10:
                self._recalibrate()

            return self._current_threshold

    def _recalibrate(self) -> None:
        """Recompute threshold with dampened update (Alpha stacking)."""
        # Assumption: called while holding self._lock
        data = np.array(self._buffer)
        target_mean = np.mean(data)
        target_std = np.std(data)
        target_threshold = float(target_mean + self.k * target_std)

        # Dampened update: move towards target but don't jump to prevent rapid poisoning
        self._current_threshold = (1 - self.alpha) * self._current_threshold + self.alpha * target_threshold
        self._updates_since_recalc = 0
