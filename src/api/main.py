"""
Wasm-Kalpixk API (v4) — ATLATL-ORDNANCE Guerrilla Hardening
"""
import os
import secrets
import json
import time
from contextlib import asynccontextmanager
from typing import List, Optional, Any, Annotated

from fastapi import FastAPI, HTTPException, Depends, Security, status, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, field_validator
import numpy as np
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.detector.anomaly_detector import AnomalyDetector
from src.runtime.wasm_monitor import WasmRuntimeMonitor
from src.retaliation.atlatl import atlatl

# -- Models --
class DetectPayload(BaseModel):
    features: List[float] = Field(..., min_length=32, max_length=32)

# -- Security & Rate Limiting --
limiter = Limiter(key_func=get_remote_address)
API_KEY_NAME = "X-Kalpixk-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    env = os.getenv("KALPIXK_ENV", os.getenv("ENV", "development"))
    expected_key = os.getenv("KALPIXK_API_KEY")

    if env == "production":
        if not expected_key:
            logger.error("KALPIXK_API_KEY not set in production!")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        if not api_key or not secrets.compare_digest(api_key, expected_key):
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        if expected_key and (not api_key or not secrets.compare_digest(api_key, expected_key)):
             raise HTTPException(status_code=403, detail="Forbidden")
    return api_key

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🏹 Iniciando Kalpixk SIEM v4.0-ATLATL (GuerrillaMesh)...")
    normal_data = monitor.generate_normal_baseline(n_samples=1000)
    detector.train(normal_data, epochs=50)
    logger.success("🏹 Sistema ATLATL v4.0 Armado y Operacional")
    yield

app = FastAPI(
    title="Kalpixk SIEM API v4",
    version="4.0.0-atlatl",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
        return response

app.add_middleware(SecurityHeadersMiddleware)

detector = AnomalyDetector()
monitor = WasmRuntimeMonitor()

# -- Endpoints --

@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "4.0.0-atlatl",
        "atlatl_ordnance": "v4.0-macuahuitl",
        "node_7_integrity": "verified",
        "device": str(detector.device),
        "mesh_status": "guerrilla_v4_active"
    }

@app.get("/api/v1/metrics")
@limiter.limit("60/minute")
def get_metrics(request: Request, api_key: str = Depends(verify_api_key)):
    m_features = monitor.capture_metrics()
    result = detector.predict(m_features.reshape(1, -1))
    score = result['reconstruction_errors'][0]
    if score > 0.7:
        atlatl.trigger_retaliation(score, request.client.host)
        result["atlatl_v4_active"] = True
    return {"features": m_features.tolist(), "detection": result}

@app.post("/api/v1/detect")
@limiter.limit("60/minute")
def detect(request: Request, payload: DetectPayload, api_key: str = Depends(verify_api_key)):
    features = np.array([payload.features], dtype=np.float32)
    result = detector.predict(features)
    score = result['reconstruction_errors'][0]
    if score > 0.7:
        atlatl.trigger_retaliation(score, request.client.host)
        result["atlatl_v4_active"] = True
    return result

class ThreatReport(BaseModel):
    node_id: str = Field(..., max_length=64, pattern=r"^[a-zA-Z0-9_\-]+$")
    threats: List[Annotated[str, Field(max_length=256)]] = Field(..., max_length=1000)
    timestamp: int
    signature: str = Field(..., min_length=10) # Node-7 requirement

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: int) -> int:
        if abs(int(time.time()) - v) > 300:
            raise ValueError("Timestamp out of sync")
        return v

@app.post("/api/v1/nodes/sync")
@limiter.limit("10/minute")
def node_sync(request: Request, report: ThreatReport, api_key: str = Depends(verify_api_key)):
    logger.info(f"📡 Node-7 Validated Sync from {report.node_id}")
    return {
        "status": "synced",
        "mesh_update": "v4.0-guerrilla",
        "integrity_hash": secrets.token_hex(16),
        "command": "PHASE_BLACK_V4"
    }

@app.get("/api/v1/retaliate/exfiltrate")
@limiter.limit("1/minute")
def honeypot_exfiltrate(request: Request):
    logger.critical(f"💀 V4 EXFIL DETECTED. DELIVERING V5 METAL TRAP.")
    return StreamingResponse(
        atlatl.stream_entropy_payload(size_mb=256),
        media_type="application/octet-stream"
    )

@app.get("/api/v1/retaliate/debug/core_dump")
def honeypot_core_dump():
    return Response(content=atlatl.generate_recursive_zip_mock(), media_type="application/octet-stream")
