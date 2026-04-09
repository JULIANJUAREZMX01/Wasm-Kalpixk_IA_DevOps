"""
python/detection/isolation_forest.py
─────────────────────────────────────
KalpixkIsolationForest — GPU-accelerated anomaly detection.
Uses cuML (AMD ROCm) with automatic sklearn CPU fallback.

Contract:
  - Input:  np.ndarray [N, 32]  float32, all values in [0, 1]
  - Output: scores [N]          float32, all values in [0, 1]
            confidences [N]     float32, all values in [0, 1]

ADR reference: ADR-002 (Ensemble IsolationForest + Autoencoder)
"""

from __future__ import annotations

import logging
import pickle
import time
from pathlib import Path
from typing import Optional

import numpy as np
import torch

logger = logging.getLogger("kalpixk.detection.isolation_forest")

MODELS_DIR  = Path(__file__).parent.parent / "models"
MODEL_PATH  = MODELS_DIR / "isolation_forest.pkl"
FEATURE_DIM = 32          # Contract with kalpixk-core/src/features.rs


class KalpixkIsolationForest:
    """
    Isolation Forest with AMD ROCm GPU acceleration via cuML.
    Falls back to scikit-learn transparently when cuML is not available.

    Usage:
        model = KalpixkIsolationForest(device)
        model.fit(X_normal)          # Train on normal traffic baseline
        scores, conf = model.predict(X_new)
    """

    VERSION        = "0.1.0"
    N_ESTIMATORS   = 200
    CONTAMINATION  = 0.05   # Expected anomaly rate: 5%
    MAX_SAMPLES    = "auto"
    RANDOM_STATE   = 42

    # ── Init ──────────────────────────────────────────────────────────────────

    def __init__(self, device: torch.device, force_cpu: bool = False):
        self.device     = device
        self.force_cpu  = force_cpu
        self._model     = None
        self._backend   = "none"
        self._is_trained = False
        self._score_min  = -0.5  # Calibrated after fit
        self._score_max  =  0.0

        self._init_model()
        self._try_load()

    def _init_model(self):
        """Initialize model, preferring cuML GPU over sklearn CPU."""
        if not self.force_cpu and str(self.device) != "cpu":
            try:
                from cuml.ensemble import IsolationForest as cuIF  # type: ignore
                self._model   = cuIF(
                    n_estimators=self.N_ESTIMATORS,
                    contamination=self.CONTAMINATION,
                    max_samples=self.MAX_SAMPLES,
                    random_state=self.RANDOM_STATE,
                )
                self._backend = "cuml_gpu"
                logger.info("IsolationForest: using cuML (AMD ROCm GPU)")
                return
            except ImportError:
                logger.warning("cuML not available — falling back to sklearn CPU")

        from sklearn.ensemble import IsolationForest  # type: ignore
        self._model   = IsolationForest(
            n_estimators=self.N_ESTIMATORS,
            contamination=self.CONTAMINATION,
            max_samples=self.MAX_SAMPLES,
            random_state=self.RANDOM_STATE,
            n_jobs=-1,
        )
        self._backend = "sklearn_cpu"
        logger.info("IsolationForest: using sklearn (CPU)")

    def _try_load(self):
        """Load pre-trained model from disk if it exists."""
        if not MODEL_PATH.exists():
            logger.info(f"No pre-trained model at {MODEL_PATH} — will train on first call")
            return
        try:
            with open(MODEL_PATH, "rb") as f:
                state = pickle.load(f)
            self._model      = state["model"]
            self._backend    = state.get("backend", self._backend)
            self._score_min  = state.get("score_min", -0.5)
            self._score_max  = state.get("score_max",  0.0)
            self._is_trained = True
            logger.info(f"Loaded IsolationForest from {MODEL_PATH} (backend={self._backend})")
        except Exception as e:
            logger.error(f"Failed to load model: {e} — reinitializing")
            self._init_model()

    # ── Training ─────────────────────────────────────────────────────────────

    def fit(self, X: np.ndarray) -> "KalpixkIsolationForest":
        """
        Train on baseline (normal) traffic.
        X: [N, 32] float32, normalized [0, 1].
        """
        assert X.shape[1] == FEATURE_DIM, f"Expected {FEATURE_DIM} features, got {X.shape[1]}"
        logger.info(f"Training IsolationForest on {len(X)} samples (backend={self._backend})")

        t0 = time.perf_counter()
        self._model.fit(X.astype(np.float32))

        # Calibrate score range on training data
        raw = self._model.score_samples(X.astype(np.float32))
        self._score_min = float(np.percentile(raw, 1))
        self._score_max = float(np.percentile(raw, 99))

        elapsed = time.perf_counter() - t0
        logger.info(f"Training complete in {elapsed*1000:.1f}ms — saving")

        self._is_trained = True
        self.save()
        return self

    def fit_synthetic(self, n_samples: int = 5000) -> "KalpixkIsolationForest":
        """
        Quick-start: train on synthetic normal traffic.
        Used in dev/testing when real logs aren't available.
        """
        logger.warning("Training on SYNTHETIC data — replace with real logs for production")
        rng = np.random.default_rng(42)

        # Normal traffic: clustered around 0.2-0.4 range for most features
        X = rng.normal(0.3, 0.1, (n_samples, FEATURE_DIM)).clip(0, 1).astype(np.float32)
        # Spike a few features for realism
        X[:, 2] = rng.uniform(0, 1, n_samples)    # hour_of_day: uniform
        X[:, 5] = rng.choice([0, 1], n_samples, p=[0.85, 0.15])  # off_hours: mostly false
        return self.fit(X)

    # ── Inference ────────────────────────────────────────────────────────────

    def predict(
        self, X: np.ndarray
    ) -> tuple[list[float], list[float]]:
        """
        Score anomaly for each event.

        Returns:
            scores      [N] in [0,1] — 1.0 = most anomalous
            confidences [N] in [0,1] — model confidence
        """
        if not self._is_trained:
            logger.warning("Model not trained — fitting synthetic baseline first")
            self.fit_synthetic()

        X = X.astype(np.float32)
        raw = self._model.score_samples(X)  # More negative = more anomalous

        # Normalize to [0, 1] using calibrated range
        span = self._score_max - self._score_min
        if span > 1e-8:
            normalized = np.clip(
                1.0 - (raw - self._score_min) / span,
                0.0, 1.0
            )
        else:
            normalized = np.full(len(raw), 0.5)

        # Confidence: distance from the 0.5 boundary
        confidences = np.clip(np.abs(normalized - 0.5) * 2, 0.3, 1.0)

        return normalized.tolist(), confidences.tolist()

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self):
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        state = {
            "model":      self._model,
            "backend":    self._backend,
            "score_min":  self._score_min,
            "score_max":  self._score_max,
            "version":    self.VERSION,
        }
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(state, f)
        logger.info(f"Model saved to {MODEL_PATH}")

    @property
    def backend(self) -> str:
        return self._backend

    @property
    def is_trained(self) -> bool:
        return self._is_trained
