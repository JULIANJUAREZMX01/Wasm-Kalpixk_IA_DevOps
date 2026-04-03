"""
Kalpixk Autoencoder — AMD ROCm MI300X
Anomaly detection engine core
"""
import torch
import torch.nn as nn
import numpy as np

ANOMALY_THRESHOLDS = {
    'CLEAN': (0, 10),
    'SUSPICIOUS': (10, 50),
    'ANOMALY': (50, 100),
    'CRITICAL': (100, float('inf'))
}

def classify_severity(score: float) -> str:
    for level, (low, high) in ANOMALY_THRESHOLDS.items():
        if low <= score < high:
            return level
    return 'CRITICAL'


class KalpixkEncoder(nn.Module):
    def __init__(self, input_dim=10, latent_dim=2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 5),
            nn.ReLU(),
            nn.Linear(5, latent_dim)
        )
    def forward(self, x):
        return self.net(x)


class KalpixkDecoder(nn.Module):
    def __init__(self, latent_dim=2, output_dim=10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(latent_dim, 5),
            nn.ReLU(),
            nn.Linear(5, output_dim)
        )
    def forward(self, x):
        return self.net(x)


class KalpixkAutoencoder(nn.Module):
    """
    Core anomaly detection model.
    High reconstruction error = anomaly (module deviates from normal WASM behavior)
    """
    def __init__(self, input_dim=10, latent_dim=2):
        super().__init__()
        self.encoder = KalpixkEncoder(input_dim, latent_dim)
        self.decoder = KalpixkDecoder(latent_dim, input_dim)

    def forward(self, x):
        return self.decoder(self.encoder(x))

    def anomaly_score(self, x):
        with torch.no_grad():
            reconstructed = self.forward(x)
            score = nn.MSELoss()(reconstructed, x).item()
        return score, classify_severity(score)


if __name__ == '__main__':
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'Device: {device}')

    model = KalpixkAutoencoder().to(device)

    # Simulated malicious WASM module
    malicious = torch.tensor([[10.0]*10]).to(device)
    score, severity = model.anomaly_score(malicious)
    print(f'Anomaly score: {score:.4f} — Severity: {severity}')

    # Simulated normal WASM module
    normal = torch.randn(1, 10).to(device)
    score_n, sev_n = model.anomaly_score(normal)
    print(f'Normal score: {score_n:.4f} — Severity: {sev_n}')
