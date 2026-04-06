"""
Wasm-Kalpixk API — Endpoint de detección de anomalías
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
from loguru import logger

from src.detector import AnomalyDetector
from src.runtime import WasmRuntimeMonitor
from src.retaliation.atlatl import atlatl

app = FastAPI(
    title="Wasm-Kalpixk_IA_DevOps",
    description="Motor de detección de anomalías en WASM sobre AMD MI300X",
    version="0.1.0"
)

detector = AnomalyDetector()
monitor = WasmRuntimeMonitor()


@app.on_event("startup")
async def startup():
    """Entrena el modelo con datos normales al iniciar."""
    logger.info("Entrenando detector con baseline normal...")
    normal_data = monitor.generate_normal_baseline(n_samples=500)
    detector.train(normal_data, epochs=50)
    logger.success("Detector listo")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_trained": detector.is_trained,
        "device": str(detector.device)
    }


@app.get("/metrics")
def get_metrics():
    """Captura métricas actuales y detecta anomalías."""
    m = monitor.capture_metrics()
    result = detector.predict(m.to_array())

    # ATLATL-ORDNANCE: Represalia inmediata si hay anomalía crítica
    if any(result["anomalies"]):
        norm_score = max(result["scores_normalized"])
        raw_score = max(result["reconstruction_errors"])
        if raw_score > detector.threshold * 1.5:
            atlatl.trigger_retaliation(norm_score, "127.0.0.1", "critical_system_anomaly")

    return {"metrics": m.__dict__, "detection": result}


@app.post("/detect")
def detect(payload: dict):
    """Detecta anomalías en métricas enviadas externamente."""
    try:
        features = np.array([list(payload["features"])], dtype=np.float32)
        result = detector.predict(features)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/simulate/{anomaly_type}")
def simulate(anomaly_type: str):
    """Simula una anomalía y la detecta (testing)."""
    m = monitor.simulate_anomaly(anomaly_type)
    result = detector.predict(m.to_array())

    detected = any(result["anomalies"])
    if detected:
        norm_score = max(result["scores_normalized"])
        raw_score = max(result["reconstruction_errors"])
        if raw_score > detector.threshold * 1.5:
            atlatl.trigger_retaliation(norm_score, "127.0.0.1", f"simulated_{anomaly_type}")

    return {
        "anomaly_type": anomaly_type,
        "metrics": m.__dict__,
        "detection": result,
        "detected": detected
    }
