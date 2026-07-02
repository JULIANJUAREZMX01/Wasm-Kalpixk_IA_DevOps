"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
AdversarialDriftGuard: Robust adaptive thresholding for anomaly detection.
Uses Median/MAD robust statistics to resist "slow-burn" poisoning attacks.
"""

import threading
from collections import deque
from typing import List, Union

import numpy as np


class AdversarialDriftGuard:
    """
    Robust adaptive thresholding for anomaly scores.
    Replaces standard Mean/StdDev with Median/Median Absolute Deviation (MAD)
    to provide resilience against adversarial threshold poisoning.
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
        self._median = 0.5
        self._mad = 0.1
        self._initialized = False
        self._updates_since_recalc = 0
        self._total_updates = 0

    def update(self, scores: Union[float, List[float]], is_confirmed_benign: bool = False) -> float:
        """
        Add score(s) to buffer and return current adaptive threshold.
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
                # Process multiple recalibrations if batch size is large
                while self._updates_since_recalc >= self.recalibrate_every:
                    self._recalibrate()
                    self._updates_since_recalc -= self.recalibrate_every

            return self._current_threshold

    def _recalibrate(self, force: bool = False) -> None:
        """
        Recompute threshold using Median/MAD.
        Internal method: assumes self._lock is held.
        """
        if not self._buffer:
            return

        data = np.array(self._buffer)
        new_median = float(np.median(data))
        # MAD scaled by 1.4826 to match std dev of normal distribution
        new_mad = float(np.median(np.abs(data - new_median))) * 1.4826

        # Update statistics with dampening (alpha) to prevent sudden jumps
        # during adversarial "boiling frog" attacks.
        if self._initialized and not force:
            self._median = (1 - self.alpha) * self._median + self.alpha * new_median
            self._mad = (1 - self.alpha) * self._mad + self.alpha * new_mad
        else:
            self._median = new_median
            self._mad = new_mad
            self._initialized = True

        self._current_threshold = float(self._median + self.k * self._mad)

    def set_threshold(self, value: float) -> None:
        """Manually set the threshold (e.g. during calibration)."""
        with self._lock:
            self._current_threshold = value

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
        """Serializable state for telemetry."""
        with self._lock:
            return {
                "current_threshold": round(self._current_threshold, 4),
                "median": round(self._median, 4),
                "mad": round(self._mad, 4),
                "window_size": self.window_size,
                "buffer_len": len(self._buffer),
                "k": self.k,
                "alpha": self.alpha,
                "total_updates": self._total_updates,
            }


# Backward compatibility alias
AdaptiveThreshold = AdversarialDriftGuard
