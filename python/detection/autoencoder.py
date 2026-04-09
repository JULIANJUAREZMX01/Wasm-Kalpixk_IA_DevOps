import torch
import torch.nn as nn
import numpy as np

class AutoencoderModel(nn.Module):
    def __init__(self, input_dim=32):
        super(AutoencoderModel, self).__init__()
        # Encoder: 32 -> 16 -> 8 -> 4
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 4),
            nn.ReLU()
        )
        # Decoder: 4 -> 8 -> 16 -> 32
        self.decoder = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(),
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, input_dim),
            nn.Sigmoid()
        )

    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x

class AutoencoderDetector:
    def __init__(self, device: torch.device):
        self.device = device
        self.model = AutoencoderModel().to(device)
        self.model.eval()

    def predict(self, features: torch.Tensor) -> np.ndarray:
        self.model.eval()
        with torch.no_grad():
            features = features.to(self.device)
            reconstructed = self.model(features)
            # MSE como error de reconstrucción
            errors = torch.mean((features - reconstructed) ** 2, dim=1)

            # Normalización simple basada en el máximo del batch
            max_err = torch.max(errors).item()
            if max_err > 0:
                normalized = errors / max_err
            else:
                normalized = torch.zeros_like(errors)

            return normalized.cpu().numpy()

    def train(self, X: torch.Tensor, epochs=10):
        self.model.train()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        criterion = nn.MSELoss()

        for epoch in range(epochs):
            optimizer.zero_grad()
            output = self.model(X.to(self.device))
            loss = criterion(output, X.to(self.device))
            loss.backward()
            optimizer.step()
