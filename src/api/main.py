"""
Wasm-Kalpixk API — Endpoint de detección de anomalías
"""
import os
import secrets
from fastapi import FastAPI, HTTPException, Security, Depends, status
from fastapi.security import APIKeyHeader
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

# ── Security ──────────────────────────────────────────────
API_KEY_NAME = "X-Kalpixk-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verifica la API Key en el header X-Kalpixk-Key."""
    expected_key = os.getenv("KALPIXK_API_KEY")
    if not expected_key:
        # En desarrollo, si no hay key configurada, permitimos con warning
        if os.getenv("ENV") == "production":
            logger.error("KALPIXK_API_KEY no configurada en producción!")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API Key not configured"
            )
        return None

    if not api_key or not secrets.compare_digest(api_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials"
        )
    return api_key


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
def get_metrics(api_key: str = Depends(verify_api_key)):
    """Captura métricas actuales y detecta anomalías."""
    m = monitor.capture_metrics()
    result = detector.predict(m.to_array())

    # ATLATL-ORDNANCE: Represalia inmediata si hay anomalía crítica
    if any(result["anomalies"]):
        score = max(result["reconstruction_errors"])
        if score > detector.threshold * 2:
            atlatl.trigger_retaliation(score, "127.0.0.1", "generic_anomaly")

    return {"metrics": m.__dict__, "detection": result}


@app.post("/detect")
def detect(payload: dict, api_key: str = Depends(verify_api_key)):
    """Detecta anomalías en métricas enviadas externamente."""
    try:
        features = np.array([list(payload["features"])], dtype=np.float32)
        result = detector.predict(features)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/simulate/{anomaly_type}")
def simulate(anomaly_type: str, api_key: str = Depends(verify_api_key)):
    """Simula una anomalía y la detecta (testing)."""
    m = monitor.simulate_anomaly(anomaly_type)
    result = detector.predict(m.to_array())
    return {
        "anomaly_type": anomaly_type,
        "metrics": m.__dict__,
        "detection": result,
        "detected": any(result["anomalies"])
    }
