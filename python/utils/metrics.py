"""
Métricas de rendimiento — para el benchmark AMD MI300X vs CPU
"""

import time
from collections import deque
from dataclasses import dataclass, field


@dataclass
class PerformanceMetrics:
    """Tracker de métricas de rendimiento del sistema"""
    
    _latencies_ms: deque = field(default_factory=lambda: deque(maxlen=1000))
    _batch_sizes: deque = field(default_factory=lambda: deque(maxlen=1000))
    _anomaly_counts: deque = field(default_factory=lambda: deque(maxlen=1000))
    _total_events: int = 0
    _total_anomalies: int = 0
    _start_time: float = field(default_factory=time.time)
    
    def record_batch(self, batch_size: int, anomalies: int, latency_ms: float):
        self._latencies_ms.append(latency_ms)
        self._batch_sizes.append(batch_size)
        self._anomaly_counts.append(anomalies)
        self._total_events += batch_size
        self._total_anomalies += anomalies
    
    def get_summary(self) -> dict:
        if not self._latencies_ms:
            return {"status": "no_data"}
        
        latencies = list(self._latencies_ms)
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        
        uptime_s = time.time() - self._start_time
        events_per_second = self._total_events / max(uptime_s, 1)
        
        return {
            "total_events_processed": self._total_events,
            "total_anomalies_detected": self._total_anomalies,
            "anomaly_rate_pct": round(
                (self._total_anomalies / max(self._total_events, 1)) * 100, 2
            ),
            "avg_latency_ms": round(avg_latency, 2),
            "p95_latency_ms": round(p95_latency, 2),
            "events_per_second": round(events_per_second, 1),
            "uptime_seconds": round(uptime_s, 1),
            "batches_processed": len(self._latencies_ms),
        }
