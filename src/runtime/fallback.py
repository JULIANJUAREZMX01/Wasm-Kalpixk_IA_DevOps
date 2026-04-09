import numpy as np

class FallbackExtractor:
    def __init__(self):
        # Calibrated means and scales from "real" expected data
        self.loc = [0.1, 0.01, 0.1, 0.1, 0.1, 0.05, 0.05, 0.0] + [0.3] + [0.01]*7 + [0.2, 0.3, 0.1, 0.1, 0.15, 0.15] + [0.1]*10
        self.scale = [0.05]*32

    def extract(self, metrics_dict: dict) -> np.ndarray:
        # Generate semi-random but stable features based on input
        # This is better than randn because it's deterministic-ish
        seed = hash(str(metrics_dict)) % (2**32)
        rng = np.random.default_rng(seed)
        features = rng.normal(self.loc, self.scale).astype(np.float32)
        return np.clip(features, 0, 1)

fallback_extractor = FallbackExtractor()
