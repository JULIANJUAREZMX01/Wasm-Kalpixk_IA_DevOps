"""
Wasm-Kalpixk — WASM Runtime Monitor (v2)
"""
import time
import psutil
import numpy as np
import os
from dataclasses import dataclass
from loguru import logger
from src.runtime.feature_extractor import feature_extractor

@dataclass
class WasmMetrics:
    instruction_count: int
    memory_pages: int
    fuel_consumed: int
    wall_time_ns: int
    entropy: float
    call_depth: int
    import_calls: int
    export_calls: int

    def to_dict(self):
        return self.__dict__

class WasmRuntimeMonitor:
    def __init__(self, sample_interval: float = 1.0):
        self.sample_interval = sample_interval
        logger.info("WasmRuntimeMonitor v2 inicializado")

    def capture_metrics(self) -> np.ndarray:
        """Captura métricas y las convierte a features de 32 dimensiones."""
        # En una integración real con wasmtime, estos valores vendrían del profiler
        # Por ahora, capturamos métricas del sistema como proxy o usamos valores estables
        cpu = psutil.cpu_percent(interval=0.01)
        mem = psutil.virtual_memory()
        
        metrics = WasmMetrics(
            instruction_count=int(cpu * 10000),
            memory_pages=int(mem.used / (64 * 1024)),
            fuel_consumed=int(cpu * 5000),
            wall_time_ns=int(time.time_ns() % 1000000),
            entropy=0.3,
            call_depth=5,
            import_calls=10,
            export_calls=5
        )

        return feature_extractor.extract(metrics.to_dict())

    def generate_normal_baseline(self, n_samples: int = 500) -> np.ndarray:
        """Usa el dataset real si existe, sino genera fallback."""
        dataset_path = "models/dataset_real.npz"
        if os.path.exists(dataset_path):
            logger.info(f"Cargando baseline desde {dataset_path}")
            data = np.load(dataset_path)
            X = data['X']
            y = data['y']
            # Retornar solo los normales (y=0)
            return X[y == 0][:n_samples]

        logger.warning("Dataset real no encontrado, usando fallback sintético")
        from src.runtime.fallback import fallback_extractor
        return np.array([fallback_extractor.extract({}) for _ in range(n_samples)])

    def simulate_anomaly(self, anomaly_type: str = "memory_spike") -> np.ndarray:
        """Simula una anomalía para testing."""
        metrics = {
            "instruction_count": 100000,
            "memory_pages": 10,
            "fuel_consumed": 50000,
            "wall_time_ns": 1000000,
            "entropy": 0.3,
            "call_depth": 5,
            "import_calls": 10,
            "export_calls": 5
        }

        if anomaly_type == "memory_spike":
            metrics["memory_pages"] = 1000
        elif anomaly_type == "cpu_spike":
            metrics["instruction_count"] = 5000000
            metrics["fuel_consumed"] = 4000000
        elif anomaly_type == "trap_storm":
            metrics["entropy"] = 0.9

        return feature_extractor.extract(metrics)
