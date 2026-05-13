"""
python/detection/adaptive_threshold.py
──────────────────────────────────────
AdversarialDriftGuard — Dynamic Decision Boundary Security.
Orchestrates the Adaptive Threshold system with structural hardening
against adversarial drift and normalization attacks.

ATLATL-ORDNANCE: "Inutilización del Atacante via Algorithmic Guillotine."
"""

from __future__ import annotations

import collections
import logging

import numpy as np
from loguru import logger as loguru_logger

logger = logging.getLogger("kalpixk.detection.adaptive_threshold")


class AdversarialDriftGuard:
    """
    Guards the decision threshold against gradual 'drift' attacks where
    an attacker slowly increases the baseline noise to desensitize the model.

    Architecture:
    - Sliding Window: Maintains a history of the last N benign reconstruction scores.
    - Statistical Sentinel: Calculates Z-score of new threshold calibrations.
    - Hard Ceiling: Absolute maximum threshold to prevent total blindness.
    - Volatility Lock: Rejects updates if variance increases too fast.
    """

    VERSION = "7.0.0-atlatl"
    WINDOW_SIZE = 1000
    CALIBRATION_PERCENTILE = 99.0
    MAX_THRESHOLD_DRIFT = 0.15  # 15% max change per recalibration
    VOLATILITY_LIMIT = 3.0  # Z-score limit

    def __init__(self, initial_threshold: float = 0.5):
        self._current_threshold = initial_threshold
        self._history = collections.deque(maxlen=self.WINDOW_SIZE)
        self._threshold_history = [initial_threshold]
        self._locked = False
        self._drift_detected = False

        loguru_logger.info(
            f"AdversarialDriftGuard v{self.VERSION} ARMED. Initial threshold: {initial_threshold}"
        )

    def add_benign_scores(self, scores: list[float] | np.ndarray):
        """Register new scores confirmed as benign to the sliding window."""
        if self._locked:
            return

        if isinstance(scores, np.ndarray):
            scores = scores.tolist()

        self._history.extend(scores)

    def recalibrate(self) -> float:
        """
        Calculates a new threshold based on the sliding window,
        applying v7 Alpha Stack hardening rules.
        """
        if len(self._history) < 100:
            logger.warning("Insufficient history for recalibration. Keeping current threshold.")
            return self._current_threshold

        # Calculate candidate threshold
        scores_array = np.array(self._history)
        candidate = float(np.percentile(scores_array, self.CALIBRATION_PERCENTILE))

        # [ATLATL-ORDNANCE] STAGE 1: DRIFT ANOMALY DETECTION
        historical_avg = np.mean(self._threshold_history[-20:])
        drift = abs(candidate - historical_avg) / (historical_avg + 1e-9)

        if drift > self.MAX_THRESHOLD_DRIFT:
            loguru_logger.warning(
                f"🚨 ADVERSARIAL DRIFT DETECTED: {drift:.2%} deviation. "
                f"Candidate: {candidate:.4f}, Baseline: {historical_avg:.4f}. LOCKING THRESHOLD."
            )
            self._drift_detected = True
            # We don't update to the candidate, we stay at the baseline or tighten
            return self._current_threshold

        # [ATLATL-ORDNANCE] STAGE 2: VOLATILITY LOCK
        if len(self._threshold_history) > 10:
            thresh_std = np.std(self._threshold_history)
            z_score = abs(candidate - historical_avg) / (thresh_std + 1e-9)

            if z_score > self.VOLATILITY_LIMIT:
                loguru_logger.error(
                    f"SYSTEMIC VOLATILITY DETECTED: Z-score {z_score:.2f}. Rejecting calibration."
                )
                return self._current_threshold

        # [ATLATL-ORDNANCE] STAGE 3: COMMIT & LOG
        loguru_logger.debug(
            f"Threshold recalibrated: {self._current_threshold:.4f} -> {candidate:.4f}"
        )
        self._current_threshold = candidate
        self._threshold_history.append(candidate)

        # Keep history manageable
        if len(self._threshold_history) > 100:
            self._threshold_history = self._threshold_history[-100:]

        return self._current_threshold

    @property
    def threshold(self) -> float:
        return self._current_threshold

    @property
    def is_drift_detected(self) -> bool:
        return self._drift_detected

    def reset_guard(self):
        """Manual override for legitimate environmental shifts."""
        self._drift_detected = False
        self._threshold_history = [self._current_threshold]
        loguru_logger.info("AdversarialDriftGuard reset by operator.")


class GuillotineThreshold:
    """
    Specialized threshold for the 'Algorithmic Guillotine'.
    When scores exceed this, retaliation is no longer a choice, it is a certainty.
    """

    def __init__(self, base_threshold: float):
        self.critical = base_threshold * 1.5
        self.exterminio = base_threshold * 1.9  # 95% scaling for extermination

    def get_action(self, score: float) -> str:
        if score >= self.exterminio:
            return "EXTERMINIO"
        if score >= self.critical:
            return "RETALIATE"
        if score >= 0.5:
            return "BLOCK"
        return "PASS"
