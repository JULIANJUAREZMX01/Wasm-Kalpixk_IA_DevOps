"""
Wasm-Kalpixk API (v4) — ATLATL-ORDNANCE Guerrilla Hardening
"""
import os
import secrets
import json
import time
import hmac
import hashlib
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

class ThreatReport(BaseModel):
    node_id: str = Field(..., max_length=64, pattern=r"^[a-zA-Z0-9_\-]+$")
    threats: List[Annotated[str, Field(max_length=256)]] = Field(..., max_length=1000)
    timestamp: int
    version: str = "4.0.0-atlatl"

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: int) -> int:
        now = int(time.time())
        if abs(now - v) > 300:
            raise ValueError("Timestamp out of sync (replay protection)")
        return v

# -- Security & Rate Limiting --
limiter = Limiter(key_func=get_remote_address)
API_KEY_NAME = "X-Kalpixk-Key"
API_SIG_NAME = "X-Kalpixk-Signature"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    env = os.getenv("KALPIXK_ENV", os.getenv("ENV", "development"))
    expected_key = os.getenv("KALPIXK_API_KEY", "development_secret")

    if env == "production":
        if expected_key == "development_secret":
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
    logger.info("🏹 Iniciando Kalpixk SIEM v4 (ATLATL-ORDNANCE)...")
    normal_data = monitor.generate_normal_baseline(n_samples=1000)
    detector.train(normal_data, epochs=50)

    dataset_path = "models/dataset_real.npz"
    if os.path.exists(dataset_path):
        data = np.load(dataset_path)
        metrics = detector.evaluate(data['X'], data['y'])
        detector.save_evaluation_report(metrics)

    logger.success("🏹 Sistema ATLATL v4.0.0 Armado y Operacional")
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
            logger.error("Wildcard CORS detected in production! Forcing to empty list.")
            cors_origins = []
    elif env == "production":
        logger.warning("CORS_ORIGINS not set in production. Defaulting to empty list.")
        cors_origins = []
    else:
        cors_origins = ["*"]
except Exception as e:
    logger.error(f"Failed to parse CORS_ORIGINS: {e}. Defaulting to empty list.")
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
        "atlatl_ordnance": "v4.0-atlatl",
        "model_trained": detector.is_trained,
        "wasm_connected": True,
        "mesh_status": "guerrilla_active"
    }

@app.get("/api/v1/metrics")
@limiter.limit("60/minute")
def get_metrics(request: Request, api_key: str = Depends(verify_api_key)):
    m_features = monitor.capture_metrics()
    result = detector.predict(m_features.reshape(1, -1))

    score = result['reconstruction_errors'][0]
    if score > 0.7:
        source_ip = request.client.host
        retaliation = atlatl.trigger_retaliation(score, source_ip)
        result["atlatl_active"] = True
        result["retaliation"] = retaliation

    return {"features": m_features.tolist(), "detection": result}

@app.post("/api/v1/detect")
@limiter.limit("60/minute")
def detect(request: Request, payload: DetectPayload, api_key: str = Depends(verify_api_key)):
    features = np.array([payload.features], dtype=np.float32)
    result = detector.predict(features)

    score = result['reconstruction_errors'][0]
    if score > 0.7:
        source_ip = request.client.host
        retaliation = atlatl.trigger_retaliation(score, source_ip)
        result["atlatl_active"] = True
        result["retaliation"] = retaliation

    return result

@app.get("/api/v1/report")
@limiter.limit("5/minute")
def get_report(request: Request, api_key: str = Depends(verify_api_key)):
    report_path = "models/evaluation_report.json"
    if os.path.exists(report_path):
        with open(report_path, "r") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Report not found")

@app.get("/api/v1/status")
@limiter.limit("10/minute")
def get_status(request: Request, api_key: str = Depends(verify_api_key)):
    return {
        "is_trained": detector.is_trained,
        "threshold": detector.threshold,
        "atlatl_version": "4.0.0-atlatl",
        "device": str(detector.device),
        "mesh_active": True
    }

# -- [ATLATL-ORDNANCE] Node-7 Guerrilla Node Sync --

@app.post("/api/v1/nodes/sync")
@limiter.limit("10/minute")
def node_sync(request: Request, report: ThreatReport, api_key: str = Depends(verify_api_key)):
    source_ip = request.client.host
    signature = request.headers.get(API_SIG_NAME)

    if not signature:
        logger.error(f"❌ Missing Node-7 signature from {source_ip}")
        raise HTTPException(status_code=401, detail="Missing Node-7 Signature")

    # Re-calculate signature for verification
    # Note: GuerrillaOrchestrator uses sort_keys=True
    payload_data = report.model_dump()
    data_to_verify = json.dumps(payload_data, sort_keys=True, separators=(",", ":")).encode()

    expected_sig = hmac.new(api_key.encode(), data_to_verify, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature, expected_sig):
        # Retry without separators if the above fails (depends on json library defaults)
        data_to_verify_alt = json.dumps(payload_data, sort_keys=True).encode()
        expected_sig_alt = hmac.new(api_key.encode(), data_to_verify_alt, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig_alt):
            logger.error(f"💀 Node-7 INTEGRITY FAILURE from {source_ip}")
            raise HTTPException(status_code=401, detail="Node-7 Integrity Compromised")

    logger.success(f"📡 Node-7 VERIFIED: Guerrilla Node sync from {report.node_id}@{source_ip}")

    return {
        "status": "synced",
        "integrity": "verified",
        "mesh_update": "v4.0.0-atlatl",
        "active_mesh_nodes": 7,
        "command": "PHASE_BLACK_IF_DETECTED"
    }

# [ATLATL-ORDNANCE] Offensive Honeypots v4
@app.get("/api/v1/retaliate/exfiltrate")
@limiter.limit("1/minute")
def honeypot_exfiltrate(request: Request):
    source_ip = request.client.host
    logger.critical(f"💀 EXFILTRATION V4 DETECTED FROM {source_ip}. DELIVERING RECURSIVE ENTROPY TRAP.")

    return StreamingResponse(
        atlatl.stream_entropy_payload(size_mb=100),
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=core_exfil_v4.bin"}
    )

@app.get("/api/v1/retaliate/debug/core_dump")
@limiter.limit("1/minute")
def honeypot_core_dump(request: Request):
    source_ip = request.client.host
    logger.critical(f"💀 CORE DUMP V4 ATTEMPT FROM {source_ip}. DELIVERING V4 METAL POISONED BUFFER.")

    payload = atlatl.generate_recursive_zip_mock()
    return Response(content=payload, media_type="application/octet-stream")
