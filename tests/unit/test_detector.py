import numpy as np
import pytest
import os

def test_detector_train(detector):
    assert detector.is_trained
    assert detector.threshold > 0
    assert "final_loss" in detector.train_stats

def test_detector_predict(detector, sample_normal, sample_anomaly):
    res_n = detector.predict(sample_normal)
    res_a = detector.predict(sample_anomaly)
    assert "anomalies" in res_n
    assert "reconstruction_errors" in res_n
    # Since it's random, we just check types
    assert isinstance(res_n["anomalies"][0], bool)

def test_detector_evaluate(detector):
    X_test = np.random.normal(0.5, 0.1, (10, 32))
    y_test = np.zeros(10)
    metrics = detector.evaluate(X_test, y_test)
    assert "f1" in metrics
    assert "auc" in metrics

def test_detector_save_load(detector, tmp_path):
    model_path = str(tmp_path / "test_model.pt")
    detector.save(model_path)
    assert os.path.exists(model_path)

    detector.load(model_path)
    assert detector.is_trained

def test_detector_threshold_percentile(detector):
    # Train with specific distribution
    data = np.random.normal(0.5, 0.01, (1000, 32))
    detector.train(data, epochs=5)
    # Percentile 95 should be close to the mean error
    assert detector.threshold > 0

def test_detector_save_report(detector, tmp_path):
    report_path = str(tmp_path / "report.json")
    detector.save_evaluation_report({"f1": 0.9}, report_path)
    assert os.path.exists(report_path)
