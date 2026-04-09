import os
import torch
import torch.nn as nn
import numpy as np
from loguru import logger
from sklearn.preprocessing import StandardScaler
import joblib
import json

class KalpixkAutoencoder(nn.Module):
    def __init__(self, input_dim=32, latent_dim=16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, latent_dim),
            nn.ReLU(),
            nn.Linear(latent_dim, 4),
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(4, latent_dim),
            nn.ReLU(),
            nn.Linear(latent_dim, input_dim),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))

    def reconstruction_error(self, x):
        return nn.MSELoss(reduction="none")(self.forward(x), x).mean(dim=1)

class AnomalyDetector:
    def __init__(self, input_dim: int = 32, latent_dim: int = 16):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = KalpixkAutoencoder(input_dim, latent_dim).to(self.device)
        self.threshold: float = 0.5
        self.is_trained: bool = False
        self.scaler = StandardScaler()
        self.train_stats: dict = {}
        self.input_dim = input_dim
        logger.info(f"AnomalyDetector v2.2 | device={self.device}")

    def _normalize(self, X: np.ndarray, fit: bool = False) -> np.ndarray:
        if fit:
            return self.scaler.fit_transform(X).astype(np.float32)
        return self.scaler.transform(X).astype(np.float32)

    def train(self, normal_data: np.ndarray, epochs: int = 50, lr: float = 1e-3) -> dict:
        X_norm = self._normalize(normal_data, fit=True)
        X = torch.FloatTensor(X_norm).to(self.device)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.MSELoss()

        self.model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            out = self.model(X)
            loss = criterion(out, X)
            loss.backward()
            optimizer.step()

        self.model.eval()
        train_errors = self.model.reconstruction_error(X).cpu().detach().numpy()

        # Umbral dinámico: percentil 95
        self.threshold = float(np.percentile(train_errors, 95))
        self.is_trained = True

        self.train_stats = {
            "final_loss": float(loss.item()),
            "threshold": self.threshold,
            "mean_error": float(np.mean(train_errors)),
            "std_error": float(np.std(train_errors))
        }
        logger.success(f"Entrenamiento completado. Umbral: {self.threshold:.6f}")
        return self.train_stats

    def predict(self, X: np.ndarray) -> dict:
        self.model.eval()
        X_norm = self._normalize(X, fit=False)
        with torch.no_grad():
            t_X = torch.FloatTensor(X_norm).to(self.device)
            errors = self.model.reconstruction_error(t_X).cpu().numpy()

        anomalies = errors > self.threshold
        return {
            "reconstruction_errors": errors.tolist(),
            "anomalies": anomalies.tolist(),
            "threshold": self.threshold,
            "anomaly_count": int(anomalies.sum())
        }

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        """Calcula métricas honestas: Precision, Recall, F1, AUC."""
        from sklearn.metrics import precision_recall_fscore_support, roc_auc_score

        res = self.predict(X_test)
        y_pred = np.array(res["anomalies"]).astype(int)
        y_scores = np.array(res["reconstruction_errors"])

        precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary', zero_division=0)
        try:
            auc = roc_auc_score(y_test, y_scores)
        except:
            auc = 0.5

        metrics = {
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "auc": float(auc),
            "threshold": self.threshold
        }
        logger.info(f"Evaluación: F1={f1:.4f}, AUC={auc:.4f}")
        return metrics

    def save_evaluation_report(self, metrics: dict, path: str = "models/evaluation_report.json"):
        with open(path, "w") as f:
            json.dump(metrics, f, indent=4)
        logger.info(f"Reporte de evaluación guardado en {path}")

    def save(self, path: str = "models/kalpixk_v2.pt"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save({
            "model_state": self.model.state_dict(),
            "threshold": self.threshold,
            "input_dim": self.input_dim
        }, path)
        joblib.dump(self.scaler, path.replace(".pt", "_scaler.joblib"))

    def load(self, path: str = "models/kalpixk_v2.pt"):
        state = torch.load(path, map_location=self.device)
        self.model.load_state_dict(state["model_state"])
        self.threshold = state["threshold"]
        self.scaler = joblib.load(path.replace(".pt", "_scaler.joblib"))
        self.is_trained = True
