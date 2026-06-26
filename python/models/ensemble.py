import logging

import numpy as np
import torch

from python.detection.adaptive_threshold import AdaptiveThreshold
from python.detection.autoencoder import KalpixkAutoencoder
from python.detection.isolation_forest import KalpixkIsolationForest

logger = logging.getLogger("kalpixk.models.ensemble")


class DetectionEnsemble:
    def __init__(self, device: torch.device):
        self.device = device
        self.iso_forest = KalpixkIsolationForest(device)
        self.autoencoder = KalpixkAutoencoder(device)
        self.drift_guard = AdaptiveThreshold()
        logger.info(f"Ensemble inicializado en {device} with AdaptiveThreshold")

    def predict(self, features: torch.Tensor) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
        features_np = features.cpu().numpy()

        # Inferencia
        if_scores, if_conf, adaptive_threshold = self.iso_forest.predict(features_np)
        ae_scores, ae_conf = self.autoencoder.predict(features_np)

        # Combinar: 45% IF + 55% AE
        ensemble_scores = 0.45 * if_scores + 0.55 * ae_scores

        # Determinar método dominante y confianza
        methods = np.where(if_scores > ae_scores, "isolation_forest", "autoencoder")

        # Confianza basada en el acuerdo entre modelos o el promedio de confianzas
        confidences = (if_conf + ae_conf) / 2.0

        # Update and get adaptive threshold
        for score in ensemble_scores:
            self.drift_guard.update(float(score))
        current_threshold = self.drift_guard.current_threshold

        return (
            ensemble_scores,
            methods,
            confidences,
            current_threshold,
        )
