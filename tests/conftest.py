import pytest
import numpy as np
from src.detector.anomaly_detector import AnomalyDetector
from src.runtime.wasm_monitor import WasmRuntimeMonitor

@pytest.fixture
def detector():
    d = AnomalyDetector()
    # Train with dummy data for tests
    normal_data = np.random.normal(0.5, 0.1, (100, 32))
    d.train(normal_data, epochs=10)
    return d

@pytest.fixture
def monitor():
    return WasmRuntimeMonitor()

@pytest.fixture
def sample_normal():
    return np.random.normal(0.5, 0.01, (1, 32))

@pytest.fixture
def sample_anomaly():
    return np.random.normal(0.9, 0.01, (1, 32))
