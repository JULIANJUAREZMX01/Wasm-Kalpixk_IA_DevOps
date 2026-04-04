"""
Wasm-Kalpixk — WASM Runtime Monitor
Captura métricas del runtime WASM y las alimenta al AnomalyDetector
"""
import time
import psutil
import numpy as np
from dataclasses import dataclass
from loguru import logger
from typing import Optional


@dataclass
class WasmMetrics:
    """10 features que el autoencoder analiza."""
    cpu_usage: float        # % CPU del proceso WASM
    memory_mb: float        # MB de memoria usada
    exec_time_ms: float     # tiempo de ejecución del módulo
    instructions: float     # instrucciones ejecutadas (normalizado)
    memory_pages: float     # páginas de memoria WASM (x64KB)
    function_calls: float   # llamadas a funciones exportadas
    traps: float            # traps/errores del runtime
    imports: float          # funciones importadas activas
    exports: float          # funciones exportadas activas
    heap_usage: float       # % heap del sistema

    def to_array(self) -> np.ndarray:
        return np.array([[
            self.cpu_usage, self.memory_mb, self.exec_time_ms,
            self.instructions, self.memory_pages, self.function_calls,
            self.traps, self.imports, self.exports, self.heap_usage
        ]], dtype=np.float32)


class WasmRuntimeMonitor:
    """
    Monitorea el runtime WASM y extrae métricas para el detector.
    En producción: integrar con wasmtime o wasmer para métricas reales.
    """
    def __init__(self, sample_interval: float = 1.0):
        self.sample_interval = sample_interval
        self.baseline: Optional[WasmMetrics] = None
        logger.info("WasmRuntimeMonitor inicializado")

    def capture_metrics(self) -> WasmMetrics:
        """Captura métricas actuales del sistema + runtime WASM."""
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        
        metrics = WasmMetrics(
            cpu_usage=cpu,
            memory_mb=mem.used / 1e6,
            exec_time_ms=0.0,     # rellenar con wasmtime profiler
            instructions=0.0,      # rellenar con instrumentación WASM
            memory_pages=mem.used / (64 * 1024),
            function_calls=0.0,    # rellenar con hooks de runtime
            traps=0.0,
            imports=0.0,
            exports=0.0,
            heap_usage=mem.percent
        )
        return metrics

    def generate_normal_baseline(self, n_samples: int = 500) -> np.ndarray:
        """Genera datos de entrenamiento simulando operación normal."""
        np.random.seed(42)
        return np.random.normal(
            loc=[30, 512, 5, 1000, 8, 50, 0, 10, 5, 40],
            scale=[5, 50, 1, 100, 1, 10, 0.1, 1, 0.5, 5],
            size=(n_samples, 10)
        ).astype(np.float32)

    def simulate_anomaly(self, anomaly_type: str = "memory_spike") -> WasmMetrics:
        """Simula diferentes tipos de anomalías para testing."""
        base = self.capture_metrics()
        if anomaly_type == "memory_spike":
            base.memory_mb *= 10
            base.memory_pages *= 10
        elif anomaly_type == "cpu_spike":
            base.cpu_usage = 95.0
            base.exec_time_ms = 500.0
        elif anomaly_type == "trap_storm":
            base.traps = 100.0
        return base
