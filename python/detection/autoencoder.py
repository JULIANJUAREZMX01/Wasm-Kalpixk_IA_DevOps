"""
python/detection/autoencoder.py
────────────────────────────────
KalpixkAutoencoder — Reconstruction-error anomaly detection.
Architecture: 32 → 16 → 8 → 4 → 8 → 16 → 32 (symmetric).
Runs natively on AMD MI300X via ROCm.

Anomaly = high reconstruction error: the model cannot reconstruct
events that are structurally different from normal training data.

ADR reference: ADR-002 (Ensemble IsolationForest + Autoencoder)
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

logger = logging.getLogger("kalpixk.detection.autoencoder")

MODELS_DIR   = Path(__file__).parent.parent / "models"
MODEL_PATH   = MODELS_DIR / "autoencoder.pt"
FEATURE_DIM  = 32   # Contract with kalpixk-core/src/features.rs


# ── Neural network architecture ───────────────────────────────────────────────

class _AENet(nn.Module):
    """
    Symmetric autoencoder: 32 → 16 → 8 → 4 → 8 → 16 → 32.
    BatchNorm on every encoder/decoder layer for training stability.
    Sigmoid output: features are normalized [0, 1] so this is correct.
    """

    def __init__(self, input_dim: int = FEATURE_DIM, dropout: float = 0.1):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.BatchNorm1d(16),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(16, 8),
            nn.BatchNorm1d(8),
            nn.ReLU(),
            nn.Linear(8, 4),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(4, 8),
            nn.BatchNorm1d(8),
            nn.ReLU(),
            nn.Linear(8, 16),
            nn.BatchNorm1d(16),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(16, input_dim),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(x))

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """Get the latent representation (bottleneck) for a given input."""
        return self.encoder(x)

    def reconstruction_error(self, x: torch.Tensor) -> torch.Tensor:
        """Per-sample MSE between input and reconstruction. Shape: [N]."""
        with torch.no_grad():
            recon = self.forward(x)
            return torch.mean((x - recon) ** 2, dim=1)


# ── Main class ────────────────────────────────────────────────────────────────

class KalpixkAutoencoder:
    """
    PyTorch autoencoder for unsupervised anomaly detection.
    Runs on AMD MI300X via ROCm. Falls back to CPU transparently.

    Usage:
        ae = KalpixkAutoencoder(device)
        ae.fit(X_normal, epochs=100)
        scores, confidences = ae.predict(X_new)
    """

    VERSION             = "0.1.0"
    DEFAULT_EPOCHS      = 100
    DEFAULT_BATCH_SIZE  = 512
    DEFAULT_LR          = 1e-3
    THRESHOLD_PERCENTILE = 95   # Top 5% error → anomaly

    # ── Init ──────────────────────────────────────────────────────────────────

    def __init__(self, device: torch.device):
        self.device      = device
        self.net         = _AENet().to(device)
        self._threshold  = 0.05   # Calibrated after fit
        self._is_trained = False
        self._try_load()

    def _try_load(self):
        if not MODEL_PATH.exists():
            return
        try:
            state = torch.load(MODEL_PATH, map_location=self.device, weights_only=False)
            self.net.load_state_dict(state["model_state"])
            self._threshold  = float(state.get("threshold", 0.05))
            self._is_trained = True
            logger.info(f"Autoencoder loaded from {MODEL_PATH} (threshold={self._threshold:.4f})")
        except Exception as e:
            logger.error(f"Failed to load autoencoder: {e} — using fresh model")

    # ── Training ─────────────────────────────────────────────────────────────

    def fit(
        self,
        X: np.ndarray,
        epochs: int = DEFAULT_EPOCHS,
        batch_size: int = DEFAULT_BATCH_SIZE,
        lr: float = DEFAULT_LR,
        val_split: float = 0.1,
    ) -> KalpixkAutoencoder:
        """
        Train on normal traffic baseline.
        X: [N, 32] float32, all values in [0, 1].
        """
        assert X.shape[1] == FEATURE_DIM
        logger.info(f"Training Autoencoder: {len(X)} samples, {epochs} epochs, device={self.device}")

        # Train / validation split
        n_val   = max(1, int(len(X) * val_split))
        X_val   = torch.tensor(X[:n_val],  dtype=torch.float32).to(self.device)
        X_train = torch.tensor(X[n_val:],  dtype=torch.float32).to(self.device)

        dataset = TensorDataset(X_train, X_train)
        loader  = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)

        optimizer = torch.optim.Adam(self.net.parameters(), lr=lr, weight_decay=1e-5)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
        criterion = nn.MSELoss()

        t0         = time.perf_counter()
        best_val   = float("inf")
        best_state = None

        self.net.train()
        for epoch in range(epochs):
            total_loss = 0.0
            for batch_x, batch_y in loader:
                optimizer.zero_grad()
                loss = criterion(self.net(batch_x), batch_y)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.net.parameters(), 1.0)
                optimizer.step()
                total_loss += loss.item()

            scheduler.step()

            # Validation
            self.net.eval()
            with torch.no_grad():
                val_loss = criterion(self.net(X_val), X_val).item()
            self.net.train()

            if val_loss < best_val:
                best_val   = val_loss
                best_state = {k: v.clone() for k, v in self.net.state_dict().items()}

            if (epoch + 1) % 10 == 0:
                logger.debug(f"Epoch {epoch+1}/{epochs} — train={total_loss/len(loader):.5f} val={val_loss:.5f}")

        # Restore best model
        if best_state:
            self.net.load_state_dict(best_state)

        # Calibrate threshold on training data
        self.net.eval()
        with torch.no_grad():
            errors = self.net.reconstruction_error(X_train).cpu().numpy()
        self._threshold  = float(np.percentile(errors, self.THRESHOLD_PERCENTILE))
        self._is_trained = True

        elapsed = time.perf_counter() - t0
        logger.info(
            f"Training complete: {elapsed:.1f}s — "
            f"best_val_loss={best_val:.5f} threshold={self._threshold:.4f}"
        )
        self.save()
        return self

    def fit_synthetic(self, n_samples: int = 5000) -> KalpixkAutoencoder:
        """Quick-start on synthetic normal data for dev/testing."""
        logger.warning("Training Autoencoder on SYNTHETIC data — replace for production")
        rng = np.random.default_rng(42)
        X = rng.normal(0.3, 0.1, (n_samples, FEATURE_DIM)).clip(0, 1).astype(np.float32)
        return self.fit(X, epochs=30)  # Fewer epochs for dev speed

    # ── Inference ────────────────────────────────────────────────────────────

    def predict(
        self, X: np.ndarray
    ) -> tuple[list[float], list[float]]:
        """
        Score anomaly via reconstruction error.

        Returns:
            scores      [N] in [0,1] — 1.0 = most anomalous
            confidences [N] in [0,1] — model confidence
        """
        if not self._is_trained:
            logger.warning("Autoencoder not trained — fitting synthetic first")
            self.fit_synthetic()

        self.net.eval()
        tensor = torch.tensor(X.astype(np.float32)).to(self.device)

        with torch.no_grad():
            errors = self.net.reconstruction_error(tensor).cpu().numpy()

        # Normalize: error / threshold → [0, 1]
        t    = max(self._threshold, 1e-8)
        norm = np.clip(errors / t, 0.0, 2.0) / 2.0   # Cap at 2× threshold

        # Confidence: certainty scales with distance from 0.5
        conf = np.clip(np.abs(norm - 0.5) * 2, 0.3, 1.0)
        return norm.tolist(), conf.tolist()

    def get_latent(self, X: np.ndarray) -> np.ndarray:
        """Return latent (bottleneck) vectors — useful for visualization."""
        self.net.eval()
        tensor = torch.tensor(X.astype(np.float32)).to(self.device)
        with torch.no_grad():
            return self.net.encode(tensor).cpu().numpy()

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self):
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        torch.save({
            "model_state": self.net.state_dict(),
            "threshold":   self._threshold,
            "version":     self.VERSION,
        }, MODEL_PATH)
        logger.info(f"Autoencoder saved to {MODEL_PATH}")

    @property
    def threshold(self) -> float:
        return self._threshold

    @property
    def is_trained(self) -> bool:
        return self._is_trained
