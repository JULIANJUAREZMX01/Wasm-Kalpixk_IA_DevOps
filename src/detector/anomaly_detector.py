"""
Wasm-Kalpixk — Motor de Detección de Anomalías
Autoencoder sobre AMD MI300X (ROCm) para análisis de runtime WASM
"""
import torch
import torch.nn as nn
import numpy as np
from loguru import logger
from typing import Optional


class KalpixkAutoencoder(nn.Module):
    """
    Autoencoder para detección de anomalías en métricas de runtime WASM.
    Features de entrada (10):
        [cpu_usage, memory_mb, exec_time_ms, instructions, 
         memory_pages, function_calls, traps, imports, exports, heap_usage]
    """
    def __init__(self, input_dim: int = 10, latent_dim: int = 3):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 8),
            nn.ReLU(),
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, input_dim)
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))

    def reconstruction_error(self, x):
        with torch.no_grad():
            reconstructed = self.forward(x)
            return nn.MSELoss(reduction='none')(reconstructed, x).mean(dim=1)


class AnomalyDetector:
    """
    Motor principal de detección. Inicializa en GPU AMD si está disponible.
    """
    def __init__(self, threshold: float = 0.5, input_dim: int = 10):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = KalpixkAutoencoder(input_dim=input_dim).to(self.device)
        self.threshold = threshold
        self.is_trained = False
        logger.info(f"AnomalyDetector iniciado en: {self.device}")
        if self.device.type == "cuda":
            vram = torch.cuda.get_device_properties(0).total_memory / 1e9
            logger.info(f"GPU: {torch.cuda.get_device_name(0)} | VRAM: {vram:.1f} GB")

    def train(self, normal_data: np.ndarray, epochs: int = 100, lr: float = 1e-3):
        """Entrena con datos normales (unsupervised)."""
        X = torch.FloatTensor(normal_data).to(self.device)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.MSELoss()

        self.model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            output = self.model(X)
            loss = criterion(output, X)
            loss.backward()
            optimizer.step()
            if (epoch + 1) % 20 == 0:
                logger.info(f"Epoch {epoch+1}/{epochs} | Loss: {loss.item():.6f}")

        self.is_trained = True
        logger.success(f"Entrenamiento completado. Loss final: {loss.item():.6f}")

    def predict(self, metrics: np.ndarray) -> dict:
        """Detecta anomalías en nuevas métricas WASM."""
        self.model.eval()
        X = torch.FloatTensor(metrics).to(self.device)
        errors = self.model.reconstruction_error(X).cpu().numpy()
        anomalies = errors > self.threshold
        return {
            "reconstruction_errors": errors.tolist(),
            "anomalies": anomalies.tolist(),
            "threshold": self.threshold,
            "anomaly_count": int(anomalies.sum()),
            "device": str(self.device)
        }

    def save(self, path: str = "models/kalpixk_detector.pt"):
        torch.save(self.model.state_dict(), path)
        logger.info(f"Modelo guardado en {path}")

    def load(self, path: str = "models/kalpixk_detector.pt"):
        self.model.load_state_dict(torch.load(path, map_location=self.device))
        self.is_trained = True
        logger.info(f"Modelo cargado desde {path}")
