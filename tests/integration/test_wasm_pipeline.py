import pytest
from src.runtime.wasm_monitor import WasmRuntimeMonitor

def test_pipeline_capture(monitor):
    f = monitor.capture_metrics()
    assert f.shape == (32,)

def test_pipeline_baseline(monitor):
    X = monitor.generate_normal_baseline(n_samples=10)
    assert X.shape == (10, 32)

def test_pipeline_anomaly(monitor):
    f = monitor.simulate_anomaly("memory_spike")
    assert f.shape == (32,)
