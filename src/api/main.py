"""
Wasm-Kalpixk API (v2) — DevSecOps Hardening
"""
import os
import secrets
import json
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends, Security, status, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
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
    env = os.getenv("ENV", "development")
    expected_key = os.getenv("KALPIXK_API_KEY")

    if env == "production":
        if not expected_key:
            logger.error("KALPIXK_API_KEY not set in production!")
            raise HTTPException(status_code=500, detail="API Key not configured")
        if not api_key or not secrets.compare_digest(api_key, expected_key):
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        if expected_key and (not api_key or not secrets.compare_digest(api_key, expected_key)):
             raise HTTPException(status_code=403, detail="Forbidden")
    return api_key

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando Kalpixk SIEM...")
    normal_data = monitor.generate_normal_baseline(n_samples=1000)
    detector.train(normal_data, epochs=50)

    dataset_path = "models/dataset_real.npz"
    if os.path.exists(dataset_path):
        data = np.load(dataset_path)
        metrics = detector.evaluate(data['X'], data['y'])
        detector.save_evaluation_report(metrics)

    logger.success("Sistema listo")
    yield

app = FastAPI(
    title="Kalpixk SIEM API v2",
    version="2.0.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

cors_origins_str = os.getenv("CORS_ORIGINS", '["http://localhost:8000", "http://localhost:3000"]')
try:
    cors_origins = json.loads(cors_origins_str)
except:
    cors_origins = ["http://localhost:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=True,
)

detector = AnomalyDetector()
monitor = WasmRuntimeMonitor()

# -- Endpoints --

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_trained": detector.is_trained,
        "device": str(detector.device),
        "wasm_connected": True
    }

@app.get("/api/v1/metrics")
@limiter.limit("60/minute")
def get_metrics(request: Request, api_key: str = Depends(verify_api_key)):
    m_features = monitor.capture_metrics()
    result = detector.predict(m_features.reshape(1, -1))

    # [ATLATL-ORDNANCE] Retaliation Trigger
    score = result['reconstruction_errors'][0]
    if score > 0.7:
        source_ip = request.client.host
        atlatl.trigger_retaliation(score, source_ip)
        result["atlatl_active"] = True

    return {"features": m_features.tolist(), "detection": result}

@app.post("/api/v1/detect")
@limiter.limit("60/minute")
def detect(request: Request, payload: DetectPayload, api_key: str = Depends(verify_api_key)):
    features = np.array([payload.features], dtype=np.float32)
    result = detector.predict(features)

    # [ATLATL-ORDNANCE] Retaliation Trigger
    score = result['reconstruction_errors'][0]
    if score > 0.7:
        source_ip = request.client.host
        atlatl.trigger_retaliation(score, source_ip)
        result["atlatl_active"] = True

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
        "device": str(detector.device),
        "train_stats": detector.train_stats
    }

# [ATLATL-ORDNANCE] Offensive Honeypots
@app.get("/api/v1/retaliate/exfiltrate")
@limiter.limit("1/minute")
def honeypot_exfiltrate(request: Request):
    """
    Honeypot that delivers high entropy garbage via streaming
    to prevent memory exhaustion on the server while slowing down the attacker.
    """
    source_ip = request.client.host
    logger.critical(f"💀 EXFILTRATION ATTEMPT DETECTED FROM {source_ip}. DELIVERING ENTROPY TRAP.")

    return StreamingResponse(
        atlatl.stream_entropy_payload(size_mb=100),
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=core_exfil.bin"}
    )

@app.get("/api/v1/retaliate/debug/core_dump")
@limiter.limit("1/minute")
def honeypot_core_dump(request: Request):
    """
    Honeypot that mimics a memory core dump but delivers poisoned pointers.
    """
    source_ip = request.client.host
    logger.critical(f"💀 CORE DUMP ACCESS ATTEMPT FROM {source_ip}. DELIVERING POISONED BUFFER.")

    payload = atlatl.generate_recursive_zip_mock()
    return Response(content=payload, media_type="application/octet-stream")
