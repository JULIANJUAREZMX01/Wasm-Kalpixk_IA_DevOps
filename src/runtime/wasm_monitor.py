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
    """32 features sincronizadas con kalpixk-core (Rust)."""
    # 0-9: Core Runtime Metrics
    cpu_usage: float
    memory_mb: float
    exec_time_ms: float
    instructions: float
    memory_pages: float
    function_calls: float
    traps: float
    imports: float
    exports: float
    heap_usage: float

    # 10-31: Security Context Features (Extended)
    hour_normalized: float = 0.5
    day_normalized: float = 0.5
    is_weekend: float = 0.0
    is_off_hours: float = 0.0
    is_internal: float = 1.0
    has_destination: float = 0.0
    has_user: float = 0.0
    source_entropy: float = 0.3
    user_entropy: float = 0.0
    metadata_count: float = 0.1
    is_privileged_port: float = 0.0
    dest_port_norm: float = 0.0
    bytes_log10: float = 0.0
    has_sql: float = 0.0
    has_destructive: float = 0.0
    is_sensitive_table: float = 0.0
    has_bulk_op: float = 0.0
    is_scan: float = 0.0
    is_privileged_account: float = 0.0
    is_known_process: float = 1.0
    has_lateral_move: float = 0.0
    is_cloud: float = 0.0

    def to_array(self) -> np.ndarray:
        return np.array([[
            self.cpu_usage, self.memory_mb, self.exec_time_ms,
            self.instructions, self.memory_pages, self.function_calls,
            self.traps, self.imports, self.exports, self.heap_usage,
            self.hour_normalized, self.day_normalized, self.is_weekend,
            self.is_off_hours, self.is_internal, self.has_destination,
            self.has_user, self.source_entropy, self.user_entropy,
            self.metadata_count, self.is_privileged_port, self.dest_port_norm,
            self.bytes_log10, self.has_sql, self.has_destructive,
            self.is_sensitive_table, self.has_bulk_op, self.is_scan,
            self.is_privileged_account, self.is_known_process,
            self.has_lateral_move, self.is_cloud
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
        
        # Simulación de métricas extendidas basadas en el tiempo actual
        import datetime
        now = datetime.datetime.now()

        metrics = WasmMetrics(
            cpu_usage=cpu,
            memory_mb=mem.used / 1e6,
            exec_time_ms=0.0,
            instructions=0.0,
            memory_pages=mem.used / (64 * 1024),
            function_calls=0.0,
            traps=0.0,
            imports=0.0,
            exports=0.0,
            heap_usage=mem.percent,
            hour_normalized=now.hour / 23.0,
            day_normalized=now.weekday() / 6.0,
            is_weekend=1.0 if now.weekday() >= 5 else 0.0,
            is_off_hours=1.0 if not (8 <= now.hour <= 18) else 0.0
        )
        return metrics

    def generate_normal_baseline(self, n_samples: int = 500) -> np.ndarray:
        """Genera datos de entrenamiento simulando operación normal (32 features)."""
        np.random.seed(42)
        # 32 features
        loc = [30, 512, 5, 1000, 8, 50, 0, 10, 5, 40] + [0.5]*22
        scale = [5, 50, 1, 100, 1, 10, 0.1, 1, 0.5, 5] + [0.1]*22
        return np.random.normal(
            loc=loc,
            scale=scale,
            size=(n_samples, 32)
        ).astype(np.float32)

    def simulate_anomaly(self, anomaly_type: str = "memory_spike") -> WasmMetrics:
        """Simula diferentes tipos de anomalías para testing."""
        base = self.capture_metrics()
        if anomaly_type == "memory_spike":
            base.memory_mb *= 10
            base.memory_pages *= 10
            base.heap_usage = 95.0
        elif anomaly_type == "cpu_spike":
            base.cpu_usage = 95.0
            base.exec_time_ms = 500.0
        elif anomaly_type == "trap_storm":
            base.traps = 100.0
        return base
