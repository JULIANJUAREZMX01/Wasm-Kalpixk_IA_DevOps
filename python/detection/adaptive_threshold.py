"""
python/detection/adaptive_threshold.py
───────────────────────────────────────
Sliding-window adaptive threshold for anomaly scores.
"""
import threading
from collections import deque
import numpy as np

class AdaptiveThreshold:
    def __init__(self, window_size: int = 500, k: float = 3.0, recalibrate_every: int = 50):
        self.window_size, self.k, self.recalibrate_every = window_size, k, recalibrate_every
        self._buffer, self._lock = deque(maxlen=window_size), threading.Lock()
        self._current_threshold, self._updates_since_recalc, self._total_updates = 0.5, 0, 0

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
        with self._lock: return score > self._current_threshold

    @property
    def current_threshold(self) -> float:
        with self._lock: return self._current_threshold

    def to_dict(self) -> dict:
        with self._lock:
            return {"current_threshold": round(self._current_threshold, 4), "window_size": self.window_size, "buffer_len": len(self._buffer), "k": self.k, "total_updates": self._total_updates}

class AdversarialDriftGuard:
    """Advanced adaptive threshold with Z-score protection and dampening."""
    def __init__(self, window_size: int = 1000, z_threshold: float = 3.5, recalibrate_every: int = 50, alpha: float = 0.1):
        self.window_size, self.z_threshold, self.recalibrate_every, self.alpha = window_size, z_threshold, recalibrate_every, alpha
        self._buffer, self._lock = deque(maxlen=window_size), threading.Lock()
        self._current_threshold, self._updates, self._total = 0.95, 0, 0

    def update(self, scores: list[float]) -> float:
        with self._lock:
            benign = [s for s in scores if s < self._current_threshold]
            if benign:
                self._buffer.extend(benign)
                self._updates += len(benign)
                self._total += len(scores)
                if self._updates >= self.recalibrate_every and len(self._buffer) >= 10:
                    data = np.array(self._buffer)
                    new_t = float(np.mean(data) + self.z_threshold * np.std(data))
                    self._current_threshold = (1 - self.alpha) * self._current_threshold + self.alpha * new_t
                    self._updates = 0
            return self._current_threshold

    @property
    def current_threshold(self) -> float:
        with self._lock: return self._current_threshold

    def to_dict(self) -> dict:
        with self._lock:
            return {"current_threshold": round(self._current_threshold, 4), "window_size": self.window_size, "buffer_len": len(self._buffer), "z_threshold": self.z_threshold, "total_updates": self._total}
