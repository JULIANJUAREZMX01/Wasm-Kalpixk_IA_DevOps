"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window adaptive threshold for anomaly scores.
"""

import threading
from collections import deque

import numpy as np


class AdaptiveThreshold:
    """Sliding-window adaptive threshold for anomaly scores."""

    def __init__(self, window_size: int = 500, k: float = 3.0, recalibrate_every: int = 50):
        self.window_size, self.k, self.recalibrate_every = window_size, k, recalibrate_every
        self._buffer, self._lock, self._current_threshold = (
            deque(maxlen=window_size),
            threading.Lock(),
            0.5,
        )
        self._updates_since_recalc = self._total_updates = 0

    def update(self, score: float, is_confirmed_benign: bool = False) -> None:
        with self._lock:
            if is_confirmed_benign or score < self._current_threshold:
                self._buffer.append(score)
                self._updates_since_recalc += 1
                self._total_updates += 1
                if self._updates_since_recalc >= self.recalibrate_every and len(self._buffer) >= 10:
                    self._recalibrate()

    def _recalibrate(self) -> None:
        data = np.array(self._buffer)
        self._current_threshold = float(np.mean(data) + self.k * np.std(data))
        self._updates_since_recalc = 0

    def is_anomaly(self, score: float) -> bool:
        with self._lock:
            return score > self._current_threshold

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
                "total_updates": self._total_updates,
            }


class AdversarialDriftGuard:
    """Hardened version of AdaptiveThreshold that protects against poisoning."""

    def __init__(self, window_size: int = 500, z_threshold: float = 3.5, alpha: float = 0.1):
        self.window_size, self.z_threshold, self.alpha = window_size, z_threshold, alpha
        self._buffer, self._lock, self._current_threshold = (
            deque(maxlen=window_size),
            threading.Lock(),
            0.5,
        )

    def update(self, scores: list[float]) -> float:
        with self._lock:
            if not scores:
                return self._current_threshold
            data = np.array(self._buffer) if len(self._buffer) >= 20 else None
            mean, std = (np.mean(data), np.std(data) or 1e-6) if data is not None else (0.0, 1.0)
            added = 0
            for s in scores:
                if data is None or abs(s - mean) / std < self.z_threshold:
                    self._buffer.append(s)
                    added += 1
            if added > 0 and len(self._buffer) >= 20:
                d = np.array(self._buffer)
                target = float(np.mean(d) + 3.0 * np.std(d))
                self._current_threshold = (
                    (1 - self.alpha) * self._current_threshold + self.alpha * target
                )
            return self._current_threshold

    @property
    def current_threshold(self) -> float:
        with self._lock:
            return self._current_threshold

    def to_dict(self) -> dict:
        with self._lock:
            return {"current_threshold": round(self._current_threshold, 4), "alpha": self.alpha}
