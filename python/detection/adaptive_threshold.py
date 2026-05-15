"""
python/detection/adaptive_threshold.py
──────────────────────────────────────
AdversarialDriftGuard — Dynamic threshold recalibration.
Protects against normalization attacks and statistical drift.
"""

import numpy as np
from collections import deque

class AdversarialDriftGuard:
    def __init__(self, window_size: int = 500, sigma: float = 3.0):
        self.window_size = window_size
        self.sigma = sigma
        self.benign_scores = deque(maxlen=window_size)
        self.current_threshold = 0.5

    def update(self, score: float, is_anomaly: bool):
        """Update window with new benign scores to adjust threshold."""
        if not is_anomaly:
            self.benign_scores.append(score)

        if len(self.benign_scores) >= 50:
            mean = np.mean(self.benign_scores)
            std = np.std(self.benign_scores)
            # Re-calculate threshold: mean + 3*sigma
            new_threshold = mean + (self.sigma * std)
            # Clamp to [0.3, 0.9] to avoid extreme drift
            self.current_threshold = np.clip(new_threshold, 0.3, 0.9)

    def get_threshold(self) -> float:
        return self.current_threshold

class AdaptiveThreshold:
    """Wrapper for integration with the detection ensemble."""
    def __init__(self):
        self.guard = AdversarialDriftGuard()

    def recalibrate(self, scores: list[float], is_anomalies: list[bool]):
        for s, a in zip(scores, is_anomalies):
            self.guard.update(s, a)

    @property
    def value(self) -> float:
        return self.guard.get_threshold()
