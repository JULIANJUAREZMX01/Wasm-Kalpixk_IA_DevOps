"""
Wasm-Kalpixk — Motor de Detección de Anomalías v2.1
Fixes:
  - StandardScaler serializado con joblib (compatible PyTorch 2.6)
  - Auto-threshold calibrado: mean + 2*std
  - Arquitectura ATLATL: 32→64→16→64→32 (Sincronizada con Alpha Stack)
  - evaluate() para métricas de precision/recall/F1
"""
import os
import torch
import torch.nn as nn
import numpy as np
from loguru import logger
from typing import Optional

try:
    from sklearn.preprocessing import StandardScaler
    import joblib
    SKLEARN_OK = True
except ImportError:
    SKLEARN_OK = False
    logger.warning("sklearn no disponible — normalización desactivada")


class KalpixkAutoencoder(nn.Module):
    """
    Autoencoder para detección de anomalías en métricas WASM.
    Arquitectura ATLATL: 32 → 64 → 16 → 64 → 32
    """
    def __init__(self, input_dim: int = 32, latent_dim: int = 16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, input_dim)
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))

    def reconstruction_error(self, x) -> torch.Tensor:
        with torch.no_grad():
            return nn.MSELoss(reduction="none")(self.forward(x), x).mean(dim=1)


class AnomalyDetector:
    """
    Motor principal de detección de anomalías en runtimes WASM.

    Features (32):
        Sincronizado con kalpixk-core (Rust/WASM) para análisis forense profundo.
    """

    def __init__(self, input_dim: int = 32, latent_dim: int = 16):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = KalpixkAutoencoder(input_dim, latent_dim).to(self.device)
        self.threshold: float = 2.0
        self.is_trained: bool = False
        self.scaler = StandardScaler() if SKLEARN_OK else None
        self.train_stats: dict = {}
        self.input_dim = input_dim

        logger.info(f"AnomalyDetector v2.1 | device={self.device}")
        if self.device.type == "cuda":
            props = torch.cuda.get_device_properties(0)
            logger.info(f"GPU: {props.name} | VRAM: {props.total_memory/1e9:.1f} GB")

    def _normalize(self, X: np.ndarray, fit: bool = False) -> np.ndarray:
        """Normaliza features con StandardScaler."""
        if self.scaler is None:
            return X.astype(np.float32)
        if fit:
            return self.scaler.fit_transform(X).astype(np.float32)
        return self.scaler.transform(X).astype(np.float32)

    def train(self, normal_data: np.ndarray, epochs: int = 100,
              lr: float = 1e-3, auto_threshold_sigma: float = 2.0) -> dict:
        """
        Entrena con datos de operación normal. Auto-calibra el threshold.

        Args:
            normal_data:            array (N, 10) de operación normal
            epochs:                 epochs de entrenamiento
            lr:                     learning rate
            auto_threshold_sigma:   umbral = mean + sigma * std
        Returns:
            dict con stats de entrenamiento
        """
        X_norm = self._normalize(normal_data, fit=True)
        X = torch.FloatTensor(X_norm).to(self.device)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr, weight_decay=1e-5)
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

        # Auto-calibrar threshold
        self.model.eval()
        train_errors = self.model.reconstruction_error(X).cpu().numpy()
        mu, sigma = train_errors.mean(), train_errors.std()
        self.threshold = float(mu + auto_threshold_sigma * sigma)
        self.is_trained = True
        self.train_stats = {
            "epochs": epochs, "final_loss": best_loss,
            "train_error_mean": float(mu), "train_error_std": float(sigma),
            "threshold": self.threshold, "n_samples": len(normal_data),
        }
        logger.success(
            f"Train OK | loss={best_loss:.6f} | "
            f"threshold={self.threshold:.4f} (μ={mu:.4f} + {auto_threshold_sigma}σ={sigma:.4f})"
        )
        return self.train_stats

    def predict(self, metrics: np.ndarray) -> dict:
        """Detecta anomalías. Retorna scores normalizados [0,1] para el dashboard."""
        if not self.is_trained:
            logger.warning("Modelo no entrenado")
        self.model.eval()
        X_norm = self._normalize(metrics, fit=False)
        X = torch.FloatTensor(X_norm).to(self.device)
        errors = self.model.reconstruction_error(X).cpu().numpy()
        anomalies = errors > self.threshold
        scores_normalized = np.clip(errors / max(self.threshold * 3, 1e-8), 0, 1)
        return {
            "reconstruction_errors": errors.tolist(),
            "anomalies": anomalies.tolist(),
            "threshold": self.threshold,
            "scores_normalized": scores_normalized.tolist(),
            "anomaly_count": int(anomalies.sum()),
            "device": str(self.device),
        }

    def evaluate(self, normal: np.ndarray, anomalous: np.ndarray) -> dict:
        """Precision / Recall / F1 con datos etiquetados."""
        rn = self.predict(normal)
        ra = self.predict(anomalous)
        tp = sum(ra["anomalies"])
        tn = sum(not x for x in rn["anomalies"])
        fp = len(rn["anomalies"]) - tn
        fn = len(ra["anomalies"]) - tp
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2*precision*recall / (precision+recall) if (precision+recall) > 0 else 0.0
        return {"precision": precision, "recall": recall, "f1": f1,
                "tp": int(tp), "tn": int(tn), "fp": int(fp), "fn": int(fn)}

    def save(self, path: str = "models/kalpixk_v2.pt"):
        """Guarda modelo y scaler por separado (compatible PyTorch 2.6)."""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        # Guardar solo weights del modelo
        torch.save({
            "model_state": self.model.state_dict(),
            "threshold": self.threshold,
            "train_stats": self.train_stats,
            "input_dim": self.input_dim,
        }, path)
        # Guardar scaler por separado con joblib
        if self.scaler is not None and SKLEARN_OK:
            scaler_path = path.replace(".pt", "_scaler.joblib")
            joblib.dump(self.scaler, scaler_path)
        logger.info(f"Modelo guardado: {path}")

    def load(self, path: str = "models/kalpixk_v2.pt"):
        """Carga modelo y scaler."""
        state = torch.load(path, map_location=self.device, weights_only=True)
        self.model.load_state_dict(state["model_state"])
        self.threshold = state.get("threshold", 2.0)
        self.train_stats = state.get("train_stats", {})
        self.is_trained = True
        # Cargar scaler si existe
        scaler_path = path.replace(".pt", "_scaler.joblib")
        if os.path.exists(scaler_path) and SKLEARN_OK:
            self.scaler = joblib.load(scaler_path)
        logger.info(f"Modelo cargado: {path} | threshold={self.threshold:.4f}")
