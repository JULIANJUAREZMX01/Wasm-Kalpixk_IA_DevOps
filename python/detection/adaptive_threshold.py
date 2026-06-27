"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Adversarial Drift Guard for robust adaptive thresholding.
"""

import threading
from collections import deque

import numpy as np


class AdversarialDriftGuard:
    """
    [ATLATL-ORDNANCE] Adversarial Drift Guard v9.0.0
    Protects the detection threshold against adversarial 'boiling frog' poisoning.

    Algorithm:
      1. Maintains a ring buffer of normal scores.
      2. Uses Median and Median Absolute Deviation (MAD) for robust statistics.
      3. Implements update dampening (alpha=0.1) to prevent rapid threshold shifts.
      4. Recalibrates every `recalibrate_every` updates if buffer >= 10.
    """

    def __init__(
        self,
        window_size: int = 500,
        k: float = 3.5,
        recalibrate_every: int = 50,
        alpha: float = 0.1,
    ):
        self.window_size = window_size
        self.k = k
        self.recalibrate_every = recalibrate_every
        self.alpha = alpha  # Update dampening factor

        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = 0.5
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(self, scores: float | list[float], is_confirmed_benign: bool = False) -> float:
        """
        Add new score(s) to buffer and return current threshold.
        If scores is a list, processes them as a batch.
        """
        if isinstance(scores, (int, float)):
            scores = [float(scores)]

        with self._lock:
            for score in scores:
                # Security: Only update buffer with confirmed benign or scores below threshold
                if is_confirmed_benign or score < self._current_threshold:
                    self._buffer.append(score)
                    self._updates_since_recalc += 1
                    self._total_updates += 1

            # Check for recalibration
            while self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10:
                self._recalibrate(force_immediate=is_confirmed_benign)
                self._updates_since_recalc -= self.recalibrate_every

            return self._current_threshold

    def _recalibrate(self, force_immediate: bool = False) -> None:
        """
        Recompute threshold using robust statistics.
        Uses Median and MAD to resist outliers.
        """
        data = np.array(self._buffer)
        if data.size == 0:
            return

        median = np.median(data)
        # MAD = Median of absolute deviations from the median
        mad = np.median(np.abs(data - median))
        # Scale MAD to be consistent with standard deviation (for normal distribution)
        robust_std = mad * 1.4826

        target_threshold = float(median + self.k * robust_std)

        if force_immediate:
            self._current_threshold = target_threshold
        else:
            # Dampened update: New = Old + alpha * (Target - Old)
            self._current_threshold += self.alpha * (target_threshold - self._current_threshold)

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
                "alpha": self.alpha,
                "method": "MAD_ROBUST_V9",
            }


# Backward compatibility alias
AdaptiveThreshold = AdversarialDriftGuard
