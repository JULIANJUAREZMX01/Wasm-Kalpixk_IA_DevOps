"""Robust adaptive threshold for anomaly scores using Median/MAD."""
import threading
from collections import deque

import numpy as np


class AdversarialDriftGuard:
    """Resists threshold poisoning via Median/MAD and alpha-dampening."""
    def __init__(self, window_size=1000, k=3.5, recalibrate_every=100, alpha=0.1):
        self.window_size, self.k, self.recalibrate_every, self.alpha = window_size, k, recalibrate_every, alpha
        self._buffer = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._current_threshold = self._median = 0.5
        self._mad, self._updates, self._total, self._initialized = 0.1, 0, 0, False

    def update(self, scores: float | list[float], force_recalibrate: bool = False) -> float:
        if isinstance(scores, (int, float)):
            scores = [float(scores)]
        with self._lock:
            for s in scores:
                self._buffer.append(s)
                self._updates += 1
                self._total += 1
            if force_recalibrate or (self._updates >= self.recalibrate_every and len(self._buffer) >= 20):
                self._recalibrate()
            return self._current_threshold

    def _recalibrate(self):
        data = np.array(self._buffer)
        new_med = float(np.median(data))
        new_mad = max(float(np.median(np.abs(data - new_med))), 0.01)
        if not self._initialized:
            self._median, self._mad, self._initialized = new_med, new_mad, True
        else:
            self._median = (1 - self.alpha) * self._median + self.alpha * new_med
            self._mad = (1 - self.alpha) * self._mad + self.alpha * new_mad
        self._current_threshold = float(self._median + self.k * (self._mad * 1.4826))
        self._updates = 0

    def is_anomaly(self, score: float) -> bool:
        with self._lock:
            return score > self._current_threshold
    def set_threshold(self, value: float):
        with self._lock:
            self._current_threshold = value
    @property
    def current_threshold(self) -> float:
        with self._lock:
            return self._current_threshold
    def to_dict(self) -> dict:
        with self._lock:
            return {
                "current_threshold": round(self._current_threshold, 4),
                "median": round(self._median, 4),
                "mad": round(self._mad, 4),
                "buffer_len": len(self._buffer),
                "total_updates": self._total
            }

AdaptiveThreshold = AdversarialDriftGuard
