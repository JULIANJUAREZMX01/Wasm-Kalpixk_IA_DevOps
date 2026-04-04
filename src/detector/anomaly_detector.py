"""
Wasm-Kalpixk — Motor de Detección de Anomalías v2
Fixes:
  - StandardScaler integrado (features en escalas distintas)
  - Auto-threshold calibrado en entrenamiento (mean + 2*std)
  - Normalización automática en predict()
  - Métricas de evaluación incluidas
"""
import torch
import torch.nn as nn
import numpy as np
from loguru import logger
from typing import Optional, Tuple

try:
    from sklearn.preprocessing import StandardScaler
    SKLEARN_OK = True
except ImportError:
    SKLEARN_OK = False
    logger.warning("sklearn no disponible — normalización desactivada")


class KalpixkAutoencoder(nn.Module):
    """
    Autoencoder para detección de anomalías en métricas WASM.
    Arquitectura: 10 → 32 → 16 → 4 → 16 → 32 → 10
    (más profundo para mejor representación latente)
    """
    def __init__(self, input_dim: int = 10, latent_dim: int = 4):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32), nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(32, 16), nn.ReLU(),
            nn.Linear(16, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 16), nn.ReLU(),
            nn.Linear(16, 32), nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(32, input_dim)
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))

    def reconstruction_error(self, x) -> torch.Tensor:
        with torch.no_grad():
            return nn.MSELoss(reduction="none")(self.forward(x), x).mean(dim=1)


class AnomalyDetector:
    """
    Motor principal — detecta anomalías en runtimes WASM.
    
    Flujo correcto:
        1. train(normal_data)   ← aprende distribución normal
        2. predict(new_data)    ← compara contra distribución aprendida
    
    Features (10): cpu_usage, memory_mb, exec_time_ms, instructions,
                   memory_pages, function_calls, traps, imports, exports, heap_usage
    """

    def __init__(self, input_dim: int = 10, latent_dim: int = 4):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = KalpixkAutoencoder(input_dim, latent_dim).to(self.device)
        self.threshold: float = 2.0          # auto-calibrado en train()
        self.is_trained: bool = False
        self.scaler = StandardScaler() if SKLEARN_OK else None
        self.train_stats: dict = {}

        logger.info(f"AnomalyDetector v2 | device={self.device}")
        if self.device.type == "cuda":
            props = torch.cuda.get_device_properties(0)
            vram = props.total_memory / 1e9
            logger.info(f"GPU: {props.name} | VRAM: {vram:.1f} GB")

    def _normalize(self, X: np.ndarray, fit: bool = False) -> np.ndarray:
        if self.scaler is None:
            return X.astype(np.float32)
        if fit:
            return self.scaler.fit_transform(X).astype(np.float32)
        return self.scaler.transform(X).astype(np.float32)

    def train(self, normal_data: np.ndarray, epochs: int = 100,
              lr: float = 1e-3, auto_threshold_sigma: float = 2.0):
        """
        Entrena con datos normales. Auto-calibra el threshold.
        
        Args:
            normal_data: array (N, 10) de operación normal
            epochs: epochs de entrenamiento
            lr: learning rate
            auto_threshold_sigma: umbral = mean + sigma*std de errores de train
        """
        X_norm = self._normalize(normal_data, fit=True)
        X = torch.FloatTensor(X_norm).to(self.device)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr,
                                     weight_decay=1e-5)
        scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=50, gamma=0.5)
        criterion = nn.MSELoss()

        self.model.train()
        best_loss = float("inf")
        for epoch in range(epochs):
            optimizer.zero_grad()
            out = self.model(X)
            loss = criterion(out, X)
            loss.backward()
            optimizer.step()
            scheduler.step()

            if loss.item() < best_loss:
                best_loss = loss.item()

            if (epoch + 1) % 25 == 0:
                logger.info(f"Epoch {epoch+1}/{epochs} | loss={loss.item():.6f}")

        # Auto-calibrar threshold con errores de entrenamiento
        self.model.eval()
        train_errors = self.model.reconstruction_error(X).cpu().numpy()
        mu, sigma = train_errors.mean(), train_errors.std()
        self.threshold = float(mu + auto_threshold_sigma * sigma)

        self.is_trained = True
        self.train_stats = {
            "epochs": epochs,
            "final_loss": best_loss,
            "train_error_mean": float(mu),
            "train_error_std": float(sigma),
            "threshold": self.threshold,
            "n_samples": len(normal_data),
        }
        logger.success(
            f"Entrenamiento OK | loss={best_loss:.6f} | "
            f"threshold={self.threshold:.4f} (mu={mu:.4f} + {auto_threshold_sigma}σ={sigma:.4f})"
        )
        return self.train_stats

    def predict(self, metrics: np.ndarray) -> dict:
        """
        Detecta anomalías en nuevas métricas WASM.
        
        Args:
            metrics: array (N, 10) de métricas a evaluar
        Returns:
            dict con reconstruction_errors, anomalies, threshold, scores_normalized
        """
        if not self.is_trained:
            logger.warning("Modelo no entrenado — usando threshold default")

        self.model.eval()
        X_norm = self._normalize(metrics, fit=False)
        X = torch.FloatTensor(X_norm).to(self.device)
        errors = self.model.reconstruction_error(X).cpu().numpy()
        anomalies = errors > self.threshold

        # Score normalizado 0→1 para el dashboard
        scores_normalized = np.clip(errors / (self.threshold * 3), 0, 1)

        return {
            "reconstruction_errors": errors.tolist(),
            "anomalies": anomalies.tolist(),
            "threshold": self.threshold,
            "scores_normalized": scores_normalized.tolist(),
            "anomaly_count": int(anomalies.sum()),
            "device": str(self.device),
        }

    def evaluate(self, normal: np.ndarray, anomalous: np.ndarray) -> dict:
        """Evalúa precisión del detector con datos etiquetados."""
        r_normal = self.predict(normal)
        r_anomal = self.predict(anomalous)
        tp = sum(r_anomal["anomalies"])
        tn = sum(not x for x in r_normal["anomalies"])
        fp = len(r_normal["anomalies"]) - tn
        fn = len(r_anomal["anomalies"]) - tp
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        return {"precision": precision, "recall": recall, "f1": f1,
                "tp": tp, "tn": tn, "fp": fp, "fn": fn}

    def save(self, path: str = "models/kalpixk_v2.pt"):
        import pickle
        state = {
            "model": self.model.state_dict(),
            "threshold": self.threshold,
            "scaler": self.scaler,
            "train_stats": self.train_stats,
        }
        torch.save(state, path)
        logger.info(f"Modelo guardado: {path}")

    def load(self, path: str = "models/kalpixk_v2.pt"):
        state = torch.load(path, map_location=self.device)
        self.model.load_state_dict(state["model"])
        self.threshold = state.get("threshold", 2.0)
        self.scaler = state.get("scaler", self.scaler)
        self.train_stats = state.get("train_stats", {})
        self.is_trained = True
        logger.info(f"Modelo cargado: {path} | threshold={self.threshold:.4f}")
