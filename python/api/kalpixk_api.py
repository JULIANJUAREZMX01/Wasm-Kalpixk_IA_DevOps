"""
Kalpixk FastAPI — Backend principal con AMD ROCm
Endpoints:
  POST /analyze     → Analiza un log y retorna anomaly score + explicación LLM
  GET  /status      → Estado del sistema y GPU
  POST /train       → Entrena/re-entrena el modelo
  WS   /stream      → WebSocket para telemetría en tiempo real (MessagePack)
  GET  /features    → Nombres de las 32 features (XAI)
"""

import json
import os
import secrets
import sys
import time

import msgpack
import numpy as np
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
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
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
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

API_KEY_NAME = "X-Kalpixk-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    env = os.getenv("KALPIXK_ENV", os.getenv("ENV", "development"))
    expected_key = os.getenv("KALPIXK_API_KEY")

    if env == "production":
        if not expected_key:
            from loguru import logger
            logger.error("KALPIXK_API_KEY not set in production!")
            raise HTTPException(status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
        if not api_key or not secrets.compare_digest(api_key, expected_key):
            raise HTTPException(status_code=fastapi_status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
    else:
        if expected_key and (not api_key or not secrets.compare_digest(api_key, expected_key)):
             raise HTTPException(status_code=fastapi_status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
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


class LogRequest(BaseModel):
    features: list[float] = Field(..., min_length=32, max_length=32)
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


@app.on_event("startup")
async def startup():
    global _ensemble, _device
    _device = get_rocm_device()
    log_gpu_info(_device)
    _ensemble = DetectionEnsemble(device=str(_device))
    print(f"[Kalpixk] API iniciada en {_device}")


@app.get("/status")
@limiter.limit("10/minute")
async def status(request: Request, api_key: str = Depends(verify_api_key)):
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
@limiter.limit("60/minute")
async def analyze(request: Request, req: LogRequest, api_key: str = Depends(verify_api_key)):
    if _ensemble is None:
        raise HTTPException(503, "Modelo no inicializado")

    if len(req.features) != 32:
        raise HTTPException(422, f"Se esperan 32 features, recibidas: {len(req.features)}")

    t0 = time.time()
    features_array = np.array([req.features], dtype=np.float32)
    score, is_anomaly = _ensemble.predict(features_array)
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
@limiter.limit("5/minute")
async def train(request: Request, payload: TrainPayload, api_key: str = Depends(verify_api_key)):
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
@limiter.limit("10/minute")
async def get_feature_names(request: Request, api_key: str = Depends(verify_api_key)):
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
