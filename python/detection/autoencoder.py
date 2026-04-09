"""
KalpixkAutoencoder — PyTorch anomaly detection via reconstruction error.
Runs on AMD MI300X via ROCm.
Architecture: 32 → 16 → 8 → 4 → 8 → 16 → 32 (symmetric encoder-decoder)
"""
import logging
import torch
import torch.nn as nn
import numpy as np
from pathlib import Path

logger = logging.getLogger("kalpixk.detection.autoencoder")
MODELS_DIR = Path(__file__).parent.parent / "models"

class _AutoencoderNet(nn.Module):
    def __init__(self, input_dim: int = 32):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16), nn.ReLU(), nn.BatchNorm1d(16),
            nn.Linear(16, 8),         nn.ReLU(), nn.BatchNorm1d(8),
            nn.Linear(8, 4),          nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(4, 8),          nn.ReLU(), nn.BatchNorm1d(8),
            nn.Linear(8, 16),         nn.ReLU(), nn.BatchNorm1d(16),
            nn.Linear(16, input_dim), nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(x))

    def reconstruction_error(self, x: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            recon = self.forward(x)
            return torch.mean((x - recon) ** 2, dim=1)

class KalpixkAutoencoder:
    VERSION = "0.1.0"
    THRESHOLD_PERCENTILE = 95  # Top 5% reconstruction error → anomaly

    def __init__(self, device: torch.device):
        self.device = device
        self.net = _AutoencoderNet(input_dim=32).to(device)
        self._threshold = 0.05
        self._is_trained = False
        self._load()

    def _load(self):
        path = MODELS_DIR / "autoencoder.pt"
        if path.exists():
            try:
                state = torch.load(path, map_location=self.device)
                self.net.load_state_dict(state["model"])
                self._threshold = state.get("threshold", 0.05)
                self._is_trained = True
                logger.info(f"Autoencoder cargado desde {path}")
            except Exception as e:
                logger.error(f"Error cargando autoencoder: {e}")

    def fit(self, X: np.ndarray, epochs: int = 10, lr: float = 1e-3):
        self.net.train()
        optimizer = torch.optim.Adam(self.net.parameters(), lr=lr)
        criterion = nn.MSELoss()

        X_tensor = torch.tensor(X, dtype=torch.float32).to(self.device)
        dataset = torch.utils.data.TensorDataset(X_tensor)
        loader = torch.utils.data.DataLoader(dataset, batch_size=512, shuffle=True)

        logger.info(f"Entrenando Autoencoder por {epochs} épocas")
        for epoch in range(epochs):
            total_loss = 0
            for (batch,) in loader:
                optimizer.zero_grad()
                output = self.net(batch)
                loss = criterion(output, batch)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

        # Set threshold at 95th percentile of training reconstruction error
        self.net.eval()
        with torch.no_grad():
            errors = self.net.reconstruction_error(X_tensor).cpu().numpy()
        self._threshold = float(np.percentile(errors, self.THRESHOLD_PERCENTILE))
        self._is_trained = True
        logger.info(f"Entrenamiento completado. Threshold: {self._threshold:.6f}")
        return self

    def predict(self, X: np.ndarray) -> tuple[list[float], list[float]]:
        self.net.eval()
        tensor = torch.tensor(X, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            errors = self.net.reconstruction_error(tensor).cpu().numpy()

        # Normalize: error / threshold. Cap at 1.0.
        # If error > threshold, score > 1.0, but we want [0, 1] usually.
        # Actually, let's follow the brief's min(1.0, e / threshold)
        scores = [float(min(1.0, e / (self._threshold + 1e-8))) for e in errors]
        confidences = [min(1.0, s * 1.2) for s in scores]
        return scores, confidences

    def save(self):
        MODELS_DIR.mkdir(exist_ok=True)
        torch.save({"model": self.net.state_dict(), "threshold": self._threshold},
                   MODELS_DIR / "autoencoder.pt")
        logger.info(f"Autoencoder guardado en {MODELS_DIR / 'autoencoder.pt'}")
