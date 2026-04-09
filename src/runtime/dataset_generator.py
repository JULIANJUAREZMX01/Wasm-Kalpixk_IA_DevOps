import numpy as np
import os
from loguru import logger
from src.runtime.fallback import fallback_extractor

class WasmDatasetGenerator:
    def __init__(self, output_path="models/dataset_real.npz"):
        self.output_path = output_path
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

    def generate_normal(self, n: int = 10000) -> np.ndarray:
        logger.info(f"Generating {n} normal events...")
        data = []
        for i in range(n):
            # Simulate normal metrics
            metrics = {
                "instruction_count": 100000 + i % 1000,
                "memory_pages": 10,
                "fuel_consumed": 50000,
                "wall_time_ns": 1000000,
                "entropy": 0.3,
                "call_depth": 5,
                "import_calls": 10,
                "export_calls": 5
            }
            data.append(fallback_extractor.extract(metrics))
        return np.array(data)

    def generate_anomalies(self, n: int = 500) -> np.ndarray:
        logger.info(f"Generating {n} anomalies for each type...")
        data = []

        # Memory spike
        for i in range(n):
            metrics = {"instruction_count": 100000, "memory_pages": 1000, "fuel_consumed": 50000, "wall_time_ns": 1000000, "entropy": 0.3, "call_depth": 5, "import_calls": 10, "export_calls": 5}
            data.append(fallback_extractor.extract(metrics))

        # CPU exhaustion
        for i in range(n):
            metrics = {"instruction_count": 10000000, "memory_pages": 10, "fuel_consumed": 9000000, "wall_time_ns": 100000000, "entropy": 0.3, "call_depth": 5, "import_calls": 10, "export_calls": 5}
            data.append(fallback_extractor.extract(metrics))

        # Instruction outlier
        for i in range(n):
            metrics = {"instruction_count": 500000, "memory_pages": 10, "fuel_consumed": 50000, "wall_time_ns": 1000000, "entropy": 0.9, "call_depth": 50, "import_calls": 100, "export_calls": 5}
            data.append(fallback_extractor.extract(metrics))

        return np.array(data)

    def build_labeled_dataset(self):
        X_normal = self.generate_normal(10000)
        X_anomalies = self.generate_anomalies(500)

        X = np.vstack([X_normal, X_anomalies])
        y = np.concatenate([np.zeros(len(X_normal)), np.ones(len(X_anomalies))])

        logger.success(f"Saving dataset to {self.output_path}")
        np.savez(self.output_path, X=X, y=y)
        return X, y

if __name__ == "__main__":
    generator = WasmDatasetGenerator()
    generator.build_labeled_dataset()
