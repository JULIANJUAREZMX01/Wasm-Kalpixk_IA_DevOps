import logging
import numpy as np
import torch
from python.detection.autoencoder import KalpixkAutoencoder
from python.detection.isolation_forest import KalpixkIsolationForest
from python.detection.adaptive_threshold import AdaptiveThreshold

logger = logging.getLogger("kalpixk.models.ensemble")

class DetectionEnsemble:
    def __init__(self, device: torch.device):
        self.device = device
        self.iso_forest = KalpixkIsolationForest(device)
        self.autoencoder = KalpixkAutoencoder(device)
        self.adaptive_threshold = AdaptiveThreshold()
        logger.info(f"Ensemble v7.0-ALPHA inicializado en {device}")

    def predict(self, features: torch.Tensor) -> tuple[list[float], list[str], list[float], float]:
        features_np = features.cpu().numpy()

        # Inferencia
        if_scores, if_conf = self.iso_forest.predict(features_np)
        ae_scores, ae_conf = self.autoencoder.predict(features_np)

        # Combinar: 45% IF + 55% AE
        if_scores_np = np.asarray(if_scores)
        ae_scores_np = np.asarray(ae_scores)
        ensemble_scores = 0.45 * if_scores_np + 0.55 * ae_scores_np

        # Determinar método dominante
        methods = np.where(if_scores_np > ae_scores_np, "isolation_forest", "autoencoder").tolist()

        # Confianza
        confidences = ((np.array(if_conf) + np.array(ae_conf)) / 2).tolist()

        # Actualizar umbral adaptativo
        threshold = self.adaptive_threshold.value
        is_anomalies = [float(s) > threshold for s in ensemble_scores]
        self.adaptive_threshold.recalibrate(ensemble_scores.tolist(), is_anomalies)

        return (
            ensemble_scores.tolist(),
            methods,
            confidences,
            self.adaptive_threshold.value
        )
