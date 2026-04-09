import logging
import numpy as np
from sklearn.ensemble import IsolationForest as SkIsolationForest

logger = logging.getLogger("kalpixk.detection.isolation_forest")

class IsolationForestDetector:
    def __init__(self, contamination=0.05):
        self.model = SkIsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42,
            n_jobs=-1
        )
        # Fit inicial con datos aleatorios (el baseline se entrena luego)
        dummy_data = np.random.randn(100, 32).astype(np.float32)
        self.model.fit(dummy_data)
        self.gpu_active = False

    def predict(self, features_np: np.ndarray) -> np.ndarray:
        """
        Retorna scores en rango [0, 1].
        Valores cercanos a 1 indican alta probabilidad de anomalía.
        """
        # score_samples retorna valores negativos para anomalías
        raw_scores = self.model.score_samples(features_np)

        # Normalización a [0, 1]
        # Invertimos: scores más bajos (anómalos) -> valores más altos
        min_s, max_s = raw_scores.min(), raw_scores.max()
        if max_s > min_s:
            normalized = 1.0 - (raw_scores - min_s) / (max_s - min_s)
        else:
            normalized = np.zeros(len(raw_scores))

        return normalized.astype(np.float32)

    def train(self, X: np.ndarray):
        logger.info(f"Entrenando IsolationForest con {len(X)} muestras")
        self.model.fit(X)
