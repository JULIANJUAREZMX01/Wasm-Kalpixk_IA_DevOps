#!/usr/bin/env python3
# train_baseline.py - Entrenar modelo Kalpixk con datos benignos
# Ejecutar en droplet AMD MI300X: python3 python/train_baseline.py

import pickle
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from models.ensemble import DetectionEnsemble
from utils.device import get_rocm_device, log_gpu_info

FEATURE_DIM = 32
BASELINE_FILE = Path("models/baseline_model.pkl")
N_SAMPLES = 2000


def generate_normal(n):
    rng = np.random.default_rng(42)
    s = rng.normal(0.3, 0.1, (n, FEATURE_DIM)).clip(0, 1).astype(np.float32)
    # Patrones de normalidad WMS
    s[:, 5] = rng.uniform(0.0, 0.2, n)  # is_off_hours = bajo
    s[:, 8] = rng.uniform(0.8, 1.0, n)  # has_user = casi siempre
    s[:, 16] = rng.uniform(0.0, 0.05, n)  # has_destructive_op = raro
    s[:, 21] = rng.uniform(0.7, 1.0, n)  # process_is_known = alto
    s[:, 25] = rng.uniform(0.0, 0.03, n)  # has_base64_payload = casi nunca
    s[:, 26] = rng.uniform(0.0, 0.05, n)  # has_powershell_sig = casi nunca
    return s


def main():
    print("=" * 50)
    print("  KALPIXK — Entrenamiento Baseline Normal")
    print("=" * 50)
    device = get_rocm_device()
    log_gpu_info(device)

    t0 = time.time()
    print(f"[1/3] Generando {N_SAMPLES} muestras normales...")
    data = generate_normal(N_SAMPLES)

    print(f"[2/3] Entrenando DetectionEnsemble en {device}...")
    ensemble = DetectionEnsemble(device=str(device))
    ensemble.fit(data)

    print("[3/3] Validando con anomalia sintetica (ransomware)...")
    anomaly = np.ones((1, FEATURE_DIM), dtype=np.float32)
    anomaly[0, [9, 16, 25, 26]] = 1.0
    score, detected = ensemble.predict(anomaly)
    assert detected, "ERROR: modelo no detecta anomalia obvia"
    print(f"    Score: {score:.4f} | Detectado: {detected}")

    BASELINE_FILE.parent.mkdir(exist_ok=True)
    with open(BASELINE_FILE, "wb") as f:
        pickle.dump(ensemble, f)

    print(f"Modelo guardado: {BASELINE_FILE}")
    print(f"Tiempo total: {time.time() - t0:.2f}s | Device: {device}")
    print("BASELINE OK")


if __name__ == "__main__":
    main()
