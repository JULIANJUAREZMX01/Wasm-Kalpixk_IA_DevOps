"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Adversarial Drift Guard — Robust adaptive threshold for anomaly scores.
Protects against "boiling frog" poisoning attacks using robust statistics.
"""

import threading
from collections import deque
from typing import Union

import numpy as np


class AdversarialDriftGuard:
    """
    Robust adaptive threshold for anomaly scores.

    Algorithm:
      1. Maintains a ring buffer of the last N benign scores (default N=500)
      2. Recomputes threshold using robust statistics (Median / MAD) to prevent
         adversarial poisoning.
      3. Implements update dampening (alpha smoothing) to prevent rapid shifts.
      4. Thread-safe (uses threading.Lock)

    Formulation:
      MAD = Median(|X_i - Median(X)|)
      Target Threshold = Median(X) + k * (1.4826 * MAD)
      Current Threshold = alpha * Target + (1 - alpha) * Current
    """

    def __init__(
        self,
        window_size: int = 500,
        k: float = 3.0,
        recalibrate_every: int = 50,
        alpha: float = 0.1,
    ):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every
        self.alpha = alpha  # Update dampening factor

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5  # Initial baseline
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(self, scores: Union[float, list[float]], is_confirmed_benign: bool = False) -> float:
        """
        Add score(s) to buffer and re-evaluate threshold.
        Only updates buffer if is_confirmed_benign or score < current_threshold.

        Returns the current_threshold after updates.
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
        """Recompute threshold based on robust statistics. Internal use only."""
        # Assumption: called while holding self._lock
        data = np.array(self._buffer)
        if len(data) < 2:
            return

        median = np.median(data)
        mad = np.median(np.abs(data - median))

        # 1.4826 is the scaling factor to make MAD a consistent estimator for StdDev
        robust_std = 1.4826 * mad
        target_threshold = float(median + self.k * robust_std)

        # Apply update dampening (Alpha smoothing)
        # Prevents "Threshold Jumping" attacks
        self._current_threshold = (self.alpha * target_threshold) + ((1 - self.alpha) * self._current_threshold)

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

    def set_threshold(self, value: float) -> None:
        """Manually set the threshold (e.g., after system calibration)."""
        with self._lock:
            self._current_threshold = value

    def to_dict(self) -> dict:
        """Serializable state for /api/status endpoint."""
        with self._lock:
            return {
                "current_threshold": round(self._current_threshold, 4),
                "window_size": self.window_size,
                "buffer_len": len(self._buffer),
                "k": self.k,
                "total_updates": self._total_updates,
                "alpha": self.alpha,
                "robust": True
            }

# Backward compatibility alias
AdaptiveThreshold = AdversarialDriftGuard
