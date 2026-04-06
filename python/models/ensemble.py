"""
Ensemble de detección de anomalías — Kalpixk

Combina Isolation Forest GPU y Autoencoder para detección robusta.
Diseñado para correr en AMD Instinct MI300X con ROCm 7.2.
"""

import logging
from pathlib import Path
from typing import Tuple

import torch
import numpy as np

logger = logging.getLogger("kalpixk.detection.ensemble")

# Directorio de modelos guardados
MODELS_DIR = Path(__file__).parent.parent / "models"


class DetectionEnsemble:
    """
    Ensemble que combina Isolation Forest y Autoencoder.
    
    Pesos del ensemble:
    - IsolationForest: 0.45 (excelente para outliers estructurales)
    - Autoencoder: 0.55 (mejor para anomalías temporales/secuenciales)
    """
    
    VERSION = "0.1.0"
    
    def __init__(self, device: torch.device):
        self.device = device
        self.version = self.VERSION
        
        # Cargar o inicializar modelos
        self.iso_forest = self._load_isolation_forest()
        self.autoencoder = self._load_autoencoder()
        
        logger.info(f"Ensemble inicializado en {device}")
    
    def predict(
        self, 
        features: torch.Tensor
    ) -> Tuple[list[float], list[str], list[float]]:
        """
        Predecir scores de anomalía para un batch de features.
        
        Args:
            features: Tensor [N, 32] de features normalizadas
            
        Returns:
            Tuple de (scores, methods, confidences)
            - scores: lista de floats [0,1] — qué tan anómalo es cada evento
            - methods: método de detección que ganó para cada evento
            - confidences: confianza del modelo en cada predicción
        """
        n = features.shape[0]
        
        # Inference en GPU
        with torch.no_grad():
            features_np = features.cpu().numpy()
            
            # Isolation Forest scores
            if_scores = self._predict_isolation_forest(features_np)
            
            # Autoencoder reconstruction error
            ae_scores = self._predict_autoencoder(features)
        
        # Combinar con pesos del ensemble
        ensemble_scores = 0.45 * if_scores + 0.55 * ae_scores
        
        # Determinar método ganador y confianza
        diffs = np.abs(if_scores - ae_scores)
        confidences = np.maximum(0.5, 1.0 - diffs).tolist()
        if_greater = if_scores > ae_scores
        methods = np.where(if_greater, "isolation_forest", "autoencoder").tolist()
        
        return (
            ensemble_scores.tolist(),
            methods,
            confidences,
        )
    
    def _predict_isolation_forest(self, features_np: np.ndarray) -> np.ndarray:
        """Inferencia con Isolation Forest (cuML en GPU o sklearn en CPU)"""
        try:
            # Intentar cuML (AMD ROCm)
            from cuml.ensemble import IsolationForest as cuIsolationForest
            
            if not hasattr(self, '_cuml_if') or self._cuml_if is None:
                self._cuml_if = cuIsolationForest(
                    n_estimators=100,
                    contamination=0.05,
                    random_state=42,
                )
                logger.info("Usando cuML IsolationForest (AMD GPU)")
            
            # cuML retorna -1 (anomaly) o 1 (normal) — convertir a [0,1]
            raw_scores = self._cuml_if.score_samples(features_np)
            # Normalizar: scores más negativos = más anómalo
            min_s, max_s = raw_scores.min(), raw_scores.max()
            if max_s > min_s:
                normalized = 1.0 - (raw_scores - min_s) / (max_s - min_s)
            else:
                normalized = np.full(len(raw_scores), 0.5)
            return np.array(normalized, dtype=np.float32)
            
        except ImportError:
            # Fallback a scikit-learn en CPU
            from sklearn.ensemble import IsolationForest
            
            if not hasattr(self, '_sklearn_if') or self._sklearn_if is None:
                self._sklearn_if = IsolationForest(
                    n_estimators=100,
                    contamination=0.05,
                    random_state=42,
                )
                # Fit con datos aleatorios si no hay modelo guardado
                dummy = np.random.randn(200, 32).astype(np.float32)
                self._sklearn_if.fit(dummy)
                logger.warning("Usando sklearn IsolationForest (CPU) — entrena el modelo con datos reales")
            
            raw_scores = self._sklearn_if.score_samples(features_np)
            min_s, max_s = raw_scores.min(), raw_scores.max()
            if max_s > min_s:
                normalized = 1.0 - (raw_scores - min_s) / (max_s - min_s)
            else:
                normalized = np.full(len(raw_scores), 0.5)
            return normalized.astype(np.float32)
    
    def _predict_autoencoder(self, features: torch.Tensor) -> np.ndarray:
        """Inferencia con Autoencoder — reconstruction error como anomaly score"""
        if not hasattr(self, '_autoencoder_model') or self._autoencoder_model is None:
            self._autoencoder_model = _build_autoencoder().to(self.device)
            logger.warning("Autoencoder sin entrenar — inicializado con pesos aleatorios")
        
        self._autoencoder_model.eval()
        with torch.no_grad():
            reconstructed = self._autoencoder_model(features.to(self.device))
            # Error de reconstrucción por evento
            errors = torch.mean((features.to(self.device) - reconstructed) ** 2, dim=1)
            
            # Normalizar a [0, 1] usando percentil 99 como máximo
            max_error = torch.quantile(errors, 0.99).item()
            if max_error > 0:
                normalized = torch.clamp(errors / max_error, 0.0, 1.0)
            else:
                normalized = torch.zeros_like(errors)
            
            return normalized.cpu().numpy()
    
    def _load_isolation_forest(self):
        model_path = MODELS_DIR / "isolation_forest.pkl"
        if model_path.exists():
            import pickle
            with open(model_path, "rb") as f:
                logger.info(f"Cargando IsolationForest desde {model_path}")
                return pickle.load(f)
        return None
    
    def _load_autoencoder(self):
        model_path = MODELS_DIR / "autoencoder.pt"
        if model_path.exists():
            model = _build_autoencoder().to(self.device)
            model.load_state_dict(torch.load(model_path, map_location=self.device))
            model.eval()
            logger.info(f"Cargando Autoencoder desde {model_path}")
            return model
        return None


def _build_autoencoder() -> torch.nn.Module:
    """Arquitectura del Autoencoder para detección de anomalías"""
    return torch.nn.Sequential(
        # Encoder: 32 → 16 → 8
        torch.nn.Linear(32, 16),
        torch.nn.ReLU(),
        torch.nn.Dropout(0.1),
        torch.nn.Linear(16, 8),
        torch.nn.ReLU(),
        # Bottleneck (representación latente)
        torch.nn.Linear(8, 4),
        torch.nn.ReLU(),
        # Decoder: 4 → 8 → 16 → 32
        torch.nn.Linear(4, 8),
        torch.nn.ReLU(),
        torch.nn.Linear(8, 16),
        torch.nn.ReLU(),
        torch.nn.Linear(16, 32),
        torch.nn.Sigmoid(),  # Features normalizadas [0,1]
    )
