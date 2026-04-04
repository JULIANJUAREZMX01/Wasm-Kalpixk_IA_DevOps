"""
Tests del motor de detección Kalpixk
"""
import numpy as np
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.detector import AnomalyDetector
from src.runtime import WasmRuntimeMonitor, WasmMetrics


def test_detector_init():
    detector = AnomalyDetector()
    assert detector.model is not None
    assert detector.threshold == 0.5

def test_monitor_metrics():
    monitor = WasmRuntimeMonitor()
    metrics = monitor.capture_metrics()
    assert isinstance(metrics, WasmMetrics)
    arr = metrics.to_array()
    assert arr.shape == (1, 10)

def test_baseline_generation():
    monitor = WasmRuntimeMonitor()
    baseline = monitor.generate_normal_baseline(n_samples=100)
    assert baseline.shape == (100, 10)

def test_train_and_predict():
    detector = AnomalyDetector()
    monitor = WasmRuntimeMonitor()
    normal = monitor.generate_normal_baseline(n_samples=200)
    detector.train(normal, epochs=10)
    assert detector.is_trained
    
    result = detector.predict(normal[:5])
    assert "reconstruction_errors" in result
    assert "anomalies" in result
    assert len(result["anomalies"]) == 5

def test_anomaly_detection():
    detector = AnomalyDetector(threshold=0.1)
    monitor = WasmRuntimeMonitor()
    normal = monitor.generate_normal_baseline(n_samples=200)
    detector.train(normal, epochs=20)
    
    # Anomalia obvia: valores extremos
    anomaly = np.array([[1000.0]*10], dtype=np.float32)
    result = detector.predict(anomaly)
    assert result["anomalies"][0] == True, "Deberia detectar anomalia extrema"

def test_simulate_anomaly():
    monitor = WasmRuntimeMonitor()
    m = monitor.simulate_anomaly("memory_spike")
    assert m.memory_mb > 1000  # spike de memoria

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
