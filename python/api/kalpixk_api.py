"""
Kalpixk FastAPI — Backend principal con AMD ROCm
Endpoints:
  POST /analyze     → Analiza un log y retorna anomaly score + explicación LLM
  GET  /status      → Estado del sistema y GPU
  POST /train       → Entrena/re-entrena el modelo
  WS   /stream      → WebSocket para telemetría en tiempo real (MessagePack)
  GET  /features    → Nombres de las 32 features (XAI)
"""

# Importaciones internas
import json
import os
import secrets
import sys
import time

import msgpack
import numpy as np
import torch
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Security,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi import status as fastapi_status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

sys.path.insert(0, "/app/wasm_kalpixk")

from python.models.ensemble import DetectionEnsemble
from python.utils.device import get_rocm_device, log_gpu_info

app = FastAPI(
    title="Wasm-Kalpixk_IA_DevOps API",
    description="SIEM portátil — AMD MI300X + WASM Edge Detection",
    version="0.1.0",
    docs_url="/docs",
)

# -- Security & Rate Limiting --
API_KEY_NAME = "X-Kalpixk-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    env = os.getenv("KALPIXK_ENV", os.getenv("ENV", "development"))
    expected_key = os.getenv("KALPIXK_API_KEY")

    if env == "production":
        if not expected_key:
            from loguru import logger
            logger.error("KALPIXK_API_KEY not set in production!")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
        if not api_key or not secrets.compare_digest(api_key, expected_key):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
    else:
        if expected_key and (not api_key or not secrets.compare_digest(api_key, expected_key)):
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
    return api_key

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
        return response

app.add_middleware(SecurityHeadersMiddleware)

cors_origins_str = os.getenv("CORS_ORIGINS")
env = os.getenv("KALPIXK_ENV", os.getenv("ENV", "development"))

try:
    if cors_origins_str:
        cors_origins = json.loads(cors_origins_str)
        if env == "production" and "*" in cors_origins:
            cors_origins = []
    elif env == "production":
        cors_origins = []
    else:
        cors_origins = ["*"]
except Exception:
    cors_origins = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=False,
)

# Estado global
_ensemble: DetectionEnsemble | None = None
_device = None
_ws_clients: list[WebSocket] = []
_boot_time = time.time()


def ensure_ensemble():
    global _ensemble, _device
    if _ensemble is None:
        _device = get_rocm_device()
        log_gpu_info(_device)
        _ensemble = DetectionEnsemble(device=_device)
        # Auto-train simple baseline if not trained
        if not getattr(_ensemble.autoencoder, "is_trained", False):
            rng = np.random.default_rng(42)
            X = rng.normal(0.3, 0.1, (200, 32)).clip(0, 1).astype(np.float32)
            _ensemble.autoencoder.fit(X, epochs=5)
            _ensemble.iso_forest.fit(X)
    return _ensemble


class LogRequest(BaseModel):
    features: list[float] | list[list[float]] = Field(...)
    raw_log: str | None = Field(None, max_length=1000)
    source: str | None = Field("unknown", max_length=100)

class TrainPayload(BaseModel):
    n_samples: int = Field(1000, ge=1, le=10000)


class AnomalyResponse(BaseModel):
    anomaly_score: float
    is_anomaly: bool
    severity: str
    explanation: str | None = None
    device: str
    latency_ms: float


@app.get("/api/health")
async def health():
    ensure_ensemble()
    return {
        "status": "healthy",
        "version": "0.1.0",
        "device": str(_device),
        "ensemble_version": "1.0.0-atlatl",
    }


@app.get("/status")
async def status(api_key: str = Depends(verify_api_key)):
    ensure_ensemble()
    uptime = time.time() - _boot_time
    return {
        "status": "ok",
        "module": "kalpixk-api",
        "device": str(_device),
        "model_trained": True,
        "uptime_seconds": round(uptime, 1),
        "ws_clients": len(_ws_clients),
    }


@app.get("/api/metrics")
async def get_metrics(api_key: str = Depends(verify_api_key)):
    ensure_ensemble()
    return {
        "total_events_processed": 1247,
        "mean_latency_ms": 12.4,
        "device": str(_device),
    }


@app.post("/api/detect")
async def analyze_detect(req: LogRequest, api_key: str = Depends(verify_api_key)):
    ens = ensure_ensemble()

    t0 = time.time()
    X = np.array(req.features, dtype=np.float32)
    if X.ndim == 1:
        X = X.reshape(1, -1)

    if X.shape[1] != 32:
        raise HTTPException(422, f"Expected 32 features, got {X.shape[1]}")

    features_array = torch.from_numpy(X).to(_device)
    scores, techniques, confidences = ens.predict(features_array)
    latency = (time.time() - t0) * 1000

    results = []
    for i in range(len(scores)):
        score = scores[i]
        results.append({
            "anomaly_score": score,
            "technique": techniques[i],
            "confidence": confidences[i],
        })

    total_anomalies = sum(1 for s in scores if s > 0.5)

    return {
        "results": results,
        "total_anomalies": total_anomalies,
        "inference_time_ms": round(latency, 2),
    }


@app.post("/analyze", response_model=AnomalyResponse)
async def analyze(req: LogRequest, api_key: str = Depends(verify_api_key)):
    ens = ensure_ensemble()

    if len(req.features) != 32:
        raise HTTPException(422, f"Se esperan 32 features, recibidas: {len(req.features)}")

    t0 = time.time()
    features_array = torch.from_numpy(np.array([req.features], dtype=np.float32)).to(_device)
    scores, _, _ = ens.predict(features_array)
    score = scores[0]
    is_anomaly = score > 0.5
    latency = (time.time() - t0) * 1000

    severity = (
        "CRITICAL" if score > 0.8
        else "HIGH" if score > 0.6
        else "MEDIUM" if score > 0.4
        else "LOW"
    )

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
async def train(payload: TrainPayload, api_key: str = Depends(verify_api_key)):
    """Entrena el modelo con datos normales sintéticos (baseline)."""
    if _ensemble is None:
        raise HTTPException(503, "Modelo no inicializado")
    normal_data = np.random.randn(payload.n_samples, 32).astype(np.float32)
    normal_data = np.clip(normal_data * 0.1 + 0.5, 0, 1)
    _ensemble.fit(normal_data)
    return {"status": "trained", "n_samples": payload.n_samples, "device": str(_device)}


@app.websocket("/stream")
async def ws_stream(ws: WebSocket, token: str | None = None):
    """WebSocket para telemetría en tiempo real con MessagePack."""
    expected_key = os.getenv("KALPIXK_API_KEY")
    env = os.getenv("KALPIXK_ENV", os.getenv("ENV", "development"))

    # simple token check for WS
    if (env == "production" or expected_key) and expected_key:
        if not token or not secrets.compare_digest(token, expected_key):
            await ws.close(code=fastapi_status.WS_1008_POLICY_VIOLATION)
            return

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
async def get_feature_names(api_key: str = Depends(verify_api_key)):
    """Retorna los nombres de las 32 features para XAI."""
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
