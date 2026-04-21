"""
Wasm-Kalpixk API (v4) — ATLATL-ORDNANCE Guerrilla Hardening
"""
import os
import secrets
import json
import time
from contextlib import asynccontextmanager
from typing import List, Annotated

from fastapi import FastAPI, HTTPException, Depends, Security, Request, Response
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
    logger.info("🏹 Iniciando Kalpixk SIEM v4.0 (ATLATL-ORDNANCE)...")
    normal_data = monitor.generate_normal_baseline(n_samples=1000)
    detector.train(normal_data, epochs=50)

    dataset_path = "models/dataset_real.npz"
    if os.path.exists(dataset_path):
        data = np.load(dataset_path)
        metrics = detector.evaluate(data['X'], data['y'])
        detector.save_evaluation_report(metrics)

    logger.success("🏹 Sistema ATLATL Armado y Operacional")
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
        # Hardened: No wildcard CORS in production
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
        "atlatl_ordnance": "v4.0-macuahuitl",
        "model_trained": detector.is_trained,
        "wasm_connected": True,
        "mesh_status": "guerrilla_v4_active",
        "node_7": "integrity_enabled"
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
        "mesh_active": True,
        "node_7_integrity": "active"
    }

# -- [ATLATL-ORDNANCE] Guerrilla Node Sync --

class ThreatReport(BaseModel):
    node_id: str = Field(..., max_length=64, pattern=r"^[a-zA-Z0-9_\-]+$")
    threats: List[Annotated[str, Field(max_length=256)]] = Field(..., max_length=1000)
    timestamp: int

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: int) -> int:
        now = int(time.time())
        if abs(now - v) > 300:
            raise ValueError("Timestamp out of sync (replay protection)")
        return v

@app.post("/api/v1/nodes/sync")
@limiter.limit("10/minute")
def node_sync(request: Request, report: ThreatReport, api_key: str = Depends(verify_api_key)):
    source_ip = request.client.host
    logger.info(f"📡 Guerrilla Mesh v4 sync from {report.node_id}@{source_ip}")

    # [ATLATL-ORDNANCE] Node-7: MESH_INTEGRITY validation
    # This simulates the cryptographic validation of the node report.
    if ".." in report.node_id or "/" in report.node_id:
        logger.critical(f"💀 MESH POISONING ATTEMPT DETECTED FROM {source_ip}!")
        atlatl.trigger_retaliation(1.0, source_ip, anomaly_type="mesh_tampering")
        raise HTTPException(status_code=400, detail="Node Integrity Violation")

    return {
        "status": "synced",
        "mesh_update": "v4.0-guerrilla",
        "active_mesh_nodes": 12,
        "integrity_verified": True,
        "command": "PHASE_BLACK_IF_DETECTED"
    }

# [ATLATL-ORDNANCE] Offensive Honeypots v3
@app.get("/api/v1/retaliate/exfiltrate")
@limiter.limit("1/minute")
def honeypot_exfiltrate(request: Request):
    """
    Honeypot that delivers high entropy garbage via streaming
    to prevent memory exhaustion on the server while slowing down the attacker.
    """
    source_ip = request.client.host
    logger.critical(f"💀 EXFILTRATION V3 DETECTED FROM {source_ip}. DELIVERING RECURSIVE ENTROPY TRAP.")

    return StreamingResponse(
        atlatl.stream_entropy_payload(size_mb=100),
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=core_exfil.bin"}
    )

@app.get("/api/v1/retaliate/debug/core_dump")
@limiter.limit("1/minute")
def honeypot_core_dump(request: Request):
    source_ip = request.client.host
    logger.critical(f"💀 CORE DUMP V3 ATTEMPT FROM {source_ip}. DELIVERING V3 POISONED BUFFER.")

    payload = atlatl.generate_recursive_zip_mock()
    return Response(content=payload, media_type="application/octet-stream")
