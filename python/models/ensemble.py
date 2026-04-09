import logging
import numpy as np
import torch
from python.detection.isolation_forest import IsolationForestDetector
from python.detection.autoencoder import AutoencoderDetector

logger = logging.getLogger("kalpixk.models.ensemble")

class DetectionEnsemble:
    def __init__(self, device: torch.device):
        self.device = device
        self.iso_forest = IsolationForestDetector()
        self.autoencoder = AutoencoderDetector(device)
        logger.info(f"Ensemble inicializado en {device}")

    def predict(self, features: torch.Tensor) -> tuple[list[float], list[str], list[float]]:
        features_np = features.cpu().numpy()
        
        # Inferencia
        if_scores = self.iso_forest.predict(features_np)
        ae_scores = self.autoencoder.predict(features)
        
        # Combinar: 45% IF + 55% AE
        ensemble_scores = 0.45 * if_scores + 0.55 * ae_scores
        
        # Determinar método dominante y confianza
        diffs = np.abs(if_scores - ae_scores)
        methods = np.where(if_scores > ae_scores, "isolation_forest", "autoencoder").tolist()
        confidences = np.maximum(0.5, 1.0 - diffs).tolist()
        
        return (
            ensemble_scores.tolist(),
            methods,
            confidences,
        )
