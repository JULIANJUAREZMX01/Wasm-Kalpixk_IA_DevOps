"""
KalpixkIsolationForest — GPU-accelerated anomaly detection
Wraps cuML IsolationForest (AMD ROCm) with CPU fallback (sklearn).
"""
import logging
from pathlib import Path

import numpy as np
import torch

logger = logging.getLogger("kalpixk.detection.isolation_forest")
MODELS_DIR = Path(__file__).parent.parent / "models"

class KalpixkIsolationForest:
    VERSION = "0.1.0"
    N_ESTIMATORS = 200
    CONTAMINATION = 0.05  # Expected anomaly rate
    MAX_SAMPLES = "auto"

    def __init__(self, device: torch.device):
        self.device = device
        self._model = None
        self._is_trained = False
        self._load_or_init()

    def _load_or_init(self):
        model_path = MODELS_DIR / "isolation_forest.pkl"
        if model_path.exists():
            import joblib
            try:
                self._model = joblib.load(model_path)
                self._is_trained = True
                logger.info(f"Modelo cargado desde {model_path}")
                return
            except Exception as e:
                logger.error(f"Error cargando modelo: {e}")

        # Initialize untrained model
        if str(self.device) != "cpu":
            try:
                from cuml.ensemble import IsolationForest as cuIsolationForest
                self._model = cuIsolationForest(
                    n_estimators=self.N_ESTIMATORS,
                    contamination=self.CONTAMINATION,
                    max_samples=self.MAX_SAMPLES,
                    random_state=42,
                )
                logger.info("Inicializado cuML IsolationForest (GPU)")
            except ImportError:
                logger.warning("cuML no disponible, usando fallback sklearn")

        if self._model is None:
            from sklearn.ensemble import IsolationForest
            self._model = IsolationForest(
                n_estimators=self.N_ESTIMATORS,
                contamination=self.CONTAMINATION,
                max_samples=self.MAX_SAMPLES,
                random_state=42,
                n_jobs=-1,
            )
            # Dummy fit if totally new
            dummy = np.random.randn(100, 32).astype(np.float32)
            self._model.fit(dummy)
            logger.info("Inicializado sklearn IsolationForest (CPU)")

    def fit(self, X: np.ndarray) -> "KalpixkIsolationForest":
        logger.info(f"Entrenando IsolationForest con {len(X)} muestras")
        self._model.fit(X)
        self._is_trained = True
        return self

    def predict(self, X: np.ndarray) -> tuple[list[float], list[float]]:
        if not self._is_trained:
            n = X.shape[0]
            return [0.3] * n, [0.5] * n

        raw_scores = self._model.score_samples(X)
        # Normalize to [0, 1]: more negative = more anomalous
        min_s, max_s = raw_scores.min(), raw_scores.max()
        if max_s == min_s:
            normalized = np.full(len(raw_scores), 0.3)
        else:
            normalized = 1.0 - (raw_scores - min_s) / (max_s - min_s)

        confidences = np.clip(np.abs(raw_scores) / 0.5, 0.0, 1.0)
        return normalized.tolist(), confidences.tolist()

    def save(self):
        MODELS_DIR.mkdir(exist_ok=True)
        import joblib
        joblib.dump(self._model, MODELS_DIR / "isolation_forest.pkl")
        logger.info(f"Modelo guardado en {MODELS_DIR / 'isolation_forest.pkl'}")
