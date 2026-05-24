import numpy as np
from loguru import logger


class AdversarialDriftGuard:
    """
    [ATLATL-ORDNANCE] Adversarial Drift Guard v7.0
    Protects detection thresholds against normalization attacks using Z-score windowing
    and statistical invariants.
    """
    def __init__(self, window_size: int = 500, z_threshold: float = 3.0):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.score_history = []
        self.current_threshold = 0.3 # Aggressive default for Guerrilla Mode
        logger.info(f"🛡️ AdversarialDriftGuard v8.0 initialized (window={window_size})")

    def update(self, scores: list[float]) -> float:
        """Updates the adaptive threshold based on a sliding window of benign scores."""
        for s in scores:
            # Only add scores that are not extreme outliers to the benign baseline
            if s < 0.9:
                self.score_history.append(s)

        if len(self.score_history) > self.window_size:
            self.score_history = self.score_history[-self.window_size:]

        if len(self.score_history) < 100:
            return self.current_threshold

        # Recalibrate based on mean and std
        mean_score = np.mean(self.score_history)
        std_score = np.std(self.score_history)

        # Guard against zero variance
        if std_score < 1e-6:
            std_score = 0.1

        # Adaptive threshold: mean + 3.0 * std
        new_threshold = float(mean_score + self.z_threshold * std_score)
        self.current_threshold = np.clip(new_threshold, 0.3, 0.95)

        return self.current_threshold

    def validate_batch(self, features: np.ndarray) -> bool:
        """
        [ATLATL-ORDNANCE] Bit-level statistical invariant validation.
        Detects if features have been manipulated to cause drift.
        """
        # Statistical Invariant: Features should not have near-zero variance in an active system
        feat_std = np.std(features, axis=0)
        if np.any(feat_std < 1e-9):
             logger.warning("☣️  Potential normalization attack detected (near-zero feature variance).")
             return False

        # Max-Abs scaling invariant: normalized features should be within [0, 1]
        if np.any(features < -0.1) or np.any(features > 1.1):
             logger.warning("☣️  Out-of-bounds feature detected (adversarial injection).")
             return False

        return True
