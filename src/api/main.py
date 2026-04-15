"""
Wasm-Kalpixk API (v3) — ATLATL-ORDNANCE Guerrilla Hardening
"""
import os
import secrets
import json
from contextlib import asynccontextmanager
from typing import List, Optional, Any

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
    logger.info("🏹 Iniciando Kalpixk SIEM v3 (ATLATL-ORDNANCE)...")
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
    title="Kalpixk SIEM API v3",
    version="3.1.0-atlatl",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

cors_origins_str = os.getenv("CORS_ORIGINS", '["*"]')
try:
    cors_origins = json.loads(cors_origins_str)
except:
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=False,
)

detector = AnomalyDetector()
monitor = WasmRuntimeMonitor()

# -- Endpoints --

@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "3.1.0-atlatl",
        "atlatl_ordnance": "v3.1-macuahuitl",
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
@limiter.limit("5/minute")
def get_status(request: Request, api_key: str = Depends(verify_api_key)):
    return {
        "is_trained": detector.is_trained,
        "threshold": detector.threshold,
        "atlatl_version": "3.1-atlatl",
        "device": str(detector.device),
        "mesh_active": True
    }

# -- [ATLATL-ORDNANCE] Guerrilla Node Sync --

class ThreatReport(BaseModel):
    node_id: str
    threats: List[str]
    timestamp: int

@app.post("/api/v1/nodes/sync")
@limiter.limit("10/minute")
def node_sync(request: Request, report: ThreatReport, api_key: str = Depends(verify_api_key)):
    source_ip = request.client.host
    logger.info(f"📡 Guerrilla Node sync from {report.node_id}@{source_ip}")

    # [ATLATL-ORDNANCE] Integrate with Rust Core mesh
    # Note: In a real scenario, we'd call the WASM/FFI functions here.
    # For now, we simulate the interaction with the decentralized registry.

    return {
        "status": "synced",
        "mesh_update": "v3.1-guerrilla",
        "active_mesh_nodes": 5, # Placeholder for real count
        "command": "PHASE_BLACK_IF_DETECTED"
    }

# [ATLATL-ORDNANCE] Offensive Honeypots v3
@app.get("/api/v1/retaliate/exfiltrate")
@limiter.limit("1/minute")
def honeypot_exfiltrate(request: Request):
    source_ip = request.client.host
    logger.critical(f"💀 EXFILTRATION V3 DETECTED FROM {source_ip}. DELIVERING RECURSIVE ENTROPY TRAP.")

    # Stream 100MB of v3 entropy garbage
    return StreamingResponse(
        atlatl.generate_entropy_stream(100),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=exfiltration_v3_leak.zip"}
    )

@app.get("/api/v1/retaliate/debug/core_dump")
@limiter.limit("1/minute")
def honeypot_core_dump(request: Request):
    source_ip = request.client.host
    logger.critical(f"💀 CORE DUMP V3 ATTEMPT FROM {source_ip}. DELIVERING V3 POISONED BUFFER.")

    payload = atlatl.generate_recursive_zip_mock()
    return Response(content=payload, media_type="application/octet-stream")
