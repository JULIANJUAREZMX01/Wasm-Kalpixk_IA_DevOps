"""
Kalpixk Test Suite v2
Valida: normalización, auto-threshold, evaluate, save/load, API
"""
import numpy as np
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.detector import AnomalyDetector, KalpixkAutoencoder
from src.runtime import WasmRuntimeMonitor, WasmMetrics


@pytest.fixture
def trained_detector():
    """Detector entrenado con baseline normal."""
    det = AnomalyDetector()
    mon = WasmRuntimeMonitor()
    data = mon.generate_normal_baseline(300)
    det.train(data, epochs=50)
    return det, mon


# ── Init ────────────────────────────────────────────────────────
def test_detector_init():
    det = AnomalyDetector()
    assert det.model is not None
    assert det.device is not None
    assert not det.is_trained

def test_autoencoder_shape():
    model = KalpixkAutoencoder(input_dim=10, latent_dim=4)
    import torch
    x = torch.randn(5, 10)
    out = model(x)
    assert out.shape == (5, 10), "Output shape debe ser igual al input"

# ── Monitor ─────────────────────────────────────────────────────
def test_monitor_metrics():
    mon = WasmRuntimeMonitor()
    m = mon.capture_metrics()
    assert isinstance(m, WasmMetrics)
    arr = m.to_array()
    assert arr.shape == (1, 10)
    assert all(isinstance(v, float) for v in [m.cpu_usage, m.memory_mb])

def test_baseline_generation():
    mon = WasmRuntimeMonitor()
    data = mon.generate_normal_baseline(200)
    assert data.shape == (200, 10)
    assert data.dtype == np.float32

def test_simulate_anomalies():
    mon = WasmRuntimeMonitor()
    for atype in ["memory_spike", "cpu_spike", "trap_storm"]:
        m = mon.simulate_anomaly(atype)
        assert isinstance(m, WasmMetrics)
    # memory spike debe tener memoria alta
    m_mem = mon.simulate_anomaly("memory_spike")
    assert m_mem.memory_mb > 1000

# ── Training ────────────────────────────────────────────────────
def test_train_returns_stats(trained_detector):
    det, mon = trained_detector
    assert det.is_trained
    assert "threshold" in det.train_stats
    assert "final_loss" in det.train_stats
    assert det.threshold > 0
    print(f"\n  threshold={det.threshold:.4f} loss={det.train_stats['final_loss']:.6f}")

def test_auto_threshold_calibration():
    """Threshold debe calibrarse automáticamente (no hardcodeado)."""
    det = AnomalyDetector()
    mon = WasmRuntimeMonitor()
    data = mon.generate_normal_baseline(300)
    stats = det.train(data, epochs=50, auto_threshold_sigma=2.0)
    # threshold = mean + 2*std — debe ser > 0
    expected = stats["train_error_mean"] + 2.0 * stats["train_error_std"]
    assert abs(det.threshold - expected) < 1e-5

# ── Prediction ──────────────────────────────────────────────────
def test_predict_normal_no_false_positives(trained_detector):
    """Datos normales NO deben disparar anomalía (< 10% FP)."""
    det, mon = trained_detector
    data = mon.generate_normal_baseline(50)
    result = det.predict(data)
    fp_rate = sum(result["anomalies"]) / 50
    assert fp_rate <= 0.10, f"Demasiados falsos positivos: {fp_rate:.1%}"
    print(f"\n  FP rate: {fp_rate:.1%} ✅")

def test_predict_anomalies_detected(trained_detector):
    """Anomalías obvias DEBEN ser detectadas (recall > 95%)."""
    det, mon = trained_detector
    # Anomalías extremas — valores 10x fuera de rango normal
    anomalies = np.tile([1000.0, 50000.0, 500.0, 50000.0, 500.0,
                          5000.0, 100.0, 100.0, 50.0, 99.0], (20, 1)).astype(np.float32)
    result = det.predict(anomalies)
    recall = sum(result["anomalies"]) / 20
    assert recall >= 0.95, f"Recall insuficiente: {recall:.1%}"
    print(f"\n  Anomaly recall: {recall:.1%} ✅")

def test_predict_output_format(trained_detector):
    det, mon = trained_detector
    m = mon.capture_metrics()
    result = det.predict(m.to_array())
    assert "reconstruction_errors" in result
    assert "anomalies" in result
    assert "threshold" in result
    assert "scores_normalized" in result
    assert "anomaly_count" in result
    assert "device" in result
    score = result["scores_normalized"][0]
    assert 0.0 <= score <= 1.0, f"score_normalized debe estar en [0,1]: {score}"

def test_simulate_anomalies_detected(trained_detector):
    """Las 3 anomalías simuladas deben detectarse."""
    det, mon = trained_detector
    for atype in ["memory_spike", "cpu_spike", "trap_storm"]:
        sim = mon.simulate_anomaly(atype)
        result = det.predict(sim.to_array())
        assert result["anomalies"][0], f"No detectó {atype}"
        print(f"\n  {atype}: score={result['reconstruction_errors'][0]:.2f} ✅")

# ── Evaluate ────────────────────────────────────────────────────
def test_evaluate_metrics(trained_detector):
    det, mon = trained_detector
    normal = mon.generate_normal_baseline(30)
    anomalies = np.tile([5000.0]*10, (10, 1)).astype(np.float32)
    metrics = det.evaluate(normal, anomalies)
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1" in metrics
    assert metrics["recall"] > 0.8, f"Recall debe ser > 80%: {metrics['recall']:.1%}"
    print(f"\n  Precision={metrics['precision']:.1%} Recall={metrics['recall']:.1%} F1={metrics['f1']:.1%}")

# ── Save / Load ─────────────────────────────────────────────────
def test_save_load_roundtrip(trained_detector, tmp_path):
    det, mon = trained_detector
    path = str(tmp_path / "test_model.pt")
    det.save(path)
    # Cargar en nuevo detector
    det2 = AnomalyDetector()
    det2.load(path)
    assert det2.is_trained
    assert abs(det2.threshold - det.threshold) < 1e-5
    # Predict debe dar resultados idénticos
    m = mon.capture_metrics()
    r1 = det.predict(m.to_array())
    r2 = det2.predict(m.to_array())
    assert abs(r1["reconstruction_errors"][0] - r2["reconstruction_errors"][0]) < 1e-3

# ── UI ──────────────────────────────────────────────────────────
def test_theme_imports():
    from src.ui import KalpixkTheme, ANSI
    assert KalpixkTheme.BANNER
    assert ANSI.RED_BRIGHT
    line = KalpixkTheme.status_line("GPU", "AMD MI300X", "ok")
    assert "AMD MI300X" in line

# ── Integration ─────────────────────────────────────────────────
def test_full_pipeline():
    """Pipeline completo: train → monitor → predict → evaluate."""
    det = AnomalyDetector()
    mon = WasmRuntimeMonitor()

    # 1. Entrenar
    normal = mon.generate_normal_baseline(400)
    stats = det.train(normal, epochs=75)
    assert det.is_trained

    # 2. Capturar métricas reales
    m = mon.capture_metrics()
    result = det.predict(m.to_array())
    assert result["scores_normalized"][0] <= 1.0

    # 3. Evaluar
    anomalies = np.tile([9999.0]*10, (5, 1)).astype(np.float32)
    eval_res = det.evaluate(normal[:20], anomalies)
    assert eval_res["f1"] > 0.5

    print(f"\n  Pipeline OK | F1={eval_res['f1']:.1%} threshold={det.threshold:.4f}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
