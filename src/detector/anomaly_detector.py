import os
import torch
import numpy as np
from loguru import logger
from python.models.ensemble import DetectionEnsemble
from python.utils.device import get_rocm_device

class AnomalyDetector:
    def __init__(self, input_dim: int = 32):
        self.device = get_rocm_device()
        self.ensemble = DetectionEnsemble(self.device)
        self.input_dim = input_dim
        self.is_trained = self.ensemble.autoencoder._is_trained or self.ensemble.iso_forest._is_trained
        self.threshold = self.ensemble.autoencoder._threshold
        self.train_stats = {}
        logger.info(f"AnomalyDetector v2.2 (Ensemble) | device={self.device}")

    def train(self, normal_data: np.ndarray, epochs: int = 50, lr: float = 1e-3) -> dict:
        logger.info(f"Training Ensemble with {len(normal_data)} samples")
        self.ensemble.autoencoder.fit(normal_data, epochs=epochs, lr=lr)
        self.ensemble.iso_forest.fit(normal_data)
        self.is_trained = True
        self.threshold = self.ensemble.autoencoder._threshold

        self.train_stats = {
            "ae_threshold": self.threshold,
            "device": str(self.device),
            "status": "trained"
        }

        # Save models after training
        self.ensemble.autoencoder.save()
        self.ensemble.iso_forest.save()

        return self.train_stats

    def predict(self, X: np.ndarray) -> dict:
        # X should be (batch_size, 32)
        X_tensor = torch.tensor(X, dtype=torch.float32).to(self.device)
        scores, methods, confidences = self.ensemble.predict(X_tensor)

        # Threshold at 0.6 for ensemble anomaly
        anomalies = [float(s) > 0.6 for s in scores]

        return {
            "reconstruction_errors": scores,
            "anomalies": anomalies,
            "methods": methods,
            "confidences": confidences,
            "anomaly_count": sum(anomalies)
        }

    def load(self, path=None):
        # Ensemble loads itself on init if files exist
        pass

    def save(self, path=None):
        self.ensemble.autoencoder.save()
        self.ensemble.iso_forest.save()

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        from sklearn.metrics import precision_recall_fscore_support
        res = self.predict(X_test)
        y_pred = np.array(res["anomalies"]).astype(int)

        precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary', zero_division=0)

        return {
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "threshold": 0.6
        }

    def save_evaluation_report(self, metrics: dict, path: str = "models/evaluation_report.json"):
        import json
        with open(path, "w") as f:
            json.dump(metrics, f, indent=4)
