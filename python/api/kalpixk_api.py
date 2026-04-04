"""
Kalpixk FastAPI — Backend principal con AMD ROCm
Endpoints:
  POST /analyze     → Analiza un log y retorna anomaly score + explicación LLM
  GET  /status      → Estado del sistema y GPU
  POST /train       → Entrena/re-entrena el modelo
  WS   /stream      → WebSocket para telemetría en tiempo real (MessagePack)
  GET  /features    → Nombres de las 32 features (XAI)
"""

import asyncio
import time
from typing import Optional, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import msgpack
import numpy as np

# Importaciones internas
import sys
sys.path.insert(0, "/app/wasm_kalpixk")

from python.utils.device import get_device, log_device_info
from python.models.ensemble import DetectionEnsemble

app = FastAPI(
    title="Wasm-Kalpixk_IA_DevOps API",
    description="SIEM portátil — AMD MI300X + WASM Edge Detection",
    version="0.1.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estado global
_ensemble: Optional[DetectionEnsemble] = None
_device = None
_ws_clients: List[WebSocket] = []
_boot_time = time.time()


class LogRequest(BaseModel):
    features: List[float]          # Vector de 32 features del WASM core
    raw_log: Optional[str] = None  # Log original para el LLM explicador
    source: Optional[str] = "unknown"


class AnomalyResponse(BaseModel):
    anomaly_score: float
    is_anomaly: bool
    severity: str
    explanation: Optional[str] = None
    device: str
    latency_ms: float


@app.on_event("startup")
async def startup():
    global _ensemble, _device
    _device = get_device()
    log_device_info()
    _ensemble = DetectionEnsemble(device=str(_device))
    print(f"[Kalpixk] API iniciada en {_device}")


@app.get("/status")
async def status():
    uptime = time.time() - _boot_time
    return {
        "status": "ok",
        "module": "kalpixk-api",
        "device": str(_device),
        "model_trained": _ensemble is not None and getattr(_ensemble, '_trained', False),
        "uptime_seconds": round(uptime, 1),
        "ws_clients": len(_ws_clients),
    }


@app.post("/analyze", response_model=AnomalyResponse)
async def analyze(req: LogRequest):
    if _ensemble is None:
        raise HTTPException(503, "Modelo no inicializado")

    if len(req.features) != 32:
        raise HTTPException(422, f"Se esperan 32 features, recibidas: {len(req.features)}")

    t0 = time.time()
    features_array = np.array([req.features], dtype=np.float32)
    score, is_anomaly = _ensemble.predict(features_array)
    latency = (time.time() - t0) * 1000

    severity = "CRITICAL" if score > 0.8 else "HIGH" if score > 0.6 else "MEDIUM" if score > 0.4 else "LOW"

    # Broadcast a clientes WebSocket conectados
    if _ws_clients and is_anomaly:
        alert = msgpack.packb({
            "type": "anomaly",
            "score": float(score),
            "severity": severity,
            "source": req.source,
        })
        for ws in _ws_clients[:]:
            try:
                await ws.send_bytes(alert)
            except Exception:
                _ws_clients.remove(ws)

    return AnomalyResponse(
        anomaly_score=float(score),
        is_anomaly=bool(is_anomaly),
        severity=severity,
        explanation=f"Score: {score:.4f} — {'ANOMALÍA DETECTADA' if is_anomaly else 'Normal'}",
        device=str(_device),
        latency_ms=round(latency, 2),
    )


@app.post("/train")
async def train(n_samples: int = 1000):
    """Entrena el modelo con datos normales sintéticos (baseline)."""
    if _ensemble is None:
        raise HTTPException(503, "Modelo no inicializado")
    normal_data = np.random.randn(n_samples, 32).astype(np.float32)
    normal_data = np.clip(normal_data * 0.1 + 0.5, 0, 1)
    _ensemble.fit(normal_data)
    return {"status": "trained", "n_samples": n_samples, "device": str(_device)}


@app.websocket("/stream")
async def ws_stream(ws: WebSocket):
    """WebSocket para telemetría en tiempo real con MessagePack."""
    await ws.accept()
    _ws_clients.append(ws)
    try:
        while True:
            data = await ws.receive_bytes()
            payload = msgpack.unpackb(data, raw=False)
            features = payload.get("features", [])
            if len(features) == 32:
                arr = np.array([features], dtype=np.float32)
                score, is_anomaly = _ensemble.predict(arr)
                response = msgpack.packb({
                    "score": float(score),
                    "is_anomaly": bool(is_anomaly),
                    "severity": "HIGH" if score > 0.6 else "LOW",
                })
                await ws.send_bytes(response)
    except WebSocketDisconnect:
        _ws_clients.remove(ws)


@app.get("/features")
async def get_feature_names():
    """Retorna los nombres de las 32 features para XAI."""
    from python.utils.device import get_device
    return {
        "feature_dim": 32,
        "contract_version": "1.0.0",
        "features": [
            "event_type_encoded", "local_severity", "hour_of_day", "day_of_week",
            "is_weekend", "is_off_hours", "source_is_internal", "destination_exists",
            "has_user", "source_entropy", "user_entropy", "metadata_field_count",
            "is_privileged_port", "dst_port_normalized", "bytes_log10_normalized",
            "has_db_keyword", "has_destructive_op", "is_sensitive_table",
            "has_bulk_operation", "has_network_scan_sig", "is_privileged_account",
            "process_is_known", "has_lateral_movement", "source_is_cloud",
            "raw_length_normalized", "has_base64_payload", "has_powershell_sig",
            "windows_event_risk", "db2_operation_risk", "netflow_risk",
            "composite_risk_1", "composite_risk_2",
        ]
    }
